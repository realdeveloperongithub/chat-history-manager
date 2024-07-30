# coding = utf-8
from typing import Tuple, List, Dict, Any
from Message import Message
import os
from datetime import datetime
import logging
import sqlite3
import hashlib
from shutil import copy2
from xml.dom import minidom

logger = logging.getLogger(__name__)


class WeChatParser(object):
    """
    Attributes: time, type, sender, content
    time: datetime attribute
    msg_type: TEXT (1), VIDEO (2), IMAGE (3), VOICE (4), FILE(5), SYSTEM (6)
    for VIDEO, IMAGE and VOICE type, the content should only be the filename
    """

    def __init__(self, db_path: str, res_dir: str, attachment_dir: str):
        """
        WeChat Parser for WeChat Chat History
        :param db_path: path to the decrypted version of EnMicroMsg.db
        :param res_dir: resource folder of wechat, should contain image2, video and voice2 folders
        :param attachment_dir: where to save all the multimedia files
        """
        super(WeChatParser, self).__init__()
        self.res_dir = res_dir
        self.attachment_dir = attachment_dir
        self.voice_dir = os.path.join(res_dir, "voice2")
        self.video_dir = os.path.join(res_dir, "video")
        self.img_dir = os.path.join(res_dir, "image2")
        self.db_conn = sqlite3.connect(db_path)
        self.cc = self.db_conn.cursor()

    def convert_time(self, timestring: str) -> datetime:
        timestring = timestring.split(".")[0]
        return datetime.strptime(timestring, '%Y-%m-%d %H:%M:%S')

    def convert_image(self, content: str) -> str:
        image_key = "THUMBNAIL_DIRPATH://" + str(content.split("|img:THUMBNAIL_DIRPATH://")[1])
        result = self._get_img_file(image_key)
        if result:
            parent_dir, filename = os.path.split(result)
            filename = filename + ".jpg"
            copy2(result, os.path.join(self.attachment_dir, filename))
            return filename
        else:
            return f"Image message {image_key}"

    def convert_voice(self, content: str) -> str:
        voice_path = str(content.split("|img:")[1])
        result = self._get_voice_file(voice_path)
        if result:
            parent_dir, filename = os.path.split(result)
            copy2(result, os.path.join(self.attachment_dir, filename))
            return filename
        else:
            return f"Voice message {voice_path}"

    def convert_video(self, content: str) -> Tuple[str, str]:
        video_path = content.strip("WeChat VIDEO|img:")
        video_path = video_path.strip("VIDEO FILE|img:")
        result, filetype = self._get_video_file(video_path)
        if result:
            parent_dir, filename = os.path.split(result)
            copy2(result, os.path.join(self.attachment_dir, filename))
            return filename, filetype
        else:
            return f"Video message {video_path}", "EMPTY"

    def convert_url_or_file(self, content: str) -> Tuple[str, int]:
        if content.startswith("FILE:"):
            filename = content.strip("FILE:")
            if os.path.isfile(os.path.join(self.res_dir, filename)):
                copy2(os.path.join(self.res_dir, filename), os.path.join(self.attachment_dir, filename))
            return filename, 5
        else:
            content = content.strip("URL:")
            if "|img:THUMBNAIL_DIRPATH:" in content:
                content = content.split("|img:THUMBNAIL_DIRPATH:")[0]
            return content, 1

    def convert_youtube_url(self, content: str) -> str:
        return content.strip(" null")

    def convert_live_location(self, content: str) -> str:
        return "live location shared"

    def convert_quote(self, content: str) -> str:
        dom = minidom.parseString(content)
        reply_text = dom.getElementsByTagName("title")[0].firstChild.data
        quoted_text = dom.getElementsByTagName("content")[1].firstChild.data
        return f"{quoted_text}\n================\n{reply_text}"

    def convert_location(self, content: str) -> str:
        return content

    def convert_video_chat(self, content: str) -> str:
        return "REQUEST VIDEO CHAT"

    def convert_sticker(self, content: str) -> str:
        return "Sticker"

    def convert_cloud_video(self, content: str) -> str:
        return "Video message"

    def convert_wechat_transfer(self, content: str) -> str:
        dom = minidom.parseString(content)
        fee_desc = dom.getElementsByTagName("feedesc")[0].firstChild.data
        try:
            pay_memo = dom.getElementsByTagName("pay_memo")[0].firstChild.data
        except IndexError:
            pay_memo = ""
        return f"WeChat Transfer:\nAmount: {fee_desc}\nNote: {pay_memo}"

    def convert_namecard(self, content: str) -> str:
        content = content.strip("NAMECARD: ")
        dom = minidom.parseString(content)
        nickname = dom.getElementsByTagName("msg")[0].getAttribute("nickname")
        return f"Namecard: {nickname}"

    def sql_query_img(self, key: str) -> str:
        query = self.cc.execute("SELECT bigImgPath FROM ImgInfo2 WHERE thumbImgPath = ?", (key,))
        bigImg = query.fetchone()
        if bigImg and bigImg[0].startswith("SERVERID://"):
            return ""
        return bigImg[0] if bigImg else ""

    def _get_voice_file(self, imgpath: str) -> str:
        fname = hashlib.md5(imgpath.encode("ascii")).hexdigest()
        dir1, dir2 = fname[:2], fname[2:4]
        ret = os.path.join(self.voice_dir, dir1, dir2, 'msg_{}.opus'.format(imgpath))
        if not os.path.isfile(ret):
            logger.error(f"Cannot find voice file for {imgpath}, with filename {fname}")
            return ""
        return ret

    def _get_img_file(self, fname: str) -> str:
        bigImg = self.sql_query_img(fname)
        if bigImg:
            dir1, dir2 = bigImg[:2], bigImg[2:4]
            dirname = os.path.join(self.img_dir, dir1, dir2)
            if os.path.isdir(dirname):
                full_name = os.path.join(dirname, bigImg)
                if os.path.isfile(full_name) and os.path.getsize(full_name) > 0:
                    return full_name
        fname = fname.replace("THUMBNAIL_DIRPATH://", "")
        dir1, dir2 = fname[3:5], fname[5:7]
        dirname = os.path.join(self.img_dir, dir1, dir2)
        full_name = os.path.join(dirname, fname)
        if os.path.isfile(full_name) and os.path.getsize(full_name) > 0:
            return full_name
        logger.warning(f"Image file not found or not valid: {full_name}")
        return ""

    def _get_video_file(self, videoid: str) -> Tuple[str, str]:
        video_file = os.path.join(self.video_dir, videoid + ".mp4")
        video_thumbnail_file = os.path.join(self.video_dir, videoid + ".jpg")
        if os.path.exists(video_file):
            return video_file, "VIDEO"
        elif os.path.exists(video_thumbnail_file):
            return video_thumbnail_file, "THUMB"
        logger.warning(f"Cannot find video {videoid}")
        return "", ""

    def convert_msg(self, msg_str: str) -> Message:
        msg = Message()
        msg_type, sender_info, *content_parts = msg_str.split("|")
        sender = sender_info.split(":")[0]
        msg.sender = sender
        time_str = ":".join(sender_info.split(":")[1:4])
        msg.time = self.convert_time(time_str)
        content = ":".join(content_parts).strip("\n")

        msg_type = int(msg_type)
        conversion_map = {
            1: (self.convert_text, 1),
            822083633: (self.convert_quote, 1),
            34: (self.convert_voice, 4),
            3: (self.convert_image, 3),
            62: (self.convert_video, 2),
            43: (self.convert_video, 2),
            49: (self.convert_url_or_file, None),
            16777265: (self.convert_youtube_url, 1),
            -1879048186: (self.convert_live_location, 6),
            47: (self.convert_sticker, 1),
            48: (self.convert_location, 6),
            1048625: (self.convert_cloud_video, 6),
            50: (self.convert_video_chat, 6),
            419430449: (self.convert_wechat_transfer, 6),
            42: (self.convert_namecard, 6)
        }

        try:
            converter, default_type = conversion_map.get(msg_type, (self.convert_unknown, -1))
            converted_content = converter(content)
            msg.msg_type = default_type if default_type is not None else converted_content[1]
            msg.content = converted_content[0] if isinstance(converted_content, tuple) else converted_content
        except Exception as e:
            logger.warning(f"Error converting message: {repr(e)}")
            msg.msg_type = -1
            msg.content = content

        if msg.msg_type != 1 and (msg.content.startswith("Video message")
                                  or msg.content.startswith("Image message")
                                  or msg.content.startswith("Voice message")):
            msg.msg_type = 1

        return msg

    def convert_text(self, content: str) -> str:
        return content

    def convert_unknown(self, content: str) -> Tuple[str, int]:
        logger.warning(f"Unknown WeChat message type")
        return content, -1

    def parse_txt(self, txt_path: str) -> List[str]:
        with open(txt_path, "r", encoding="utf-8") as f:
            all_data = f.readlines()
        line_idx = [i for i, line in enumerate(all_data) if line.split("|")[0].isdigit()]
        line_idx.append(len(all_data))
        split_data = ["".join(all_data[line_idx[i]:line_idx[i + 1]]).strip() for i in range(len(line_idx) - 1)]
        return split_data

    def msg_list_generator(self, chat_log_file_path: str) -> List[Message]:
        msg_list: List[Message] = []
        split_data_list = self.parse_txt(chat_log_file_path)
        for line in split_data_list:
            msg_list.append(self.convert_msg(line))
        try:
            self.cc.close()
        except Exception as e:
            logger.error(f"Error closing database cursor: {repr(e)}")
        return msg_list


if __name__ == '__main__':
    attachment_dir = r"/Users/xxx/Downloads/yyy/MediaStorage"
    chat_log_file_path = r"/Users/xxx/Downloads/yyy/WeChat Old/yyy.txt"
    res_dir = r"/Users/xxx/Downloads/yyy/WeChat Old/resource"
    db_path = r"/Users/xxx/Downloads/yyy/WeChat Old/decrypted.db"

    wp = WeChatParser(db_path=db_path, res_dir=res_dir, attachment_dir=attachment_dir)
    full_msg_list = wp.msg_list_generator(chat_log_file_path=chat_log_file_path)
    for msg in full_msg_list:
        print(str(msg) + "\n")
