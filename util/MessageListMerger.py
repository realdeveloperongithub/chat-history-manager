class MessageListMerger(object):
    """docstring for MessageListMerger"""

    def __init__(self):
        super(MessageListMerger, self).__init__()

    def merge(self, *multi_msg_list):
        full_list = []
        for item in multi_msg_list:
            full_list.extend(item)
        return full_list

    def sort(self, list):
        list.sort(key=lambda x: x.time)
        return list

    def convert(self, *multi_msg_list):
        full_list = self.merge(*multi_msg_list)
        return self.sort(full_list)


if __name__ == '__main__':
    pass
