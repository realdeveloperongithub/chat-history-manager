# coding = utf-8
import os.path
from typing import List
import logging
from Generator import HTMLWrapper
from Message import Message
from sys import platform

logger = logging.getLogger(__name__)


class HTMLGenerator(object):
    """Generates HTML for preview"""

    html_wrapper = HTMLWrapper.html_wrapper
    html_history_wrapper = HTMLWrapper.html_history_wrapper
    css = HTMLWrapper.css
    video_wrapper = HTMLWrapper.video_wrapper
    voice_wrapper = HTMLWrapper.voice_wrapper
    image_wrapper = HTMLWrapper.image_wrapper
    file_wrapper = HTMLWrapper.file_wrapper

    def __init__(self, **kwargs):
        """
        Generates an HTML page for preview
        :param attachment_dir: folder with all attachment files
        :param result_dir: path to put the HTML file and CSS file
        :param html_name: name of the HTML file
        """
        super(HTMLGenerator, self).__init__()
        attachment_dir = kwargs['attachment_dir']
        result_dir = kwargs['result_dir']
        html_name = kwargs['html_name']
        self.send_recv_dict = kwargs['send_recv_dict']
        self.attachment_dir = attachment_dir
        self.result_dir = result_dir
        self.html_name = html_name

    def sender_replace(self, sender: str) -> str:
        return self.send_recv_dict[sender]

    def convert_time(self, datetime_object) -> str:
        # windows
        if platform == "win32":
            converted_time = datetime_object.strftime("%#m/%#d/%y, %#I:%M %p")
        # linux or macos
        #if platform == "linux" or platform == "linux2" or platform == "darwin":
        else:
            converted_time = datetime_object.strftime("%-m/%-d/%y, %-I:%M %p")
        return converted_time

    def html_formatter(self, msg_list: List[Message]) -> str:
        logger.info("Converting message list to html")
        content = ""
        for msg in msg_list:
            msg.sender = self.sender_replace(msg.sender)
            if msg.msg_type == 1:
                content = content + self.html_history_wrapper.format(self.convert_time(msg.time), msg.sender,
                                                                     msg.content) + "\n"
            elif msg.msg_type == 2:
                file_content = self.video_wrapper.format(os.path.join(self.attachment_dir, msg.content))
                content = content + self.html_history_wrapper.format(self.convert_time(msg.time), msg.sender,
                                                                     file_content) + "\n"
            elif msg.msg_type == 3:
                file_content = self.image_wrapper.format(os.path.join(self.attachment_dir, msg.content))
                content = content + self.html_history_wrapper.format(self.convert_time(msg.time), msg.sender,
                                                                     file_content) + "\n"
            elif msg.msg_type == 4:
                file_content = self.voice_wrapper.format(os.path.join(self.attachment_dir, msg.content))
                content = content + self.html_history_wrapper.format(self.convert_time(msg.time), msg.sender,
                                                                     file_content) + "\n"
            else:
                file_content = self.file_wrapper.format(os.path.join(self.attachment_dir, msg.content), msg.content)
                content = content + self.html_history_wrapper.format(self.convert_time(msg.time), msg.sender,
                                                                     file_content) + "\n"

        return self.html_wrapper.format(content)

    def file_generator(self, msg_list):
        converted_data = self.html_formatter(msg_list)
        with open(os.path.join(self.result_dir, "style.css"), "w", encoding="utf-8") as f:
            f.writelines(self.css)
        with open(os.path.join(self.result_dir, self.html_name), "w", encoding="utf-8") as f:
            f.writelines(converted_data)


if __name__ == '__main__':
    msg_list = []
    attachment_dir = r"/Users/xxx/Downloads/yyy/attachment"
    result_dir = r"/Users/xxx/Downloads/yyy/html"
    html_name = "HTMLPreview.html"
    send_recv_dict = {"me": "xxx",
                      "yyy": "yyy",
                      "yyy2": "yyy2"}
    hg = HTMLGenerator(attachment_dir=attachment_dir, result_dir=result_dir, html_name=html_name, send_recv_dict=send_recv_dict)
    hg.file_generator(msg_list)
