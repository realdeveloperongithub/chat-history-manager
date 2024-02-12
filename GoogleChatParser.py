# coding = utf-8
import logging
from datetime import datetime, timezone, timedelta
from os import listdir
from os.path import isfile, join, split
from shutil import copy2
from typing import List
import pytz
import json

from Message import Message

logger = logging.getLogger(__name__)


class GoogleChatParser(object):
    """
    Attributes: time, type, sender, content
    time: datetime attribute
    msg_type: TEXT (1), VIDEO (2), IMAGE (3), VOICE (4), FILE(5), SYSTEM (6)
    for VIDEO, IMAGE and VOICE type, the content should only be the filename
    """

    def __init__(self, **kwargs):
        """
        Google Chat Parser for Google / Hangouts Chat History
        :param attachment_dir: where to save all the multimedia files
        """
        super(GoogleChatParser, self).__init__()
        attachment_dir = kwargs['attachment_dir']
        #res_dir = kwargs['res_dir']
        #timezone = int(kwargs['timezone'])
        self.attachment_dir = attachment_dir
        #self.res_dir = res_dir
        #self.timezone = timezone

    # def timestamp_ms_to_local_datetime(self, timestamp: int, tz_offset: float) -> datetime:
    #     seconds = timestamp / 1000
    #     utc_time = datetime.utcfromtimestamp(seconds)
    #     offset = timedelta(hours=tz_offset)
    #     tz = timezone(offset)
    #     local_time = utc_time.replace(tzinfo=timezone.utc).astimezone(tz)
    #     return local_time

    def timestring_to_datetime(self, timestring: str, tz_offset: float) -> datetime:
        date_format = "%A, %B %d, %Y at %I:%M:%S %p"
        date_obj = datetime.strptime(timestring.split(" UTC")[0], date_format)
        offset = timedelta(hours=tz_offset)
        tz = timezone(offset)
        local_time_aware = date_obj.replace(tzinfo=timezone.utc).astimezone(tz)
        local_time_naive = local_time_aware.replace(tzinfo=None)
        return local_time_naive

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
            if 'attached_files' in msg:
                # multimedia
                for file in msg['attached_files']:
                    msg_obj = Message()
                    msg_obj.msg_type = 3
                    msg_obj.sender = msg['creator']['name']
                    if 'updated_date' in msg:
                        msg_obj.time = self.timestring_to_datetime(msg['updated_date'], timezone)
                    else:
                        msg_obj.time = self.timestring_to_datetime(msg['created_date'], timezone)
                    msg_obj_list.append(self.media_processor(msg_obj, file['export_name'], res_dir))
                if "text" in msg:
                    # caption
                    msg_obj_caption = Message()
                    msg_obj_caption.sender = msg['creator']['name']
                    if 'updated_date' in msg:
                        msg_obj_caption.time = self.timestring_to_datetime(msg['updated_date'], timezone)
                    else:
                        msg_obj_caption.time = self.timestring_to_datetime(msg['created_date'], timezone)
                    msg_obj_list.append(msg_obj_caption)
            elif 'text' in msg:
                msg_obj = Message()
                msg_obj.sender = msg['creator']['name']
                if 'updated_date' in msg:
                    msg_obj.time = self.timestring_to_datetime(msg['updated_date'], timezone)
                else:
                    msg_obj.time = self.timestring_to_datetime(msg['created_date'], timezone)
                msg_obj.msg_type = 1
                msg_obj.content = msg['text']
                msg_obj_list.append(msg_obj)
            else:
                if 'updated_date' in msg:
                    logger.error("Unknown message type at " + str(msg['updated_date']))
                else:
                    logger.error("Unknown message type at " + str(msg['created_date']))
                continue
        # msg_obj_list.reverse()
        return msg_obj_list

    def media_processor(self, msg_obj, filepath, res_dir):
        if filepath.strip() != "":
            filepath = filepath.replace("?", "_")
            filename = split(filepath)[1]
            copy2(join(res_dir, filepath), join(self.attachment_dir, filename))
            msg_obj.content = filename
        return msg_obj


if __name__ == '__main__':
    chat_log_file_path = r"/Users/xxx/Downloads/Chat History/Takeout/Google Chat/Groups/DM _yyy/messages.json"
    res_dir = r"/Users/xxx/Downloads/Chat History/Takeout/Google Chat/Groups/DM _yyy/"
    attachment_dir = r"/Users/xxx/Downloads/Chat History/yyy/MediaStorage"
    gcp = GoogleChatParser(attachment_dir=attachment_dir)
    full_msg_list = gcp.msg_list_generator(chat_log_file_path=chat_log_file_path, res_dir=res_dir, timezone=12)
    for full_msg in full_msg_list:
        print(str(full_msg) + "\n")
