# coding = utf-8
import logging
from datetime import datetime, timezone, timedelta
from os import listdir
from os.path import isfile, join, split
from shutil import copy2
from typing import List, Dict, Any
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

    def __init__(self, attachment_dir: str):
        """
        Telegram Parser for Telegram Chat History
        :param attachment_dir: Where to save all the multimedia files
        """
        super(TelegramParser, self).__init__()
        self.attachment_dir = attachment_dir

    def timestamp_to_local_datetime(self, timestamp: int, tz_offset: float) -> datetime:
        utc_time = datetime.utcfromtimestamp(timestamp)
        offset = timedelta(hours=tz_offset)
        tz = timezone(offset)
        local_time_aware = utc_time.replace(tzinfo=timezone.utc).astimezone(tz)
        local_time_naive = local_time_aware.replace(tzinfo=None)
        return local_time_naive

    def ogg_to_opus(self, content: str) -> str:
        return content.replace(".ogg", ".opus")

    def msg_list_generator(self, chat_log_file_path: str, res_dir: str, timezone: int) -> List[Message]:
        msg_obj_list: List[Message] = []
        try:
            with open(chat_log_file_path, encoding="utf8") as json_messages:
                messages = json.load(json_messages)['messages']
        except IOError as e:
            logger.error(f"Error opening chat log file: {repr(e)}")
            return msg_obj_list
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error parsing JSON: {repr(e)}")
            return msg_obj_list

        for msg in messages:
            msg_obj = self.parse_message(msg, res_dir, timezone)
            if msg_obj:
                msg_obj_list.extend(msg_obj)

        return msg_obj_list

    def parse_message(self, msg: Dict[str, Any], res_dir: str, timezone: int) -> List[Message]:
        msg_obj_list = []
        msg_obj = Message()
        msg_obj.time = self.timestamp_to_local_datetime(int(msg['date_unixtime']), timezone)

        try:
            if msg['type'] == "service":
                msg_obj.msg_type = 6
                msg_obj.sender = msg['actor']
                msg_obj.content = f"{msg['actor']}: {msg['action']}"
            elif msg['type'] == "message":
                msg_obj.sender = msg['from']
                if "self_destruct_period_seconds" in msg:
                    msg_obj.msg_type = 1
                    msg_obj.content = self.construct_self_destruct_content(msg)
                    msg_obj_list.append(msg_obj)
                elif "photo" in msg:
                    msg_obj.msg_type = 3
                    msg_obj = self.media_processor(msg_obj, msg['photo'], res_dir)
                    msg_obj_list.append(msg_obj)
                    msg_obj_list.extend(self.handle_caption(msg_obj, msg))
                elif "file" in msg:
                    msg_obj = self.handle_file_message(msg_obj, msg, res_dir)
                    if msg_obj:
                        msg_obj_list.append(msg_obj)
                        msg_obj_list.extend(self.handle_caption(msg_obj, msg))
                elif "text" in msg:
                    msg_obj.msg_type = 1
                    msg_obj.content = self.construct_text_content(msg["text"])
                    msg_obj_list.append(msg_obj)
                else:
                    logger.error(f"Unknown message type at {msg['date_unixtime']}")
            else:
                logger.error(f"Unsupported message type at {msg['date_unixtime']}")
        except KeyError as e:
            logger.error(f"KeyError processing message: {repr(e)}")

        return msg_obj_list

    def construct_self_destruct_content(self, msg: Dict[str, Any]) -> str:
        content_str = f"Self-destruct: {msg['self_destruct_period_seconds']} seconds"
        if "text" in msg and msg["text"] != "":
            content_str += "\n" + msg["text"]
        return content_str

    def handle_caption(self, msg_obj: Message, msg: Dict[str, Any]) -> List[Message]:
        msg_obj_list = []
        if "text" in msg and msg["text"] != "":
            msg_obj_caption = Message()
            msg_obj_caption.msg_type = 1
            msg_obj_caption.sender = msg_obj.sender
            msg_obj_caption.time = msg_obj.time
            msg_obj_caption.content = msg["text"]
            msg_obj_list.append(msg_obj_caption)
        return msg_obj_list

    def handle_file_message(self, msg_obj: Message, msg: Dict[str, Any], res_dir: str) -> Message:
        try:
            if ("media_type" in msg and msg["media_type"] == "video_file") or \
               ("mime_type" in msg and msg["mime_type"].startswith("video")) or \
               "file" in msg and msg["file"].endswith(".mp4"):
                msg_obj.msg_type = 2
                msg_obj = self.media_processor(msg_obj, msg['file'], res_dir)
            elif ("media_type" in msg and msg["media_type"] == "voice_message") or \
                 ("mime_type" in msg and msg["mime_type"].startswith("audio")) or \
                 "file" in msg and msg["file"].endswith(".ogg"):
                msg_obj.msg_type = 4
                msg_obj = self.media_processor(msg_obj, msg['file'], res_dir)
            elif ("mime_type" in msg) and not msg["mime_type"].startswith("audio") and not msg["mime_type"].startswith("video"):
                msg_obj.msg_type = 5
                msg_obj = self.media_processor(msg_obj, msg['file'], res_dir)
            else:
                logger.error(f"Unknown file type at {msg['date_unixtime']}")
                return None
        except KeyError as e:
            logger.error(f"KeyError processing file message: {repr(e)}")
            return None
        return msg_obj

    def construct_text_content(self, text: Any) -> str:
        if isinstance(text, list):
            return ''.join(entity if isinstance(entity, str) else entity["text"] for entity in text)
        return text if text else ""

    def media_processor(self, msg_obj: Message, filepath: str, res_dir: str) -> Message:
        if filepath.strip():
            try:
                filename = split(filepath)[1]
                copy2(join(res_dir, filepath), join(self.attachment_dir, filename))
                msg_obj.content = filename
            except IOError as e:
                logger.error(f"Error copying file: {repr(e)}")
        return msg_obj


if __name__ == '__main__':
    chat_log_file_path = r"/Users/xxx/Downloads/Chat History/ChatExport_2024-02-11/result.json"
    res_dir = r"/Users/xxx/Downloads/Chat History/ChatExport_2024-02-11"
    attachment_dir = r"/Users/xxx/Downloads/Chat History/MediaStorage"
    tp = TelegramParser(attachment_dir=attachment_dir)
    full_msg_list = tp.msg_list_generator(chat_log_file_path=chat_log_file_path, res_dir=res_dir, timezone=12)
    for full_msg in full_msg_list:
        print(str(full_msg) + "\n")
