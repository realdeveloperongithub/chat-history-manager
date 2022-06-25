# coding = utf-8
from datetime import datetime
from sys import platform


class Message(object):
    """
    Attributes: time, type, sender, content
    time: datetime attribute
    msg_type: TEXT (1), VIDEO (2), IMAGE (3), VOICE (4), FILE(5), SYSTEM (6)
    for VIDEO, IMAGE and VOICE type, the content should only be the filename
    """

    time = datetime.now()
    msg_type = 0
    sender = ""
    content = ""

    def __init__(self):
        super(Message, self).__init__()
        # self.arg = arg

    def __str__(self) -> str:
        if platform == "win32":
            result = f'Time: {self.time.strftime("%#m/%#d/%y, %#I:%M %p")}\nMessage type: {self.msg_type}\n' \
                     f'Sender: {self.sender}\nContent: {self.content}'
        else:
            result = f'Time: {self.time.strftime("%-m/%-d/%y, %-I:%M %p")}\nMessage type: {self.msg_type}\n' \
                     f'Sender: {self.sender}\nContent: {self.content}'
        # return super().__str__()
        return result

    def __repr__(self) -> str:
        if platform == "win32":
            result = f'Time: {self.time.strftime("%#m/%#d/%y, %#I:%M %p")}\nMessage type: {self.msg_type}\n' \
                     f'Sender: {self.sender}\nContent: {self.content}'
        else:
            result = f'Time: {self.time.strftime("%-m/%-d/%y, %-I:%M %p")}\nMessage type: {self.msg_type}\n' \
                     f'Sender: {self.sender}\nContent: {self.content}'
        # return super().__str__()
        return result
