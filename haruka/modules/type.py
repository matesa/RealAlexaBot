import random
import re
import asyncio
import time
from cowpy import cow
from haruka.events import register
import html
import random
import time
from typing import List
from telegram import Bot, Update, ParseMode
from telegram.ext import run_async
from haruka import dispatcher
from haruka.modules.helper_funcs.chat_status import is_user_admin, user_admin
from haruka.modules.helper_funcs.extraction import extract_user
from haruka import LOGGER, tbot
from telethon import types
from telethon.tl import functions

async def is_register_admin(chat, user):
    if isinstance(chat, (types.InputPeerChannel, types.InputChannel)):

        return isinstance(
            (await tbot(functions.channels.GetParticipantRequest(chat, user))).participant,
            (types.ChannelParticipantAdmin, types.ChannelParticipantCreator)
        )
    elif isinstance(chat, types.InputPeerChat):

        ui = await tbot.get_peer_id(user)
        ps = (await tbot(functions.messages.GetFullChatRequest(chat.chat_id))) \
            .full_chat.participants.participants
        return isinstance(
            next((p for p in ps if p.user_id == ui), None),
            (types.ChatParticipantAdmin, types.ChatParticipantCreator)
        )
    else:
        return None

@register(pattern="^/type (.*)")
async def typewriter(typew):
    if typew.is_group:
       if not (await is_register_admin(typew.input_chat, typew.message.sender_id)):
          return

    message = typew.pattern_match.group(1)
    if message:
        pass
    else:
        await typew.reply("`Give a text to type!`")
        return
    typing_symbol = "|"
    old_text = ''
    now = await typew.reply(typing_symbol)
    await asyncio.sleep(2)
    for character in message:
        old_text = old_text + "" + character
        typing_text = old_text + "" + typing_symbol
        await now.edit(typing_text)
        await asyncio.sleep(2)
        await now.edit(old_text)
        await asyncio.sleep(2)


__help__ = """
 - /type <text>: Make the bot type something for you in a professional way
"""
__mod_name__ = "Typewriter"
