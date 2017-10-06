from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.messages import GetMessagesRequest
from telethon.tl.types import (InputPeerChat, PeerChat)
from config import *

client = TelegramClient('tg_client', CLIENT_API_ID, CLIENT_API_HASH)
client.connect()
if (not client.is_user_authorized()):
    client.sign_in(CLIENT_PHONE)
    try:
        client.sign_in(code=input('Enter code: '))
    except SessionPasswordNeededError:
        client.sign_in(password=CLIENT_2FA_PASSWORD)


def get_download_link(message_id):
    chat = client.get_entity(PeerChat(-1*int(CHANNEL_REPLY_ID)))
    messages = client.get_message_history(chat, limit=10)
    message = None
    for each in messages[1]:
        if (each.id == message_id):
            message = each
            break
    client.download_media(message)

