from flask import Flask, request, make_response
import os
import requests
import telebot
from telebot import types
from config import *

server = Flask(__name__)
bot = telebot.TeleBot(API_TOKEN)
TELEGRAM_FILE_URL = "https://api.telegram.org/file/bot{token}/".format(token=API_TOKEN) + "{file_path}"

def google_url_shorten(url):
   req_url = "https://www.googleapis.com/urlshortener/v1/url?key={api_key}".format(api_key=GOOGLE_URL_SHORTEN_API)
   r = requests.post(req_url, json={'longUrl': url}, headers={'content-type': 'application/json'})
   return r.json()['id']

@bot.message_handler(content_types=['text', 'audio', 'document', 'photo', 'sticker', 'video', 'video_note', 'voice', 'location', 'contact', 'new_chat_members', 'left_chat_member', 'new_chat_title', 'new_chat_photo', 'delete_chat_photo', 'group_chat_created', 'supergroup_chat_created', 'channel_chat_created', 'migrate_to_chat_id', 'migrate_from_chat_id', 'pinned_message'])
def get_link(message):
    # Get message whatever type it is
    document = message.__getattribute__(message.content_type)[1] if type(message.__getattribute__(message.content_type)) is type([]) else message.__getattribute__(message.content_type)

    # Check if it has file_id (some types doesn't so them can't be linked)
    if (not hasattr(document, 'file_id')):
        bot.reply_to(message, "That content can't be linked")
        return

    # Try to generate the link. It may fail because file size mainly, but may there be other reasons
    try:
        url = TELEGRAM_FILE_URL.format(file_path=bot.get_file(document.file_id).file_path)
    except Exception as e:
        error_message = str(e).split('"description":"')[1].split('"')[0]
        if (error_message == "Bad Request: file is too big"):
            bot.reply_to(message, "This file is too big. Max file size is 20MB")
        else:
            bot.reply_to(message, error_message[0].upper() + error_message[1:])
        return

    # Try to short the link. May fail due Google policies
    try:
        bot.reply_to(message, google_url_shorten(url))
    except Exception as e:
        bot.reply_to(message, url)
        return


@server.route("/bot", methods=['POST'])
def getMessage():
    bot.process_new_updates(
        [telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200


@server.route("/")
def webhook():
    webhook = bot.get_webhook_info()
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL + "/bot")
    return "!", 200


if (POLLING):
    bot.remove_webhook()
    bot.polling()
else:
    server.run(host="0.0.0.0", port=os.environ.get('PORT', 5000))
