import json
from pprint import pprint

import requests
from telegram import Update, Bot
from telegram.ext import CommandHandler
from haruka.modules.helper_funcs.chat_status import user_admin

from haruka import dispatcher

# Open API key
API_KEY = "6ae0c3a0-afdc-4532-a810-82ded0054236"
URL = "http://services.gingersoftware.com/Ginger/correct/json/GingerTheText"

def translate(bot: Bot, update: Update):
    if update.effective_message.reply_to_message:
        msg = update.effective_message.reply_to_message

        params = dict(
            lang="US",
            clientVersion="2.0",
            apiKey=API_KEY,
            text=msg.text
        )

        res = requests.get(URL, params=params)
        # print(res)
        # print(res.text)
        pprint(json.loads(res.text))
        changes = json.loads(res.text).get('LightGingerTheTextResult')
        curr_string = ""

        prev_end = 0

        for change in changes:
            start = change.get('From')
            end = change.get('To') + 1
            suggestions = change.get('Suggestions')
            if suggestions:
                sugg_str = suggestions[0].get('Text')  # should look at this list more
                curr_string += msg.text[prev_end:start] + sugg_str

                prev_end = end

        curr_string += msg.text[prev_end:]
        print(curr_string)
        update.effective_message.reply_text(curr_string)

__help__ = """
 - /afk <reason>: mark yourself as AFK(Away From Keyboard)
 - brb <reason>: same as the afk command
 - /spell: while replying to a message, will reply with a grammar corrected version(ENGLISH ONLY)
 - /forbesify: Correct your punctuations better use the advanged spell module 
 - /tr (language code) as reply to a long message.
 - /define <text>: Type the word or expression you want to search\nFor example /define Gay
 - /banme: ban yourself from a chat
 - /kickme: kicks yourself from a chat
 - /markdownhelp: quick summary of how markdown works in telegram - can only be called in private chats
 - /smsbomb {country code without +} {phone no}: Take revenge upon your enemy by sending bulk messages 
"""

__mod_name__ = "Helpers 🤗"


TRANSLATE_HANDLER = CommandHandler('spell', translate)

dispatcher.add_handler(TRANSLATE_HANDLER)
