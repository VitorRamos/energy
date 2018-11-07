from pypapi import papi_low as papi
from pypapi import events
import subprocess, os, signal
import numpy as np
import time

papi.library_init()
total=[]
cont= 0

for i in range(100):
    try:
        evs= papi.create_eventset()
        papi.add_event(evs, events.PAPI_TOT_INS)
        papi.add_event(evs, events.PAPI_BR_INS)
        papi.add_event(evs, events.PAPI_BR_MSP)
        papi.add_event(evs, events.PAPI_L3_TCR)

        p= subprocess.Popen(['./teste'], stdout= subprocess.PIPE)
        os.kill(p.pid, signal.SIGSTOP)
        papi.attach(evs, p.pid)
        papi.start(evs)
        os.kill(p.pid, signal.SIGCONT)
        p.wait()
        result= papi.stop(evs)
        total.append(result)
        cont+=1
        papi.cleanup_eventset(evs)
        papi.destroy_eventset(evs)
        # print("Not Too fast", i)
        # print(result)
    except Exception as e:
        print("Too fast", cont)
        print(e)
        pass

print(cont)
total= np.asarray(total)
print(total.mean(axis=0))
print(total.std(axis=0))

