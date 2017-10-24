from io import BytesIO
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.tl.types import InputPeerChannel
import threading
from config import *

client = TelegramClient('tg_client', CLIENT_API_ID, CLIENT_API_HASH)
client.connect()
if (not client.is_user_authorized()):
    client.sign_in(CLIENT_PHONE)
    try:
        client.sign_in(code=input('Enter code: '))
    except SessionPasswordNeededError:
        client.sign_in(password=CLIENT_2FA_PASSWORD)


def get_file_stream(message_ids):
    peer = InputPeerChannel(CHANNEL_REPLY_TELETHON_ID,
                            CHANNEL_REPLY_TELETHON_HASH)
    messages = []
    for message_id in message_ids:
        messages.append(client.get_message_history(
            peer, offset_id=message_id + 1, limit=1)[1][0])

    for message in messages:
        stream = BytesIO()
        thread = threading.Thread(target=client.download_media, args=(
            message,), kwargs={'file': stream})
        thread.daemon = True
        thread.start()
        pos = 0
        while (thread.is_alive()):
            stream.seek(pos)
            r = stream.read()
            pos += len(r)
            yield r
