from telethon import events
import subprocess
from telethon.errors import MessageEmptyError, MessageTooLongError, MessageNotModifiedError
import io
import asyncio
import time
from haruka.events import register
import glob
import os
import instantmusic, subprocess

@register(pattern="^/song (.*)")
async def _(event):
    if event.fwd_from:
        return
    cmd = event.pattern_match.group(1)
    reply_to_id = event.message.id
    if event.reply_to_msg_id:
        reply_to_id = event.reply_to_msg_id
    subprocess.check_output(["instantmusic", "-q", "-s", cmd])
    subprocess.check_output('for f in *.webm; do      mv -- "$f" "${f%.webm}.mp3"; done && for f in *.m4a; do      mv -- "$f" "${f%.m4a}.mp3"; done && for f in *.wav; do      mv -- "$f" "${f%.wav}.mp3"; done', shell=True)
    l = glob.glob("*.mp3")
    loa = l[0]
    await event.reply("sending the song")
    await event.client.send_file(
                event.chat_id,
                loa,
                force_document=True,
                allow_cache=False,
                caption=cmd,
                reply_to=reply_to_id
            )
    subprocess.Popen("rm -rf *.mp3", shell=True)

__help__ = """
 - /song <name>: search download and return a song in the best format
"""
__mod_name__ = "Songs" 
