import copy

import yaml
from Parser import LineParser, OnlineChatroomParser, KakaoTalkParser, MetaParser, TelegramParser, WeChatParser, \
    WhatsAppParser
from Generator import HTMLGenerator, WhatsAppGenerator
from util.MessageListMerger import MessageListMerger

if __name__ == '__main__':
    f = open("config.yml")
    config = yaml.load(f, Loader=yaml.FullLoader)
    full_list = []
    print("Parser:")
    for module in config["Parser"]:
        seg_name = module["name"]
        print(seg_name)
        module_name = module["module"]
        # print(module_name)
        try:
            obj = eval(f"{module_name}.{module_name}(**{module})")
            result_msg_list = obj.msg_list_generator(**module)
            full_list.extend(result_msg_list)
        except Exception as e:
            print(repr(e))
    mlm = MessageListMerger()
    full_list = mlm.sort(full_list)
    print("Generator:")
    if config["print"]:
        for msg in full_list:
            print(str(msg) + "\n")
    for module in config["Generator"]:
        module_name = module["module"]
        print(module_name)
        original_full_list = copy.deepcopy(full_list)
        try:
            obj = eval(f"{module_name}.{module_name}(**{module})")
            obj.file_generator(original_full_list)
        except Exception as e:
            print(repr(e))
