## Chat History Organizer
### How this project was born
Originally, this project was to import chat history into Telegram, but now we can do more with it. In January 2021, Telegram [announced](https://telegram.org/blog/move-history) a new feature for people to bring their chat history – including videos and documents – to Telegram from apps like WhatsApp, Line and KakaoTalk.

The founder of Telegram, Pavel Durov,  on his personal channel also [promised](https://t.me/durov/150) to provide "free APIs for third-party developers who want to create tools that will allow users to import messages to Telegram from anywhere".

The API has been published, but for me, it is not easy to manipulate it. And the existing way of importing chat history has many to be improved:
1. Images and videos  
Images and videos import is only available when you import chat history from WhatsApp. When you import from Line or Kakao Talk, all the multimedia files will be ignored.
2. 100 messages limitation  
If the target chat (where you import messages to) has fewer than 100 messages, Telegram will mix the existing messages in a Telegram chat with the imported messages in one unified timeline. However I believe most people have more than 100 messages in the chat.
3. (Of course) Support for more apps  
Currently only three apps (Line, Kakao Talk, WhatsApp) are supported. We need more apps to be supported.

### What does this project do

**Basic feature:**

With multiple Parsers and Generators, this project helps you to organize chat history from other apps. Theoretically, if you are able to create a parser, you can import chat history from any app you want, including the old-fashioned online chatroom :)

**Exclusively for Telegram:**

If you convert all chat history to WhatsApp format, you will be able to import all chat history into Telegram, with a unified timeline and with all media files reserved.

**Supported apps:**

- Line
- Kakao Talk
- Messenger
- WeChat
- WhatsApp
- Telegram

### Prerequisites

1. A rooted Android phone (refer to the table below)
2. python 3
3. ffmpeg
4. `pip install -r requirements.txt`
6. Different source apps have different requirements, see below:

| Source App | Root Needed | Comments                                                                                                                                                                                                                                                                                                                      |
|------------|-------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Kakao Talk | ❌           | Chatroom Settings - Export Messages                                                                                                                                                                                                                                                                                           |
| Line       | ✅           | Chatroom - Other settings - Export chat history.<br />A local database at `/data/data/jp.naver.line.android/databases/naver_line`<br />Resources file at `/storage/emulated/0/Android/data/jp.naver.line.android/files/chats`.                                                                                                |
| Messenger  | ❌           | [Download Your Information](https://www.facebook.com/dyi)                                                                                                                                                                                                                                                                     |
| Telegram   | ❌           | Chatroom - Export chat history (using HTML format)                                                                                                                                                                                                                                                                            |
| WeChat     | ✅           | A decrypted WeChat database (EnMicroMsg.db) and all the resources files.</br>All voice messages need to be converted to opus format (you can refer to [silk2mp3](https://github.com/Coldison/silk2mp3) and then convert mp3 to opus).<br/>Please refer to the [wechat-dump](https://github.com/ppwwyyxx/wechat-dump) project. |
| WhatsApp   | ✅ [^1]      | Chatroom - More - Export chat</br>All files under `/storage/emulated/0/Android/media/com.whatsapp/WhatsApp/Media` need to be collected and put into one folder.                                                                                                                                                               |

[^1]: Root is not needed if there's not much media in the WhatsApp chat. In that case, share to local storage with a file manager (for example [Solid Explorer](https://play.google.com/store/apps/details?id=pl.solidexplorer2)) will do.
7. All the voice message files, need to be converted to .opus format. Code snippet for converting all amr files in one folder.
```shell
find /folder/to/amr/files -name '*.amr' -print0 | \
xargs -0 -I FILE \
sh -c 'ffmpeg -i "$1" "${1%.amr}.opus"' -- FILE
```

### How to use

1. Rename `config-sample.yml` to `config.yml`.
2. Set modules
   1. In the `config.yml` file comment out the Parser modules and Generator modules you don't want to use.
   2. Remember that you can add multiple accounts of the same module by specifying different `name`. See Kakao Talk module in `config-sample.yml`.
3. Settings for different Generators, see below:

| Generator | Comments                                                                                                                                                                                     |
|-----------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| WhatsApp  | `send_recv_dict` is the dict for mapping from different usernames.</br>`base_numbers` defines the new name of media files. Leaving it unchanged or change it to current date is recommended. |
| HTML      | `send_recv_dict` is the dict for mapping from different usernames.                                                                                                                           |

4. Run `python3 main.py`
5. For importing chat history into Telegram, please refer to [this project](https://github.com/realdeveloperongithub/Telegram).

### FAQ

1. Support for iOS  
This project is actually manipulating WhatsApp exported files in the system level. That's why a rooted Android phone is a must. Sadly on iOS, we can't do that. In other words, the target chat (where to import the chat history) must be on Android platform.  
The good news is, though, we are importing chat history to Telegram, so after importing, all the chat history will be also visible on your iOS devices.

### To-do

1. Support for more apps
- Google Chats / Hangouts ([Google Takeout](https://takeout.google.com/))
- Skype ([Export data](https://secure.skype.com/en/data-export))
- Instagram ([Download Your Data](https://www.instagram.com/download/request/))

### Credit

[wechat-dump](https://github.com/ppwwyyxx/wechat-dump)

### Donation

ETH: 0xbdb823ea4bcee4c5bdecc1544a29bbdd2034028a
