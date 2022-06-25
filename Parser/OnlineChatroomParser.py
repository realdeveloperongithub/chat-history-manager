# coding = utf-8
import os
from datetime import datetime
from typing import List

from Message import Message
import re
from shutil import copy2


class OnlineChatroomParser(object):
    """
    Attributes: time, type, sender, content
    time: datetime attribute
    msg_type: TEXT (1), VIDEO (2), IMAGE (3), VOICE (4), FILE(5), SYSTEM (6)
    for VIDEO, IMAGE and VOICE type, the content should only be the filename
    """

    def __init__(self, **kwargs):
        """
        Online Chatroom Parser for Online Chatroom Chat History, it is for reference
        :param chat_log_file_path: path to the export directory
        """
        self.chat_log_file_path = kwargs['chat_log_file_path']

    def msg_list_generator(self, **kwargs) -> List[str]:
        chat_log_file_path = self.chat_log_file_path
        username1 = kwargs['username1']
        username2 = kwargs['username2']
        timezone_code = kwargs['timezone_code']
        with open(chat_log_file_path, "r", encoding="utf-8") as f:
            all_data = f.readlines()
            # print(all_data)
            line_idx = []
            split_data = []
            msg_list = []
            last_user = ""
            last_date = ""
            last_time = ""
            for i, line in enumerate(all_data):
                if line.strip() == username1:
                    last_user = username1
                elif line.strip() == username2:
                    last_user = username2
                # 23:32 CST
                elif bool(re.search(r"\d{1,2}:\d{2} CST", line.strip())):
                    last_time = line.strip()
                # elif line.endswith(f" {timezone_code}"):
                #     last_time = line
                # Sep 01, 2016
                elif bool(
                        re.search(r"^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) \d{2}, 20\d{2}", line.strip())):
                    last_date = line.strip()
                else:
                    content = line.strip()
                    msg = Message()
                    msg.time = self.convert_time(last_date + " " + last_time.replace(" " + timezone_code, ""))
                    msg.sender = last_user
                    msg.msg_type = 1
                    msg.content = content
                    msg_list.append(msg)
        return msg_list

    def convert_time(self, timestring: str) -> datetime:
        # Sep 01, 2016 23:32
        datetime_object = datetime.strptime(timestring, '%b %d, %Y %H:%M')
        return datetime_object


if __name__ == '__main__':
    msg_list = []
    chat_log_file_path = r"/Users/xxx/Downloads/telegram/chathistory.txt"
    ip = OnlineChatroomParser(chat_log_file_path=chat_log_file_path)
    msg_list = ip.msg_list_generator(username1="yyy", username2="xxx", timezone_code="HKT")
    # print(len(msg_list))
    for msg in msg_list:
        print(str(msg) + "\n")
