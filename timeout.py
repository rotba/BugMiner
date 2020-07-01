import multiprocessing
from subprocess import Popen
import time
import sys


timeout = int(sys.argv[1])
frame = int(sys.argv[2])
p = Popen(sys.argv[3:])

passed = 0
while passed < timeout:
	time.sleep(frame)
	passed += frame
	poll = p.poll()
	if poll is not None:
		break
poll = p.poll()
if poll is None:
	p.terminate()
p.wait()
