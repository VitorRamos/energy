from pypapi import papi_low as papi
from pypapi import events
import subprocess, os, signal

papi.library_init()
evs= papi.create_eventset()
papi.add_event(evs, events.PAPI_TOT_INS)

p= subprocess.Popen(['./teste'])
os.kill(p.pid, signal.SIGSTOP)
papi.attach(evs, p.pid)
os.kill(p.pid, signal.SIGCONT)

papi.start(evs)
p.wait()
result= papi.stop(evs)
print(result)

papi.cleanup_eventset(evs)
papi.destroy_eventset(evs)