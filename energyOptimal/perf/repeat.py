import subprocess
import numpy as np
import pandas as pd
import sys

def run_all(bench, prog):
    m= []
    print(bench, prog)
    for i in range(100):
        sys.stdout.write('.')
        sys.stdout.flush()
        data= subprocess.Popen([bench,prog],stdout=subprocess.PIPE).stdout.readlines()
        n= []
        names= []
        for c in data[1:]:
            aux= str(c)
            names.append(str(aux.split(':')[0]))
            n.append(int(str(aux.split(':')[1])[:-3]))
        m.append(n)
    df= pd.DataFrame(m, columns=names)
    print()
    print(df.mean())
    print(df.std())

run_all('./event_perf', 'teste')
run_all('./papi_perf', 'teste')