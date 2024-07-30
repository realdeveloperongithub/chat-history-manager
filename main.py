import copy
import yaml
from typing import List, Dict, Any
from Parser import (
    LineParser, OnlineChatroomParser, KakaoTalkParser, MetaParser,
    TelegramParser, WeChatParser, WhatsAppParser, GoogleChatParser
)
from Generator import HTMLGenerator, WhatsAppGenerator
from util.MessageListMerger import MessageListMerger

def load_config(file_path: str) -> Dict[str, Any]:
    with open(file_path, 'r') as f:
        return yaml.load(f, Loader=yaml.FullLoader)

def instantiate_class(module_name: str, class_name: str, **kwargs) -> Any:
    module = globals().get(module_name)
    if not module:
        raise ImportError(f"Module {module_name} not found.")
    cls = getattr(module, class_name, None)
    if not cls:
        raise ImportError(f"Class {class_name} not found in module {module_name}.")
    return cls(**kwargs)

if __name__ == '__main__':
    config = load_config("config.yml")
    full_list: List[Dict[str, Any]] = []

    print("Parser:")
    for module in config["Parser"]:
        seg_name = module["name"]
        print(seg_name)
        module_name = module["module"]
        try:
            parser_instance = instantiate_class(module_name, module_name, **module)
            result_msg_list = parser_instance.msg_list_generator(**module)
            full_list.extend(result_msg_list)
        except (ImportError, AttributeError, TypeError) as e:
            print(f"Error in {seg_name}: {repr(e)}")

    mlm = MessageListMerger()
    full_list = mlm.sort(full_list)

    print("Generator:")
    if config.get("print", False):
        for msg in full_list:
            print(str(msg) + "\n")

    for module in config["Generator"]:
        module_name = module["module"]
        print(module_name)
        original_full_list = copy.deepcopy(full_list)
        try:
            generator_instance = instantiate_class(module_name, module_name, **module)
            generator_instance.file_generator(original_full_list)
        except (ImportError, AttributeError, TypeError) as e:
            print(f"Error in {module_name}: {repr(e)}")
