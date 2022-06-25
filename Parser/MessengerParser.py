# coding = utf-8
import logging
from datetime import datetime
from os import listdir
from os.path import isfile, join, split
from shutil import copy2
from typing import List

from bs4 import BeautifulSoup

from Message import Message

logger = logging.getLogger(__name__)


class MessengerParser(object):
    """
    Attributes: time, type, sender, content
    time: datetime attribute
    msg_type: TEXT (1), VIDEO (2), IMAGE (3), VOICE (4), FILE(5), SYSTEM (6)
    for VIDEO, IMAGE and VOICE type, the content should only be the filename
    """

    def __init__(self, **kwargs):
        """
        Messenger Parser for Messenger Chat History
        :param attachment_dir: where to save all the multimedia files
        """
        super(MessengerParser, self).__init__()
        attachment_dir = kwargs['attachment_dir']
        self.attachment_dir = attachment_dir

    def list_message_html(self, path: str) -> List[str]:
        return [join(path, f) for f in listdir(path) if
                isfile(join(path, f)) and f.startswith("messages")]

    def convert_time(self, timestring: str) -> datetime:
        # Jun 29, 2018 9:51:51pm
        datetime_object = datetime.strptime(timestring, '%b %d, %Y %I:%M:%S%p')
        return datetime_object

    def ogg_to_opus(self, content: str) -> str:
        return content.replace(".ogg", ".opus")

    def msg_list_generator(self, **kwargs) -> List[Message]:
        # msg_obj = Message()
        html = kwargs['chat_log_file_path']
        res_dir = kwargs['res_dir']
        msg_obj_list = []
        with open(html, encoding="utf8") as fp:
            soup = BeautifulSoup(fp, 'html.parser')
        for item in soup.findAll('div', {'class': ['_3-95 _a6-g']}):
            msg_obj = Message()
            msg_obj.sender = item.select("div._2ph_._a6-h._a6-i")[0].text.strip()
            msg_obj.time = self.convert_time(item.select("div._3-94._a6-o > div")[0].text.strip())
            filepath = ""
            if item.select("div._2ph_._a6-p > div > div:nth-child(2)")[0].text.strip() != "":
                msg_obj.msg_type = 1
                msg_obj.content = item.select("div._2ph_._a6-p > div > div:nth-child(2)")[0].text.strip()
            elif len(item.select("div._2ph_._a6-p > div > div:nth-child(5) > div > a > img")) > 0:
                # image
                msg_obj.msg_type = 3
                filepath = item.select("div._2ph_._a6-p > div > div:nth-child(5) > div > a > img")[0]["src"]
            elif len(item.select("div._2ph_._a6-p > div > div:nth-child(5) > div > video > a")) > 0:
                # video
                msg_obj.msg_type = 2
                filepath = item.select("div._2ph_._a6-p > div > div:nth-child(5) > div > video > a")[0].get("href")
            elif len(item.select("div._2ph_._a6-p > div > div:nth-child(5) > div > audio > a")) > 0:
                # voice message
                msg_obj.msg_type = 4
                filepath = item.select("div._2ph_._a6-p > div > div:nth-child(5) > div > audio > a")[0].get("href")
            elif len(item.select("div._2ph_._a6-p > div > div:nth-child(5) > div > a")) > 0:
                if item.select("div._2ph_._a6-p > div > div:nth-child(5) > div > a")[0].text.startswith("Download file:"):
                    msg_obj.msg_type = 5
                    filepath = item.select("div._2ph_._a6-p > div > div:nth-child(5) > div > a")[0].get("href")
                else:
                    logger.error("Unknown message type at " + str(msg_obj.time))
                    continue
            else:
                logger.error("Unknown message type at " + str(msg_obj.time))
                continue
            if msg_obj.msg_type != 1 and msg_obj.msg_type != 6 and filepath.strip() != "":
                filename = split(filepath)[1]
                copy2(join(res_dir, filepath), join(self.attachment_dir, filename))
                msg_obj.content = filename
            msg_obj_list.append(msg_obj)
        msg_obj_list.reverse()
        return msg_obj_list


if __name__ == '__main__':
    chat_log_file_path = r"/Users/xxx/Downloads/yyy/facebook-xxx/messages/inbox/yyy/message_1.html"
    res_dir = r"/Users/xxx/Downloads/yyy/facebook-xxx"
    attachment_dir = r"/Users/xxx/Downloads/yyy"
    mp = MessengerParser(attachment_dir=attachment_dir)
    full_msg_list = mp.msg_list_generator(chat_log_file_path=chat_log_file_path, res_dir=res_dir)
    for full_msg in full_msg_list:
        print(str(full_msg) + "\n")

