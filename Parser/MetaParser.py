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


class MetaParser(object):
    """
    Attributes: time, type, sender, content
    time: datetime attribute
    msg_type: TEXT (1), VIDEO (2), IMAGE (3), VOICE (4), FILE(5), SYSTEM (6)
    for VIDEO, IMAGE and VOICE type, the content should only be the filename
    """

    def __init__(self, **kwargs):
        """
        Meta Parser for Messenger/Instagram Chat History
        :param attachment_dir: where to save all the multimedia files
        """
        super(MetaParser, self).__init__()
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
    
    def timestamp_ms_to_local_datetime(self, timestamp: int, tz_offset: float) -> datetime:
        seconds = timestamp / 1000
        utc_time = datetime.utcfromtimestamp(seconds)
        offset = timedelta(hours=tz_offset)
        tz = timezone(offset)
        local_time_aware = utc_time.replace(tzinfo=timezone.utc).astimezone(tz)
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
            msg_obj = Message()
            msg_obj.sender = msg['sender_name']
            msg_obj.time = self.timestamp_ms_to_local_datetime(msg['timestamp_ms'], timezone)

            if 'photos' in msg:
                # image
                msg_obj.msg_type = 3
                for photo in msg['photos']:
                    msg_obj_list.append(self.media_processor(msg_obj, photo['uri'], res_dir))
            elif 'videos' in msg:
                msg_obj.msg_type = 2
                for video in msg['videos']:
                    msg_obj_list.append(self.media_processor(msg_obj, video['uri'], res_dir))
            elif 'audio_files' in msg:
                msg_obj.msg_type = 4
                for audio_file in msg['audio_files']:
                    msg_obj_list.append(self.media_processor(msg_obj, audio_file['uri'], res_dir))
            elif 'share' in msg:
                msg_obj.msg_type = 1
                if ('link' not in msg['share']) and ('share_text' in msg['share']):
                    msg_obj.content = msg['share']['share_text'].encode('latin1').decode('utf8')
                else:
                    msg_obj.content = msg['share']['link']
            elif 'content' in msg:
                msg_obj.msg_type = 1
                msg_obj.content = msg['content'].encode('latin1').decode('utf8')
                # msg_obj_list.append(msg_obj)
            else:
                logger.error("Unknown message type at " + str(msg['timestamp_ms']))
                continue
            # if msg_obj.msg_type != 1 and msg_obj.msg_type != 6 and filepath.strip() != "":
            #     filename = split(filepath)[1]
            #     copy2(join(res_dir, filepath), join(self.attachment_dir, filename))
            #     msg_obj.content = filename
            msg_obj_list.append(msg_obj)
        msg_obj_list.reverse()
        return msg_obj_list

    def media_processor(self, msg_obj, filepath, res_dir):
        if filepath.strip() != "":
            filename = split(filepath)[1]
            copy2(join(res_dir, filepath), join(self.attachment_dir, filename))
            msg_obj.content = filename
        return msg_obj


if __name__ == '__main__':
    chat_log_file_path = r"/Users/xxx/Downloads/yyy/facebook-xxx/messages/inbox/yyy/message_1.json"
    res_dir = r"/Users/xxx/Downloads/yyy/facebook-xxx"
    attachment_dir = r"/Users/xxx/Downloads/yyy"
    mp = MetaParser(attachment_dir=attachment_dir)
    full_msg_list = mp.msg_list_generator(chat_log_file_path=chat_log_file_path, res_dir=res_dir, timezone=12)
    for full_msg in full_msg_list:
        print(str(full_msg) + "\n")
