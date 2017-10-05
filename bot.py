from flask import Flask, request, make_response
import json
import os
import requests
import telebot
from telebot import types
from config import *

server = Flask(__name__)
bot = telebot.TeleBot(API_TOKEN)
TELEGRAM_FILE_URL = "https://api.telegram.org/file/bot{token}/".format(token=API_TOKEN) + "{file_path}"

def google_url_shorten(url):
   req_url = 'https://www.googleapis.com/urlshortener/v1/url?key=' + GOOGLE_URL_SHORTEN_API
   payload = {'longUrl': url}
   headers = {'content-type': 'application/json'}
   r = requests.post(req_url, data=json.dumps(payload), headers=headers)
   resp = json.loads(r.text)
   return resp['id']

@bot.message_handler(content_types=['document'])
def get_link(message):
    if (message.document.file_size > 20 * 1024 * 1024):
        bot.reply_to(message, "This file is too big. Max file size is 20MB")
        return

    try:
        url = TELEGRAM_FILE_URL.format(file_path=bot.get_file(message.document.file_id).file_path)
        bot.reply_to(message, google_url_shorten(url))
    except Exception as e:
        bot.reply_to(message, url)


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
