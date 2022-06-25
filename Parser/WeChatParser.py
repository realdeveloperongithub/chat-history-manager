# coding = utf-8
from typing import Tuple, List

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

    def __init__(self, **kwargs):
        """
        WeChat Parser for WeChat Chat History
        :param db_path: path to the decrypted version of EnMicroMsg.db
        :param res_dir: resource folder of wechat, should contain image2, video and voice2 folders
        :param attachment_dir: where to save all the multimedia files
        """
        super(WeChatParser, self).__init__()
        db_path = kwargs['db_path']
        res_dir = kwargs['res_dir']
        attachment_dir = kwargs['attachment_dir']
        self.res_dir = res_dir
        self.attachment_dir = attachment_dir
        self.voice_dir = os.path.join(res_dir, "voice2")
        self.video_dir = os.path.join(res_dir, "video")
        self.img_dir = os.path.join(res_dir, "image2")
        self.db_conn = sqlite3.connect(db_path)
        self.cc = self.db_conn.cursor()

    def convert_time(self, timestring: str) -> datetime:
        timestring = timestring.split(".")[0]
        datetime_object = datetime.strptime(timestring, '%Y-%m-%d %H:%M:%S')
        return datetime_object

    def convert_image(self, content: str) -> str:
        # content = "<msg><img aeskey="null" encryver="null" cdnthumbaeskey="null" cdnthumburl="null" cdnthumblength="10240" cdnthumbheight="0" cdnthumbwidth="0" cdnmidheight="0" cdnmidwidth="0" cdnhdheight="0" cdnhdwidth="0" cdnmidimgurl="null" length="51152" md5="null" /></msg>|img:THUMBNAIL_DIRPATH://th_65e520a2f"
        image_key = "THUMBNAIL_DIRPATH://" + str(content.split("|img:THUMBNAIL_DIRPATH://")[1])
        result = self._get_img_file(image_key)
        # (file attached)
        if result != "":
            parent_dir, filename = os.path.split(result)
            filename = filename + ".jpg"
            copy2(result, os.path.join(self.attachment_dir, filename))
            return filename
        else:
            return "Image message {}".format(image_key)

    def convert_voice(self, content: str) -> str:
        # content = "wxid_uf4:8560:1|img:1022d5d103"
        voice_path = str(content.split("|img:")[1])
        result = self._get_voice_file(voice_path)
        # (file attached)
        if result != "":
            parent_dir, filename = os.path.split(result)
            # patch 0829
            # todo
            # filename = filename.replace(".mp3", "") + ".opus"
            copy2(result, os.path.join(self.attachment_dir, filename))
            return filename
        else:
            return "Voice message {}".format(voice_path)

    def convert_video(self, content: str) -> Tuple[str, str]:
        # content = "WeChat VIDEO|img:2154391783b89489105"
        video_path = content.strip("WeChat VIDEO|img:")
        video_path = video_path.strip("VIDEO FILE|img:")
        result, filetype = self._get_video_file(video_path)
        if result != "":
            parent_dir, filename = os.path.split(result)
            copy2(result, os.path.join(self.attachment_dir, filename))
            return filename, filetype
        else:
            return "Video message {}".format(video_path), "EMPTY"

    def convert_url_or_file(self, content: str) -> Tuple[str, int]:
        # content = "URL:http://www.google.com&type=comment|img:THUMBNAIL_DIRPATH://th_b164d5766"
        # content = "FILE:questionnaire.docx"
        if content.startswith("FILE:"):
            filename = content.strip("FILE:")
            if os.path.isfile(os.path.join(self.res_dir, filename)):
                copy2(os.path.join(self.res_dir, filename), os.path.join(self.attachment_dir, filename))
            return filename, 5
        else:
            content = content.strip("URL:")
            if content.find("|img:THUMBNAIL_DIRPATH:") != -1:
                content = content.split("|img:THUMBNAIL_DIRPATH:")[0]
            return content, 1

    def convert_youtube_url(self, content: str) -> str:
        # content = "https://youtu.be/rc null"
        content = content.strip(" null")
        return content

    def convert_live_location(self, content: str) -> str:
        return "live location shared"

    def convert_quote(self, content: str) -> str:
        dom = minidom.parseString(content)
        reply_text = dom.getElementsByTagName("title")[0].firstChild.data
        quoted_text = dom.getElementsByTagName("content")[1].firstChild.data
        return f"{quoted_text}\n================\n{reply_text}"

    def convert_location(self, content: str) -> str:
        # content = LOCATION:New York (45.189418,141.438920)
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
        pay_memo = dom.getElementsByTagName("pay_memo")[0].firstChild.data
        return f"WeChat Transfer:\nAmount: {fee_desc}\nNote: {pay_memo}"

    def convert_namecard(self, content: str) -> str:
        # content = NAMECARD: <msg username="gh_e4" nickname="Test" alias="test" fullpy="test" shortpy="test" imagestatus="3" scene="17" province="Guangdong" city="Guangzhou" sign="test" percard="0" sex="0" certflag="24" certinfo="test" certinfoext="" brandIconUrl="http://mmsns.qpic.cn/0" brandHomeUrl="" brandSubscriptConfigUrl="" brandFlags="" regionCode="CN_Guangdong_Guangzhou"/>
        content = content.strip("NAMECARD: ")
        dom = minidom.parseString(content)
        nickname = dom.getElementsByTagName("msg")[0].getAttribute("nickname")
        return f"Namecard: {nickname}"

    def sql_query_img(self, key: str, cc: sqlite3.Cursor) -> str:
        query = cc.execute(
            """ SELECT bigImgPath FROM ImgInfo2 WHERE thumbImgPath = '{}'""".format(key))
        bigImg = ""
        for row in query:
            bigImg = row[0]
        if bigImg.startswith("SERVERID://"):
            bigImg = ""
        return bigImg

    def _get_voice_file(self, imgpath: str) -> str:
        fname = hashlib.md5(imgpath.encode("ascii")).hexdigest()
        dir1, dir2 = fname[:2], fname[2:4]
        ret = os.path.join(self.voice_dir, dir1, dir2,
                           'msg_{}.opus'.format(imgpath))
        if not os.path.isfile(ret):
            logger.error(f"Cannot find voice file for {imgpath}, with filename {fname}")
            return ""
        return ret

    def _get_img_file(self, fname: str) -> str:
        bigImg = self.sql_query_img(fname, self.cc)
        if bigImg:
            # logger.info("Big image in database for {}".format(fname))
            dir1, dir2 = bigImg[:2], bigImg[2:4]
            dirname = os.path.join(self.img_dir, dir1, dir2)
            if not os.path.isdir(dirname):
                logger.warning("Directory not found: {}".format(dirname))
            else:
                full_name = os.path.join(dirname, bigImg)
                if os.path.isfile(full_name):
                    size = os.path.getsize(full_name)
                    if size > 0:
                        return full_name
        # logger.info("Big image in database for {}".format(fname))
        # fname = fname.replace("THUMBNAIL_DIRPATH://th_", "")
        # dir1, dir2 = fname[:2], fname[2:4]
        fname = fname.replace("THUMBNAIL_DIRPATH://", "")
        dir1, dir2 = fname[3:5], fname[5:7]
        dirname = os.path.join(self.img_dir, dir1, dir2)
        if not os.path.isdir(dirname):
            logger.warning("Directory not found: {}".format(dirname))
            return ""
        else:
            full_name = os.path.join(dirname, fname)
            if os.path.isfile(full_name):
                size = os.path.getsize(full_name)
                if size > 0:
                    return full_name
                else:
                    logger.warning("Image file not valid: {}".format(full_name))
                    return ""
            else:
                logger.warning("Image file not found: {}".format(full_name))
                return ""

    def _get_video_file(self, videoid):
        video_file = os.path.join(self.video_dir, videoid + ".mp4")
        video_thumbnail_file = os.path.join(self.video_dir, videoid + ".jpg")
        if os.path.exists(video_file):
            return video_file, "VIDEO"
        elif os.path.exists(video_thumbnail_file):
            return video_thumbnail_file, "THUMB"
        logger.warning(f"Cannot find video {videoid}")
        return "", ""

    def convert_msg(self, msg_str):
        msg = Message()
        wechat_msg_type = int(msg_str.split("|")[0])
        sender = msg_str.split("|")[1].split(":")[0]
        msg.sender = sender
        time = ":".join(msg_str.split("|")[1].split(":")[1:4])
        time = self.convert_time(time)
        msg.time = time
        content = (":".join("|".join(msg_str.split("|")[1:]).split(":")[4:])).strip("\n")

        if wechat_msg_type == 1:
            # text
            msg.msg_type = 1
        elif wechat_msg_type == 822083633:
            # quoted text
            msg.msg_type = 1
            content = self.convert_quote(content)
        elif wechat_msg_type == 34:
            # audio
            msg.msg_type = 4
            content = self.convert_voice(content)
        elif wechat_msg_type == 3:
            # image
            msg.msg_type = 3
            content = self.convert_image(content)
        elif wechat_msg_type == 62 or wechat_msg_type == 43:
            # video
            content, filetype = self.convert_video(content)
            if filetype == "THUMB":
                msg.msg_type = 3
            else:
                msg.msg_type = 2
        elif wechat_msg_type == 49:
            # url or file
            content, msg.msg_type = self.convert_url_or_file(content)
        elif wechat_msg_type == 16777265:
            # url
            msg.msg_type = 1
            content = self.convert_youtube_url(content)
        elif wechat_msg_type == -1879048186:
            # share live location
            msg.msg_type = 6
            content = self.convert_live_location(content)
        elif wechat_msg_type == 47:
            # sticker
            msg.msg_type = 1
            content = self.convert_sticker(content)
        elif wechat_msg_type == 48:
            # share location
            msg.msg_type = 6
            content = self.convert_location(content)
        elif wechat_msg_type == 1048625:
            # cloud video
            msg.msg_type = 6
            content = self.convert_cloud_video(content)
        elif wechat_msg_type == 50:
            # video chat
            msg.msg_type = 6
            content = self.convert_video_chat(content)
        elif wechat_msg_type == 419430449:
            # wechat transfer
            msg.msg_type = 6
            content = self.convert_wechat_transfer(content)
        elif wechat_msg_type == 42:
            # namecard
            msg.msg_type = 6
            content = self.convert_namecard(content)
        else:
            # unknown msg type
            msg.msg_type = -1
            logging.warning("unknown wechat message type:" + str(wechat_msg_type))
        msg.content = content
        if msg.msg_type != 1 and (msg.content.startswith("Video message")
                                  or msg.content.startswith("Image message")
                                  or msg.content.startswith("Voice message")):
            msg.msg_type = 1
        # return f"{time} - {sender}: {content}"
        return msg

    def parse_txt(self, txt_path: str) -> List[str]:
        with open(txt_path, "r", encoding="utf-8") as f:
            all_data = f.readlines()
            # print(all_data)
            line_idx = []
            split_data = []
            for i, line in enumerate(all_data):
                if line.startswith("1|") or \
                        line.startswith("3|") or \
                        line.startswith("49|") or \
                        line.startswith("62|") or \
                        line.startswith("34|") or \
                        line.startswith("49|") or \
                        line.startswith("16777265|") or \
                        line.startswith("1048625|") or \
                        line.startswith("-1879048186|") or \
                        line.startswith("419430449|") or \
                        line.startswith("50|") or \
                        line.startswith("822083633|") or \
                        line.startswith("42|") or \
                        line.startswith("47|") or \
                        line.startswith("48|") or \
                        line.startswith("43|"):
                    line_idx.append(i)
                    # if line.startswith("1|" or "3|"):
                #     line_idx.append(i)
            line_idx.append(len(all_data))
            for i in range(len(line_idx) - 1):
                temp = ""
                for sub_line in all_data[line_idx[i]:line_idx[i + 1]]:
                    temp = temp + sub_line.strip() + "\n"
                split_data.append(temp)
        return split_data

    def msg_list_generator(self, **kwargs):
        chat_log_file_path = kwargs["chat_log_file_path"]
        msg_list = []
        split_data_list = self.parse_txt(chat_log_file_path)
        for line in split_data_list:
            msg_list.append(self.convert_msg(line))
        try:
            self.cc.close()
        except:
            pass
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
