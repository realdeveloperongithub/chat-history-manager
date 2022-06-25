# coding = utf-8
import os
from datetime import datetime
from typing import List

from Message import Message
import re
from shutil import copy2


class KakaoTalkParser(object):
    # October 12, 2020, 6:49 AM
    # October 12, 2020, 6:49 AM, yyy : really? why i dont know about that
    """
    Attributes: time, type, sender, content
    time: datetime attribute
    msg_type: TEXT (1), VIDEO (2), IMAGE (3), VOICE (4), FILE(5), SYSTEM (6)
    for VIDEO, IMAGE and VOICE type, the content should only be the filename
    """

    def __init__(self, **kwargs):
        """
        Kakao Talk Parser for Kakao Talk Chat History
        :param res_dir: path to the export directory
        :param attachment_dir: where to save all the multimedia files
        """
        self.res_dir = kwargs['res_dir']
        self.attachment_dir = kwargs['attachment_dir']

    def parse_txt(self, chat_log_file_path: str) -> List[str]:
        with open(chat_log_file_path, "r", encoding="utf-8") as f:
            all_data = f.readlines()
            # print(all_data)
            line_idx = []
            split_data = []
            for i, line in enumerate(all_data):
                if bool(re.search(r"^(January|February|March|April|May|June|"
                                  r"July|August|September|October|November|December) "
                                  r"\d{1,2}, (19|20)\d{2}, \d{1,2}:\d{1,2} [AP]M", line)):
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
        # October 12, 2020, 6:49 AM
        datetime_object = datetime.strptime(timestring, '%B %d, %Y, %I:%M %p')
        return datetime_object

    def convert_to_message(self, list: List[str]) -> List[Message]:
        msg_list = []
        # file attached
        # opus jpg mp4 jpeg aac
        for item in list:
            if bool(re.search(r"^(January|February|March|April|May|June|"
                              r"July|August|September|October|November|December) "
                              r"\d{1,2}, (19|20)\d{2}, \d{1,2}:\d{1,2} [AP]M, ", item)):
                msg = Message()
                pattern = re.compile(r"^(January|February|March|April|May|June|"
                                     r"July|August|September|October|November|December)"
                                     r"( \d{1,2}, )(19|20)(\d{2}, \d{1,2}:\d{1,2} [AP]M), ")
                result1 = pattern.findall(item)
                time_string = "".join(list(result1[0]))
                msg.time = self.convert_time(time_string)
                item = item.lstrip(time_string + ", ")
                msg.sender = item.split(" : ")[0]
                msg.content = " : ".join(item.split(" : ")[1:]).rstrip("\n")
                if bool(re.search(r"^([a-z0-9]{64}\.[a-z0-9]{3,4})$", msg.content)):
                    file_path = os.path.join(self.res_dir, msg.content)
                    if os.path.isfile(file_path):
                        filename = msg.content
                        if filename.endswith(".mp4"):
                            msg.msg_type = 2
                        elif filename.endswith(".jpg") or filename.endswith(".jpeg") or filename.endswith(".png"):
                            msg.msg_type = 3
                        elif filename.endswith(".m4a"):
                            msg.msg_type = 4
                        else:
                            msg.msg_type = 5
                        msg.content = filename
                        copy2(os.path.join(self.res_dir, filename), os.path.join(self.attachment_dir, filename))
                    else:
                        msg.msg_type = 1
                    if not (msg.sender.startswith("KakaoTalk Chats with ") or msg.sender.startswith("Date Saved : ")):
                        msg_list.append(msg)
        return msg_list

    def msg_list_generator(self, **kwargs):
        chat_log_file_path = kwargs['chat_log_file_path']
        split_data_list = self.parse_txt(chat_log_file_path)
        msg_list = self.convert_to_message(split_data_list)
        return msg_list


if __name__ == '__main__':
    res_dir = r"/Users/xxx/Downloads/Kakao Talk Export"
    attachment_dir = r"/Users/xxx/Downloads/MediaStorage"
    chat_log_file_path = os.path.join(res_dir, "KakaoTalkChats.txt")
    ktp = KakaoTalkParser(res_dir=res_dir, attachment_dir=attachment_dir)
    msg_list = ktp.msg_list_generator(chat_log_file_path=chat_log_file_path)
    for msg in msg_list:
        print(str(msg) + "\n")
