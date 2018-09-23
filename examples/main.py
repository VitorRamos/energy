import pandas as pd
import numpy as np
import os

from energyOptimal import plotData
from energyOptimal.powerModel import powerModel
from energyOptimal.performanceModel import performanceModel
from energyOptimal.energyModel import energyModel
from energyOptimal.monitor import monitorProcess

parsecapps=['completo_black_3.pkl','completo_canneal_2.pkl','completo_dedup_3.pkl',
                    'completo_ferret_3.pkl','completo_fluid_2.pkl','completo_freq.pkl',
                    'completo_rtview_2.pkl','completo_swaptions_1.pkl','completo_vips_3.pkl',
                    'completo_x264_3.pkl','completo_xhpl.pkl','completo_openmc_kernel_novo.pkl']
parsecapps_argnum= [1, 4, 6, 0, 1, 1, 7, 3, 1, 23, 1, 0]
warg= 0

def energy_pics():
    titles=['Blackscholes','Canneal','Dedup', 'Ferret','Fluidanimate','Freqmine',
                    'Raytrace','Swaptions','Vips',
                    'x264','HPL','Openmc']
    for app, title in zip(parsecapps,titles):
        pw_model= powerModel('data/ipmi_2-32_cpuload.pw')
        perf_model= performanceModel('data/dataframes/'+app, 'data/svr/'+app)
        en_model= energyModel(pw_model,perf_model,freq_range_=np.arange(1.2e6,2.3e6,0.1e6)/1e6)

        plotData.setProps(xlabel='Frequencies (GHz)', ylabel='Active threads',
                            zlabel='Energy (KJ)', title=title)
        df_= perf_model.dataFrame[perf_model.dataFrame['in_cat']==5].sort_values(['freq','thr'])
        df_pred_= en_model.dataFrame[en_model.dataFrame['in']==5].sort_values(['freq','thr'])

        df_= df_[df_['thr']!=1]
        plotData.plot3D(x=df_['freq'].unique(),y=df_['thr'].unique(),
                        z=df_['energy'].values/1e3,points=True,legend='Measurements')

        plotData.plot3D(x=df_pred_['freq'].unique(),y=df_pred_['thr'].unique(),
                        z=df_pred_['energy'].values/1e3,points=False,legend='Model')
        plotData.ax.view_init(30,60)
        plotData.savePlot('fotos/'+app+'.png',showLegend=True)

parsecapps=['completo_black_3.pkl','completo_canneal_2.pkl','completo_dedup_3.pkl',
                    'completo_ferret_3.pkl','completo_fluid_2.pkl','completo_freq.pkl',
                    'completo_rtview_2.pkl','completo_swaptions_1.pkl','completo_vips_3.pkl',
                    'completo_x264_3.pkl']
parsecapps_argnum= [1, 4, 6, 0, 1, 1, 7, 3, 1, 23]

for app in parsecapps:
    pw_model= powerModel('data/ipmi_2-32_cpuload.pw')
    perf_model= performanceModel('data/dataframes/'+app, 'data/svr/'+app)
    en_model= energyModel(pw_model,perf_model,freq_range_=np.arange(1.2e6,2.3e6,0.1e6)/1e6)
    df1= perf_model.dataFrame[['in_cat','freq','thr','energy']]
    df1.columns= ['in','freq','thr','energy_x']
    df2= en_model.minimalEnergy()[['in','freq','thr','energy']]
    df2.columns= ['in','freq','thr','energy_y']
    df= pd.merge(df1,df2)
    df=df.sort_values(['in','freq','thr'])
    print(app)
    print(df['energy_x'].sum()/1e3)