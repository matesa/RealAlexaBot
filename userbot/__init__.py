# Copyright (C) 2019 The Raphielscape Company LLC.
#
# Licensed under the Raphielscape Public License, Version 1.d (the "License");
# you may not use this file except in compliance with the License.
#
""" Userbot initialization. """

import os
from distutils.util import strtobool as sb
from logging import DEBUG, INFO, basicConfig, getLogger
from sys import version_info

from dotenv import load_dotenv
from pyDownload import Downloader
from pylast import LastFMNetwork, md5
from pymongo import MongoClient
from redis import StrictRedis
from telethon import TelegramClient
from telethon.sessions import StringSession

# Bot Logs setup:
CONSOLE_LOGGER_VERBOSE = sb(os.environ.get("CONSOLE_LOGGER_VERBOSE", "True"))

if CONSOLE_LOGGER_VERBOSE:
    basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=DEBUG,
    )
else:
    basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                level=INFO)
LOGS = getLogger(__name__)

if version_info[0] < 3 or version_info[1] < 6:
    LOGS.error("You MUST have a python version of at least 3.6."
               " Multiple features depend on this. Halting!")
    quit(1)


API_KEY = os.environ.get("API_KEY") or None
if not API_KEY:
    LOGS.error("API Key is not set! Check your config.env. Halting!")
    quit(1)

API_HASH = os.environ.get("API_HASH") or None
if not API_HASH:
    LOGS.error("API Hash is not set! Check your config.env. Halting!")
    quit(1)

STRING_SESSION = os.environ.get("STRING_SESSION") or None

BOTLOG = (os.environ.get("BOTLOG") == 'True')

BOTLOG_CHATID = int(os.environ.get("BOTLOG_CHATID")) if BOTLOG else 0

# pylint: disable=invalid-name
if STRING_SESSION:
    ubot = TelegramClient(StringSession(STRING_SESSION), API_KEY, API_HASH)
else:
    ubot = TelegramClient("userbot", API_KEY, API_HASH)


async def check_botlog_chatid():
    if not BOTLOG:
        return

    entity = await ubot.get_entity(BOTLOG_CHATID)
    if entity.default_banned_rights.send_messages:
        LOGS.error(
            "Your account doesn't have rights to send messages to BOTLOG_CHATID "
            "group. Check if you typed the Chat ID correctly. Halting!")
        quit(1)


with ubot:
    try:
        ubot.loop.run_until_complete(check_botlog_chatid())
    except:
        LOGS.error("BOTLOG_CHATID environment variable isn't a "
                   "valid entity. Check your config.env file. Halting!")
        quit(1)


# Download binaries for gen_direct_links module, give correct perms
if not os.path.exists('bin'):
    os.mkdir('bin')

url1 = 'https://raw.githubusercontent.com/yshalsager/megadown/master/megadown'
url2 = 'https://raw.githubusercontent.com/yshalsager/cmrudl.py/master/cmrudl.py'

dl1 = Downloader(url=url1, filename="bin/megadown")
dl1 = Downloader(url=url1, filename="bin/cmrudl")

os.chmod('bin/megadown', 0o755)
os.chmod('bin/cmrudl', 0o755)
