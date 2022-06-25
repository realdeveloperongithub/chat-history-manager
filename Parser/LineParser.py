# coding = utf-8
import os
import sqlite3
from typing import List, Tuple
import logging
from Message import Message
from shutil import copy2
import re
from datetime import datetime

logger = logging.getLogger(__name__)


def convert_time(timestamp: str) -> datetime:
    timestamp = int(timestamp) / 1000
    return datetime.fromtimestamp(timestamp)


class LineParser(object):
    """
    Attributes: time, type, sender, content
    time: datetime attribute
    msg_type: TEXT (1), VIDEO (2), IMAGE (3), VOICE (4), FILE(5), SYSTEM (6)
    for VIDEO, IMAGE and VOICE type, the content should only be the filename
    """

    def __init__(self, **kwargs):
        """
        Line Parser for Line Chat History
        :param db_path: path to naver_line
        :param res_dir: resource folder of line
        :param attachment_dir: where to save all the multimedia files
        """
        super(LineParser, self).__init__()
        self.res_dir = kwargs['res_dir']
        self.attachment_dir = kwargs['attachment_dir']
        self.db_conn = sqlite3.connect(kwargs['db_path'])
        self.cc = self.db_conn.cursor()
        self.name = ""
        self.mid = ""

    # [Voice message]
    # [Photo]
    # [Sticker]
    # [Video]
    def _get_mid(self, name: str) -> str:
        query = self.cc.execute(
            """SELECT m_id FROM contacts WHERE name = '{}'""".format(name))
        mid = ""
        for row in query:
            mid = row[0]
        return mid

    def _get_chat_history(self, mid: str):
        query = self.cc.execute(
            """SELECT id, from_mid, type, attachement_type, parameter, content, created_time, location_name, 
            location_address, location_latitude, location_longitude FROM chat_history WHERE chat_id = '{}'  
            ORDER BY created_time ASC """.format(mid))
        return query

    def _get_video_file(self, id: str) -> str:
        video_file = os.path.join(self.res_dir, id)
        video_thumbnail_file = os.path.join(self.res_dir, id + ".thumb")
        if os.path.exists(video_file):
            return video_file
        elif os.path.exists(video_thumbnail_file):
            return video_thumbnail_file
        logger.warning(f"Cannot find video for id {id}")
        return ""

    def _get_img_file(self, id: str) -> str:
        image_file = os.path.join(self.res_dir, id)
        image_thumbnail_file = os.path.join(self.res_dir, id + ".thumb")
        if os.path.exists(image_file):
            return image_file
        elif os.path.exists(image_thumbnail_file):
            return image_thumbnail_file
        logger.warning(f"Cannot find image for id {id}")
        return ""

    def _get_voice_file(self, id: str) -> str:
        voice_file = os.path.join(self.res_dir, "voice_{}.aac".format(id))
        if os.path.exists(voice_file):
            return voice_file
        logger.warning(f"Cannot find voice message file for id {id}")
        return ""

    def _get_file(self, id: str, parameter: str) -> Tuple[str, str]:
        # FILE_EXPIRE_TIMESTAMP	155947574	OBS_POP	b	SRC_SVC_CODE	talk	FILE_SIZE	18240	FILE_NAME	まどさん　問題（2）.docx	message_relation_server_message_id		message_relation_service_code		message_relation_type_code
        # filename = parameter.split("	FILE_NAME	")[1].split("	message_relation_server_message_id		")[0].strip()
        filename = re.findall(r"\tFILE_NAME\t(.*?)\t", parameter)[0].strip()
        file = os.path.join(self.res_dir, id)
        if os.path.exists(file):
            return file, filename
        logger.warning(f"Cannot find file for id {id}")
        return "", ""

    def convert_unsent_msg(self, sender: str) -> str:
        return "{} unsent a message".format(sender)

    def convert_voice_call(self, content: str) -> str:
        # Call History : 3210000 millisecs, Result: 16
        return content

    def convert_name_card(self, parameter: str) -> str:
        # mid	u8970bfe720c3b9cb243308bae8bce63f	displayName	りんな	message_relation_server_message_id		message_relation_service_code		message_relation_type_code
        mid = re.findall(r"mid\t(.*?)\tdisplayName\t(.*?)\t", parameter)[0][0].strip()
        display_name = re.findall(r"mid\t(.*?)\tdisplayName\t(.*?)\t", parameter)[0][1].strip()
        # display_name = re.findall(r"\tdisplayName\t(.*?)\t", parameter)[0].strip()
        # mid = parameter.split("mid	")[1].split("	displayName	")[0].strip()
        # display_name = parameter.split("	displayName	")[1].split("	message_relation_server_message_id		")[0].strip()
        return f"Namecard:\nmid: {mid}\ndisplay_name:{display_name}"

    def convert_image(self, id: int) -> str:
        id = str(id)
        result = self._get_img_file(id)
        if result != "":
            parent_dir, filename = os.path.split(result)
            filename = filename + ".jpg"
            copy2(result, os.path.join(self.attachment_dir, filename))
            return filename
        else:
            return "Image message {}".format(id)

    def convert_sticker(self, content: str) -> str:
        return "[Sticker]"

    def convert_event(self, content: str) -> str:
        return content

    def convert_file(self, id: int, parameter: str) -> str:
        id = str(id)
        file, original_filename = self._get_file(id, parameter)
        if file != "":
            copy2(file, os.path.join(self.attachment_dir, original_filename))
            return original_filename
        else:
            return "File message {}".format(id)

    def convert_video(self, id: int) -> str:
        id = str(id)
        result = self._get_video_file(id)
        if result.endswith(".thumb"):
            parent_dir, filename = os.path.split(result)
            filename = filename + ".jpg"
            copy2(result, os.path.join(self.attachment_dir, filename))
            return filename
        elif result != "":
            parent_dir, filename = os.path.split(result)
            filename = filename + ".mp4"
            copy2(result, os.path.join(self.attachment_dir, filename))
            return filename
        else:
            return "Video message {}".format(id)

    def convert_voice_message(self, id: int) -> str:
        id = str(id)
        result = self._get_voice_file(id)
        if result != "":
            parent_dir, filename = os.path.split(result)
            copy2(result, os.path.join(self.attachment_dir, filename))
            return filename
        else:
            return "Voice message {}".format(id)

    def convert_undecryped_message(self, content) -> str:
        return "🔒 This message can't be decrypted\nThis message wasn't backed up and restored from your previous " \
               "device. Unfortunately, there's no way to read it on your current device. "

    def convert_location(self, latitude, longitude) -> str:
        return "location: https://maps.google.com/?q={},{}".format(latitude, longitude)

    def convert_in_app_game_message(self, content: str) -> str:
        return "In-app game message"

    def convert_to_msg(self) -> List[Message]:
        # 0 id
        # 1 from_mid
        # 2 type
        # 3 attachement_type
        # 4 parameter
        # 5 content
        # 6 created_time
        # 7 location_name
        # 8 location_address
        # 9 location_latitude
        # 10 location_longitude
        logger.info("Converting to message object list")
        query = self._get_chat_history(self.mid)
        msg_list = []
        for row in query:
            msg = Message()
            msg.time = convert_time(row[6])
            if row[1] is None:
                msg.sender = "me"
            else:
                msg.sender = self.name
            if row[2] == 5:
                msg.msg_type = 1
                msg.content = self.convert_sticker(row[4])
            elif row[2] == 27:
                msg.msg_type = 6
                msg.content = self.convert_unsent_msg(msg.sender)
            elif row[2] == 4:
                msg.msg_type = 6
                msg.content = self.convert_voice_call(msg.content)
            elif row[2] == 17:
                msg.msg_type = 6
                msg.content = self.convert_undecryped_message(msg.content)
            elif row[2] == 1:
                if row[3] == 0:
                    # text
                    msg.msg_type = 1
                    msg.content = row[5]
                elif row[3] == 1:
                    # image
                    msg.msg_type = 3
                    msg.content = self.convert_image(row[0])
                elif row[3] == 2:
                    # video
                    msg.msg_type = 2
                    msg.content = self.convert_video(row[0])
                elif row[3] == 3:
                    # voice message
                    msg.msg_type = 4
                    msg.content = self.convert_voice_message(row[0])
                elif row[3] == 4:
                    # in-app game
                    msg.msg_type = 6
                    msg.content = self.convert_in_app_game_message(row[4])
                elif row[3] == 12:
                    # event
                    msg.msg_type = 6
                    msg.content = self.convert_event(row[5])
                elif row[3] == 13:
                    # namecard
                    msg.msg_type = 6
                    msg.content = self.convert_name_card(row[4])
                elif row[3] == 14:
                    # file
                    msg.msg_type = 5
                    msg.content = self.convert_file(row[0], row[4])
                elif row[3] == 15:
                    # location
                    msg.msg_type = 6
                    msg.content = self.convert_location(row[9], row[10])
            if msg.msg_type != 1 and (msg.content.startswith("Video message ")
                                          or msg.content.startswith("Image message ")
                                          or msg.content.startswith("File message ")
                                          or msg.content.startswith("Voice message ")):
                msg.msg_type = 1
            if msg.msg_type == 2 and msg.content.endswith(".jpg"):
                msg.msg_type = 3
            msg_list.append(msg)
        return msg_list

    def analyser(self, chat_log_file_path: str) -> List[Message]:
        parent_dir, filename = os.path.split(chat_log_file_path)
        logger.info("Analysing database and chat history")
        self.name = re.findall(r"Chat history with (.*?).txt", filename)[0]
        self.mid = self._get_mid(self.name)
        if self.mid == "":
            logger.warning(f"Cannot find mid with name {self.name}")
        self.res_dir = os.path.join(self.res_dir, self.mid, "messages")
        msg_list = self.convert_to_msg()
        return msg_list

    def msg_list_generator(self, **kwargs) -> List[Message]:
        chat_log_file_path = kwargs['chat_log_file_path']
        msg_list = self.analyser(chat_log_file_path)
        try:
            self.cc.close()
        except:
            pass
        return msg_list


if __name__ == '__main__':
    db_path = r"/Users/xxx/Downloads/line/naver_line"
    res_dir = r"/Users/xxx/Downloads/line/chats"
    attachment_dir = r"/Users/xxx/Downloads/line/attachment"
    chat_log_file_path = r"/Users/xxx/Downloads/line/Chat history with yyy.txt"
    lp = LineParser(db_path=db_path, res_dir=res_dir, attachment_dir=attachment_dir)
    msg_list = lp.msg_list_generator(chat_log_file_path=chat_log_file_path)
    for msg in msg_list:
        print(str(msg) + "\n")
