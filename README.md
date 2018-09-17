# Energy 

## Table of contents

- [Description](#description)
- [Monitor script](#monitor)
- [Power Model](#power)
- [Performance Model](#performacne)
- [Energy Model](#energy)
- [Plot data](#plot3d)

<a name="description"/>

## Description

...

<a name="monitor"/>

## Monitor

Example monitor process 
```
from energyOptimal.monitor import monitorProcess
from energyOptimal.cpufreq import cpuFreq
try:
    process= monitorProcess(program_name_= 'example/program.elf', sensor_type_='ipmi')
    args= [['arg1','arg2'],['arg3','arg4'],...]
    thrs= [1]+list(range(2,33,2))
    process.run_dvfs(list_threads= thrs, list_args= args, idle_time= 30,
    verbose=2, save_name='dvfs/{}_complet.pkl'.format(p.program_name))
except KeyboardInterrupt:
    cpu= cpuFreq()
    cpu.reset()

```

<a name="power"/>

## Power Model

Example power model
```
from energyOptimal.powerModel import powerModel

pw_model= powerModel()
# Fit power model
pw_model.loadData(filename='power_model/ipmi_2-32_cpuload.pkl',verbose=0,load_sensors=False,
                    freqs_filter=np.arange(1200000,2300000,100000))
pw_model.fit()
pw_model.save('ipmi_2-32_cpuload.pw')
# Load power model
pw_model.load('ipmi_2-32_cpuload.pw')

error= pw_model.error()
print("Error, ", error)
print("Power model constants, ", pw_model.power_model_x)
res= pw_model.estimate(pw_model.frequencies, pw_model.threads)
```

<a name="performance"/>

## Performance Model

```
from energyOptimal.performanceModel import performanceModel

en_model= performanceModel()
# Fit model
df= en_model.loadData(filename='performance_model/program.pkl', arg_num=idx, verbose=0,
                                        createDataFrame=True, method='constTime',
                                        freqs_filter=np.arange(1200000,2300000,100000))
en_model.fit(C_=10e3,gamma_=0.1)
scores= en_model.crossValidate(method='mpe')
print("CrossValidation ", np.mean(scores)*100, scores)
en_model.saveDataframe('dataframes/program'+l)
en_model.saveSVR('svr/program'+l)

# Load model
df= en_model.loadDataFrame('dataframes/program')
en_model.loadSVR('svr/program')

# Predict
preds= en_model.estimate(df[['freq', 'thr', 'in_cat']].values)

```

<a name="energy"/>

## Energy Model

```
import numpy as np
from energyOptimal.energyModel import energyModel

pw_model= powerModel('data/ipmi_2-32_cpuload.pw')
perf_model= performanceModel('dataframes/program', 'svr/program')
en_model= energyModel(pw_model,perf_model,
                        thr_range_= np.hstack(([1],np.arange(2,33,2))),
                        freq_range_= np.arange(1.2e6,2.3e6,0.1e6)/1e6))

print(en_model.minimalEnergy())
```

<a name="plot3d"/>

## Plot data



### License

The entire suite is licensed under the GPL v3.0.