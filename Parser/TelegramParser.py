# coding = utf-8
import logging
from datetime import datetime, timezone, timedelta
from os import listdir
from os.path import isfile, join, split
from shutil import copy2
from typing import List
import json

from Message import Message

logger = logging.getLogger(__name__)


class TelegramParser(object):
    """
    Attributes: time, type, sender, content
    time: datetime attribute
    msg_type: TEXT (1), VIDEO (2), IMAGE (3), VOICE (4), FILE(5), SYSTEM (6)
    for VIDEO, IMAGE and VOICE type, the content should only be the filename
    """

    def __init__(self, **kwargs):
        """
        Telegram Parser for Telegram Chat History
        :param attachment_dir: where to save all the multimedia files
        """
        super(TelegramParser, self).__init__()
        attachment_dir = kwargs['attachment_dir']
        #res_dir = kwargs['res_dir']
        #timezone = int(kwargs['timezone'])
        self.attachment_dir = attachment_dir
        #self.res_dir = res_dir
        #self.timezone = timezone

    def timestamp_to_local_datetime(self, timestamp: int, tz_offset: float) -> datetime:
        utc_time = datetime.utcfromtimestamp(timestamp)
        offset = timedelta(hours=tz_offset)
        tz = timezone(offset)
        local_time = utc_time.replace(tzinfo=timezone.utc).astimezone(tz)
        return local_time

    def ogg_to_opus(self, content: str) -> str:
        return content.replace(".ogg", ".opus")

    def msg_list_generator(self, **kwargs) -> List[Message]:
        # msg_obj = Message()
        jsonfile = kwargs['chat_log_file_path']
        res_dir = kwargs['res_dir']
        timezone = kwargs['timezone']
        msg_obj_list = []
        with open(jsonfile, encoding="utf8") as json_messages:
            # with open(jsonfile) as json_messages:
            messages = json.load(json_messages)['messages']
        for msg in messages:
            msg_obj = Message()
            msg_obj.time = self.timestamp_to_local_datetime(int(msg['date_unixtime']), timezone)
            if msg['type'] == "service":
                msg_obj.msg_type = 6
                msg_obj.sender = msg['actor']
                msg_obj.content = f"{msg['actor']}: {msg['action']}"
            elif msg['type'] == "message":
                msg_obj.sender = msg['from']
                if "file" in msg:
                    if "photo" in msg:
                        # image
                        msg_obj.msg_type = 3
                        msg_obj = self.media_processor(msg_obj, msg['photo'], res_dir)
                    elif ("media_type" in msg and msg["media_type"] == "video_file") or ("mime_type" in msg and msg["mime_type"].startswith("video")) or "file" in msg and msg["file"].endswith(".mp4"):
                        # video
                        msg_obj.msg_type = 2
                        msg_obj = self.media_processor(msg_obj, msg['file'], res_dir)
                    elif ("media_type" in msg and msg["media_type"] == "voice_message") or ("mime_type" in msg and msg["mime_type"].startswith("audio")) or "file" in msg and msg["file"].endswith(".ogg"):
                        # audio
                        msg_obj.msg_type = 4
                        msg_obj = self.media_processor(msg_obj, msg['file'], res_dir)
                    elif ("mime_type" in msg) and not msg["mime_type"].startswith("audio") and not msg["mime_type"].startswith("video"):
                        # file
                        msg_obj.msg_type = 5
                        msg_obj = self.media_processor(msg_obj, msg['file'], res_dir)
                elif "text" in msg:
                    msg_obj.msg_type = 1
                    if isinstance(msg["text"], list):
                        content_str = ""
                        for entity in msg["text"]:
                            if isinstance(entity, str):
                                content_str += entity
                            else:
                                content_str += entity["text"]
                        msg_obj.content = content_str
                    elif msg["text"] != "":
                        # text
                        msg_obj.content = msg["text"]
                else:
                    logger.error("Unknown message type at " + str(msg['date_unixtime']))
                    continue
            #msg_obj.sender = msg['sender_name']
            # if msg_obj.msg_type != 1 and msg_obj.msg_type != 6 and filepath.strip() != "":
            #     filename = split(filepath)[1]
            #     copy2(join(res_dir, filepath), join(self.attachment_dir, filename))
            #     msg_obj.content = filename
            msg_obj_list.append(msg_obj)
        #msg_obj_list.reverse()
        return msg_obj_list

    def media_processor(self, msg_obj, filepath, res_dir):
        if filepath.strip() != "":
            filename = split(filepath)[1]
            copy2(join(res_dir, filepath), join(self.attachment_dir, filename))
            msg_obj.content = filename
        return msg_obj


if __name__ == '__main__':
    chat_log_file_path = r"/Users/xxx/Downloads/Chat History/ChatExport_2024-02-11/result.json"
    res_dir = r"/Users/xxx/Downloads/Chat History/ChatExport_2024-02-11"
    attachment_dir = r"/Users/xxx/Downloads/Chat History/MediaStorage"
    tp = TelegramParser(attachment_dir=attachment_dir)
    full_msg_list = tp.msg_list_generator(chat_log_file_path=chat_log_file_path, res_dir=res_dir, timezone=12)
    for full_msg in full_msg_list:
        print(str(full_msg) + "\n")
