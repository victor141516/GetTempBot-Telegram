from flask import (
    Flask,
    request,
    make_response,
    Response,
    stream_with_context
)
import os
import requests
import telebot
from telebot import types
import threading

from config import *
from DbHandler import DbHandler
from security import *
import tg_client

db = DbHandler(DB_URL)
server = Flask(__name__)
bot = telebot.TeleBot(API_TOKEN, threaded=True)
big_files = {}
TELEGRAM_FILE_URL = "https://api.telegram.org/file/bot{token}/".format(
    token=API_TOKEN) + "{file_path}"


def google_url_shorten(url):
    try:
        req_url = "https://www.googleapis.com/urlshortener/v1/url?key={api_key}".format(
            api_key=GOOGLE_URL_SHORTEN_API)
        r = requests.post(req_url, json={'longUrl': url}, headers={
                            'content-type': 'application/json'})
        return r.json()['id']
    except Exception:
        return url


@bot.message_handler(content_types=['document'])
def get_link(message):
    replied_msg = bot.forward_message(
        CHANNEL_REPLY_ID, message.chat.id, message.message_id)

    if (message.chat.id in big_files):
        big_files[message.chat.id].append({
            'file_size': message.document.file_size,
            'message_id': replied_msg.message_id
        })
        return bot.reply_to(message,
                            'Gotcha! Send more files or `/end filename` to end',
                            parse_mode='Markdown')
    else:
        hash_d = encode(replied_msg.message_id, API_TOKEN)
        db.insert('links', {
            'hash': hash_d,
            'file_name': message.document.file_name,
            'file_size': message.document.file_size,
            'message_id': [replied_msg.message_id]
        })
        url = WEBHOOK_URL + '/d?id={hash}'.format(hash=hash_d)
        return bot.reply_to(message, google_url_shorten(url))


@bot.message_handler(commands=['big'])
def begin_big(message):
    big_files[message.chat.id] = []
    return bot.reply_to(message, 'You can now send as much files as you want, they will be downloaded together as one single file (beware order!!)')


@bot.message_handler(commands=['end'])
def end_big(message):
    files = big_files[message.chat.id]
    size = 0
    message_ids = []

    for each_file in files:
        size += each_file['file_size']
        message_ids.append(each_file['message_id'])

    hash_d = encode(files[0]['message_id'], API_TOKEN)
    db.insert('links', {
        'hash': hash_d,
        'file_name': message.text.split('/end')[1][1:],
        'file_size': size,
        'message_id': message_ids
    })
    url = WEBHOOK_URL + '/d?id={hash}'.format(hash=hash_d)
    return bot.reply_to(message, google_url_shorten(url))


@server.route("/bot", methods=['POST'])
def getMessage():
    bot.process_new_updates(
        [telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200


@server.route("/d")
def serve_file():
    file_hash = request.args.get('id', default=0, type=str)
    link = db.select('links', 'hash = \'{hash}\''. format(hash=file_hash))

    if (link is False or len(link) == 0):
        return "File not found"
    else:
        link = link[0]

    stream = stream_with_context(tg_client.get_file_stream(link['message_id']))
    return Response(stream,
                    headers={
                        'Content-Type': 'application/octet-stream',
                        'Content-Length': link['file_size'],
                        'Content-Disposition': 'attachment; filename="{file_name}"'.format(file_name=link['file_name'])
                    }
                    )


@server.route("/")
def webhook():
    webhook = bot.get_webhook_info()
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL + "/bot")
    return "!", 200


if (POLLING):
    bot.remove_webhook()
    thread = threading.Thread(target=bot.polling)
    thread.daemon = True
    thread.start()


server.run(host="0.0.0.0", port=os.environ.get('PORT', 5000))
