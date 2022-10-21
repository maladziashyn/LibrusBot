import requests
import time


def split_in_chunks(long_msg, characters=3000):
    if len(long_msg) < characters:
        return [long_msg]
    else:
        sp_idx = long_msg[:characters].rfind(' ')
        beginning = long_msg[:sp_idx]
        remaining = long_msg[sp_idx + 1:]
        return [beginning] + split_in_chunks(remaining, characters)


class Telegram:
    SEC_BETWEEN_MSGS = 3
    MAX_CHARACTERS = 3000

    def __init__(self, logger, bot_token, bot_chat_id):
        self.logger = logger
        self.bot_token = bot_token
        self.bot_chat_id = bot_chat_id

    def telegram_bot_sendtext(self, bot_message):
        split_msg_parts = split_in_chunks(bot_message)
        for part_msg in split_msg_parts:
            send_text = 'https://api.telegram.org/bot' + self.bot_token \
                        + '/sendMessage?chat_id=' + self.bot_chat_id \
                        + '&parse_mode=Markdown&text=' + part_msg
            requests.get(send_text)
            time.sleep(Telegram.SEC_BETWEEN_MSGS)

    def telegram_bot_sendfile(self, files):
        send_text = 'https://api.telegram.org/bot' + self.bot_token \
                    + '/sendDocument?chat_id=' + self.bot_chat_id
        requests.post(send_text, files=files)
        time.sleep(Telegram.SEC_BETWEEN_MSGS)

    def send_messages_list(self, msg_list):
        for msg in msg_list:
            self.telegram_bot_sendtext(msg)
