# coding = utf-8
import re
from typing import List

from Message import Message
from datetime import datetime
from shutil import copy2
import os


class WhatsAppParser(object):
    # 12/4/16, 5:22 PM - yyy: PTT-20210829-WA0030.opus (file attached)
    """docstring for WhatsAppParser"""

    def __init__(self, **kwargs):
        """
        WhatsApp Parser for WhatsApp Chat History
        """
        super(WhatsAppParser, self).__init__()

    def parse_txt(self, chat_log_file_path: str) -> List[str]:
        with open(chat_log_file_path, "r", encoding="utf-8") as f:
            all_data = f.readlines()
            # print(all_data)
            line_idx = []
            split_data = []
            for i, line in enumerate(all_data):
                if bool(re.search(r"^\d{1,2}/\d{1,2}/\d{2}, \d{1,2}:\d{1,2} [AP]M - ", line)):
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

    def convert_time(self, timestring: str) -> datetime:
        datetime_object = datetime.strptime(timestring, '%m/%d/%y, %I:%M %p')
        return datetime_object

    def msg_list_generator(self, **kwargs) -> List[Message]:
        chat_log_file_path = kwargs["chat_log_file_path"]
        attachment_dir = kwargs["attachment_dir"]
        res_dir = kwargs["res_dir"]
        split_data = self.parse_txt(chat_log_file_path)
        msg_list = []
        # file attached
        # opus jpg mp4 jpeg aac
        for item in split_data:
            msg = Message()
            msg.time = self.convert_time(item.split(" - ")[0])
            msg.sender = item.split(" - ")[1].split(": ")[0]
            msg.content = ": ".join(item.split(": ")[1:]).rstrip("\n")
            if msg.content.endswith(" (file attached)"):
                filename = msg.content.strip(" (file attached)")
                if filename.endswith(".mp4"):
                    msg.msg_type = 2
                elif filename.endswith(".jpg") or filename.endswith(".jpeg"):
                    msg.msg_type = 3
                elif filename.endswith(".opus"):
                    msg.msg_type = 4
                else:
                    msg.msg_type = 5
                copy2(os.path.join(res_dir, filename), os.path.join(attachment_dir, filename))
                msg.content = filename
            else:
                msg.msg_type = 1
            if not msg.sender.startswith("Messages and calls are end-to-end encrypted. "):
                msg_list.append(msg)
        return msg_list


if __name__ == '__main__':
    chat_log_file_path = r"/Users/xxx/Downloads/yyy/WhatsApp/WhatsApp Chat with yyy/WhatsApp Chat with yyy.txt"
    attachment_dir = r"/Users/xxx/Downloads/yyy/MediaStorage"
    res_dir = r"/Users/xxx/Downloads/yyy/WhatsApp/WhatsApp Media/ALL"
    wap = WhatsAppParser()
    msg_list = wap.msg_list_generator(chat_log_file_path=chat_log_file_path, attachment_dir=attachment_dir, res_dir=res_dir)
    for msg in msg_list:
        print(str(msg) + "\n")
