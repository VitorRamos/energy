from energyOptimal import plotData
from energyOptimal.powerModel import powerModel
from energyOptimal.performanceModel import performanceModel
from energyOptimal.energyModel import energyModel
import numpy as np
import pandas as pd

program= 'completo_black_3.pkl'

pw_model= powerModel('data/ipmi_2-32_cpuload.pw')
perf_model= performanceModel('data/dataframes/'+program, 'data/svr/'+program)
en_model= energyModel(pw_model,perf_model,
                    thr_range_= np.hstack(([1],np.arange(2,33,2))),
                    freq_range_= np.arange(1.2e6,2.3e6,0.1e6)/1e6)
df= perf_model.dataFrame.sort_values(['freq','thr'])
df_pred= en_model.dataFrame.sort_values(['freq','thr'])

print(en_model.minimalEnergy())

def update_data(val):
    d= int(val)
    plotData.setProps(xlabel='Frequencies (GHz)', ylabel='Active threads',
                        zlabel='Time (s)', title=program)
    df_pred_= df_pred[df_pred['in']==d]
    df_= df[df['in_cat']==d]
    if not df_.empty:
        plotData.plot3D(x=df_['freq'].unique(),y=df_['thr'].unique(),
                                        z=df_['time'].values/1e3,points=True,legend='Measurements')
    plotData.plot3D(x=df_pred_['freq'].unique(),y=df_pred_['thr'].unique(),
                                        z=df_pred_['time'].values/1e3,points=False,legend='Model')
plotData.update_user= update_data
plotData.createSlider(label_='in',valmin_=df_pred['in'].min(),valmax_=df_pred['in'].max())
plotData.plotShow(showLegend=True)
