from asyncio import sleep
from random import choice, getrandbits, randint
import re
from re import sub
import random
from os import execl
import time
from telethon import events
from collections import deque
import requests
import sys
import os
import io
import html
import json
from PIL import ImageEnhance, ImageOps
from userbot.events import alexabot
from haruka import tbot, TEMP_DOWNLOAD_DIRECTORY
from haruka.events import register
BOTLOG_CHATID = os.environ.get("BOTLOG_CHATID")


EMOJI_PATTERN = re.compile(
    "["
    "\U0001F1E0-\U0001F1FF"  # flags (iOS)
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F680-\U0001F6FF"  # transport & map symbols
    "\U0001F700-\U0001F77F"  # alchemical symbols
    "\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
    "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
    "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
    "\U0001FA00-\U0001FA6F"  # Chess Symbols
    "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
    "\U00002702-\U000027B0"  # Dingbats 
    "]+")


def deEmojify(inputString: str) -> str:
    """Remove emojis and other non-safe characters from string"""
    return re.sub(EMOJI_PATTERN, '', inputString)


@register(pattern="^/waifu (.*)")
async def stickerizer(event):
    global newtext
    newtext = event.pattern_match.group(1)
    loader()
    print("sticker downloaded successfully")
    await event.client.send_file(animu.chat_id, store, reply_to=event.id)
    os.system(f'rm -rf {store}')

def loader():
  @alexabot(pattern="")
  async def waifu(animu):
    animus = [1, 3, 7, 9, 13, 22, 34, 35, 36, 37, 43, 44, 45, 52, 53, 55]
    sticcers = await animu.client.inline_query(
        "stickerizerbot", f"#{random.choice(animus)}{(deEmojify(newtext))}")
    local = await sticcers[0].click(BOTLOG_CHATID) # dump the shit there
    global store
    store = await animu.client.download_media(local, TEMP_DOWNLOAD_DIRECTORY)     
