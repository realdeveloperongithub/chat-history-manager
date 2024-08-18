# coding = utf-8
import os
from shutil import move, copy2
from typing import List, Tuple
from sys import platform
from Message import Message


class WhatsAppGenerator(object):
    """docstring for WhatsAppGenerator
    1. rename
    2. file attached"""

    # global image_filename_template
    # image_filename_template = "IMG-{}-WA{}.jpg"
    # global video_filename_template
    # video_filename_template = "VID-{}-WA{}.mp4"
    # global voice_filename_template
    # voice_filename_template = "PTT-{}-WA{}.opus"

    def __init__(self, **kwargs):
        """
        WhatsApp-format Chat History Generator
        :param attachment_dir: folder with all attachment files
        :param result_path: path to put the text file of whatsapp-format chat history file
        :param send_recv_dict: key-value pairs of sender names for replacement can be more than two pairs
        :param base_numbers: base number for whatsapp images, videos and voice files
        """
        super(WhatsAppGenerator, self).__init__()
        attachment_dir = kwargs['attachment_dir']
        result_path = kwargs['result_path']
        send_recv_dict = kwargs['send_recv_dict']
        base_numbers = kwargs['base_numbers']
        self.attachment_dir = attachment_dir
        self.send_recv_dict = send_recv_dict
        self.result_path = result_path
        self.image_filename_template = "IMG-{}-WA{}.jpg"
        self.video_filename_template = "VID-{}-WA{}.mp4"
        self.voice_filename_template = "PTT-{}-WA{}.opus"
        # image_base_number = ["20210829", 1]
        # video_base_number = ["20210829", 1]
        # voice_base_number = ["20210829", 1]
        if "image_base_number" in base_numbers.keys():
            self.image_base_number = base_numbers["image_base_number"]
        if "video_base_number" in base_numbers.keys():
            self.video_base_number = base_numbers["video_base_number"]
        if "voice_base_number" in base_numbers.keys():
            self.voice_base_number = base_numbers["voice_base_number"]
        self.multimedia_dict = {3: ["Image message ", self.image_base_number, self.image_filename_template],
                                2: ["Video message ", self.video_base_number, self.video_filename_template],
                                4: ["Voice message ", self.voice_base_number, self.voice_filename_template]}

    def convert_time(self, datetime_object) -> str:
        # windows
        if platform == "win32":
            converted_time = datetime_object.strftime("%#m/%#d/%y, %#I:%M %p")
        # linux or macos
        # if platform == "linux" or platform == "linux2" or platform == "darwin":
        else:
            converted_time = datetime_object.strftime("%-m/%-d/%y, %-I:%M %p")
        return converted_time

    def sender_replace(self, sender: str) -> str:
        return self.send_recv_dict[sender]

    def generator(self, msg_list: List[Message]) -> Tuple[List[str], List[Message]]:
        converted_str_list = []
        converted_msg_list = []
        filename_change_dict = {}
        for msg in msg_list:
            msg.sender = self.sender_replace(msg.sender)
            time = self.convert_time(msg.time)
            content = msg.content
            if msg.msg_type == 2 or msg.msg_type == 3 or msg.msg_type == 4 or msg.msg_type == 5:
                if msg.msg_type != 5 and (msg.content.startswith(self.multimedia_dict[msg.msg_type][0])):
                    pass
                else:
                    original_filename = msg.content
                    content = "{} (file attached)".format(original_filename)
                    msg.content = "{}".format(original_filename)
                    if msg.msg_type != 5 and self.multimedia_dict[msg.msg_type][1]:
                        # rename
                        new_filename = self.multimedia_dict[msg.msg_type][2].format(
                            self.multimedia_dict[msg.msg_type][1][0],
                            "{:04d}".format(int(self.multimedia_dict[msg.msg_type][1][1])))
                        self.multimedia_dict[msg.msg_type][1][1] = int(self.multimedia_dict[msg.msg_type][1][1]) + 1
                        if original_filename not in filename_change_dict:
                            filename_change_dict[original_filename] = new_filename
                            move(os.path.join(self.attachment_dir, original_filename),
                                 os.path.join(self.attachment_dir, new_filename))
                        else:
                            copy2(os.path.join(self.attachment_dir, filename_change_dict[original_filename]),
                                  os.path.join(self.attachment_dir, new_filename))
                        content = "{} (file attached)".format(new_filename)
                        msg.content = "{}".format(new_filename)
            converted_str_list.append(f"{time} - {msg.sender}: {content}" + "\n")
            converted_msg_list.append(msg)
        return converted_str_list, converted_msg_list

    def file_generator(self, msg_list):
        converted_str_list, converted_msg_list = self.generator(msg_list)
        with open(self.result_path, "w", encoding="utf-8") as f:
            f.writelines(converted_str_list)
        return converted_msg_list


if __name__ == '__main__':
    msg_list = []
    result_path = r"/Users/xxx/Downloads/yyy/html/yyy.txt"
    attachment_dir = r"/Users/xxx/Downloads/yyy/MediaStorage"
    send_recv_dict = {"xxx": "xxx", "yyy": "yyy"}
    base_numbers = {"image_base_number": ["20210829", 1],
                    "video_base_number": ["20210829", 1],
                    "voice_base_number": ["20210829", 1]}
    wg = WhatsAppGenerator(attachment_dir=attachment_dir, result_path=result_path, send_recv_dict=send_recv_dict,
                           base_numbers=base_numbers)
    wg.file_generator(msg_list)
