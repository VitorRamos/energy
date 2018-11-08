from energyOptimal.monitor import monitorProcess
from energyOptimal.cpufreq import cpuFreq

try:
    p= monitorProcess(program_name_= 'programs/cpu_load', sensor_type_='rapl')
    try:
        p.run(list_threads= [1,2,3,4], list_args= [['__nt__','10']],
                    idle_time= 5,  verbose=2,  save_name='data/power_phd.pkl')
    except Exception as e:
        print(e)
except KeyboardInterrupt:
    cpu= cpuFreq()
    cpu.reset()
