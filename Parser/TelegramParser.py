# coding = utf-8
import os.path
from typing import List

from bs4 import BeautifulSoup
from Message import Message
from os import listdir
from os.path import isfile, join, split, basename, splitext
from datetime import datetime
from shutil import copy2
import logging
import copy
import re

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
        self.attachment_dir = kwargs['attachment_dir']

    def list_message_html(self, path: str) -> List[str]:
        return [join(path, f) for f in listdir(path) if
                isfile(join(path, f)) and f.startswith("messages")]

    def convert_time(self, timestring: str) -> datetime:
        if " UTC" in timestring:
            timestring = timestring.split(" UTC")[0]
        datetime_object = datetime.strptime(timestring, '%d.%m.%Y %H:%M:%S')
        return datetime_object

    def ogg_to_opus(self, content: str) -> str:
        return content.replace(".ogg", ".opus")

    def parse_html(self, html: str, chat_log_dir: str) -> List[Message]:
        # msg_obj = Message()
        msg_obj_list = []
        with open(html, encoding="utf8") as fp:
            soup = BeautifulSoup(fp, 'html.parser')
        from_name_temp = ""
        filename = ""
        for item in soup.findAll('div', {'class': ['message default clearfix', 'message default clearfix joined']}):
            msg_obj = Message()
            is_tgs_sticker = False
            if len(item.select("div.from_name")) > 0:
                from_name_temp = item.select("div.from_name")[0].text.strip()
            # print(from_name_temp)
            if bool(re.search(r" \d{2}.\d{2}.20\d{2} \d{2}:\d{2}:\d{2}", from_name_temp.split("  via @")[0])):
                continue
            else:
                msg_obj.sender = from_name_temp.split("  via @")[0]
                # print(item.select("div.pull_right.date.details")[0].get('title'))
                msg_obj.time = self.convert_time(item.select("div.pull_right.date.details")[0].get('title'))
                # decide direct message or forwarded
                if len(item.select("div.body > div.forwarded.body")) > 0:
                    item = item.select("div.body > div.forwarded.body")[0]
                if len(item.select("div.media_wrap.clearfix")) > 0:
                    if len(item.select("div.media_wrap.clearfix > a")) > 0:
                        href_text = item.select("div.media_wrap.clearfix > a")[0].get("href")
                        parent_dir, filename = split(href_text)
                        # print(filename)
                        if parent_dir == "video_files":
                            msg_obj.msg_type = 2
                        elif parent_dir == "photos":
                            msg_obj.msg_type = 3
                        elif parent_dir == "voice_messages":
                            filename = self.ogg_to_opus(filename)
                            msg_obj.msg_type = 4
                        elif parent_dir == "files":
                            filename = filename.split("@")[0]
                            msg_obj.msg_type = 5
                        elif parent_dir == "contacts":
                            msg_obj.msg_type = 6
                        elif parent_dir == "https://maps.google.com":
                            msg_obj.msg_type = 6
                        elif parent_dir.startswith("https://t.me/gamebot?") or parent_dir.startswith("http://t.me/gamebot?"):
                            msg_obj.msg_type = 6
                        elif parent_dir == "stickers":
                            if filename.endswith(".tgs"):
                                is_tgs_sticker = True
                                # msg_obj.msg_type = 1
                                msg_obj.msg_type = 5
                                # msg_obj.content = item.select("div.status.details")[0].text.strip()
                                filename = filename + "_thumb.jpg"
                            elif filename.endswith(".webp"):
                                msg_obj.msg_type = 5
                            else:
                                msg_obj.msg_type = -1
                                logger.error("Unknown message type at  " + str(msg_obj.time))
                        else:
                            msg_obj.msg_type = -1
                            logger.error("Unknown message type at " + str(msg_obj.time))
                        # if not is_tgs_sticker:
                        #     copy2(join(self.path, parent_dir, filename), join(self.attachment_dir, filename))
                        #     msg_obj.content = filename
                        if msg_obj.msg_type != 6 and msg_obj.msg_type != -1:
                            if not isfile(join(chat_log_dir, parent_dir, filename)):
                                filenames = os.listdir(join(chat_log_dir, parent_dir))
                                for file_name_string in filenames:
                                    if file_name_string.startswith(splitext(basename(filename))[0] + " "):
                                        filename = file_name_string
                                        break
                            copy2(join(chat_log_dir, parent_dir, filename), join(self.attachment_dir, filename))
                            msg_obj.content = filename

                    # if len(item.select("div.media_wrap.clearfix > div > div.body > div.title.bold")) > 0:
                    #     # print(item.select("div.media_wrap.clearfix > div > div.body > div.title.bold")[0].text.strip())
                    #     msg_obj.msg_type = 1
                    #     msg_obj.content = item.select("div.title")[0].text.strip()
                    if msg_obj.msg_type == 6:
                        if len(item.select("div.title")) > 0:
                            msg_obj.content += item.select("div.title")[0].text.strip() + "\n"
                        if len(item.select("div.description")) > 0:
                            msg_obj.content += item.select("div.description")[0].text.strip() + "\n"
                        if len(item.select("div.status")) > 0:
                            msg_obj.content += item.select("div.status")[0].text.strip() + "\n"
                if msg_obj.msg_type == 2 or msg_obj.msg_type == 3 or msg_obj.msg_type == 4 or msg_obj.msg_type == 5:
                    msg_obj.content = filename
                    msg_obj_list.append(msg_obj)
                    if len(item.select("div.text")) > 0:
                        description_msg_obj = copy.deepcopy(msg_obj)
                        description_msg_obj.msg_type = 1
                        description_msg_obj.content = item.select("div.text")[0].text.strip()
                        msg_obj_list.append(description_msg_obj)
                elif len(item.select("div.text")) > 0:
                    msg_obj.msg_type = 1
                    delimiter = "@@@@@"
                    for line_break in item.findAll('br'):
                        line_break.replaceWith(delimiter)
                    msg_obj.content += item.select("div.text")[0].text.strip().replace(delimiter, "\n")
                    msg_obj_list.append(msg_obj)
                else:
                    msg_obj_list.append(msg_obj)
                # if len(item.select("div.text")) > 0:
                #     msg_obj.msg_type = 1
                #     msg_obj.content += item.select("div.text")[0].text.strip()
                # if msg_obj.msg_type == 2 or msg_obj.msg_type == 3 or msg_obj.msg_type == 4 or msg_obj.msg_type == 5:
                #     msg_obj.content = filename

                # if len(item.select("div.text")) > 0:
                #     # print(item.select("div.text")[0].text.strip())
                #     msg_obj.msg_type = 1
                #     msg_obj.content += item.select("div.text")[0].text.strip()

                # msg_obj_list.append(msg_obj)
        return msg_obj_list

    # print(item.text.strip())
    def combine_msg_obj(self, html_list, chat_log_dir) -> List[Message]:
        full_msg_list = []
        for html in html_list:
            partial_list = self.parse_html(html, chat_log_dir)
            full_msg_list.extend(partial_list)
        return full_msg_list

    def msg_list_generator(self, **kwargs):
        chat_log_dir = kwargs['chat_log_dir']
        html_list = self.list_message_html(chat_log_dir)
        full_msg_list = self.combine_msg_obj(html_list, chat_log_dir)
        return full_msg_list


if __name__ == '__main__':
    chat_log_dir = r"/Users/xxx/Downloads/yyy/ChatExport_2022-06-05"
    attachment_dir = r"/Users/xxx/Downloads/yyy/MediaStorage"
    tp = TelegramParser(attachment_dir=attachment_dir)
    full_msg_list = tp.msg_list_generator(chat_log_dir=chat_log_dir)
    for full_msg in full_msg_list:
        print(str(full_msg) + "\n")
# for item in soup.select('div.text'):
#     print(item.text.strip())
