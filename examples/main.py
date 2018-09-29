from energyOptimal import plotData
from energyOptimal.powerModel import powerModel
from energyOptimal.performanceModel import performanceModel
from energyOptimal.energyModel import energyModel
from energyOptimal.monitor import monitorProcess

import pandas as pd
import numpy as np
import os


def createPerformanceModels(appname=None):
    for p,idx in zip(parsecapps,parsecapps_argnum):
        if appname and not appname in p:
            continue
        perf_model= performanceModel()
        df= perf_model.loadData(filename='data/performance_model/'+p, arg_num=idx, verbose=0,
                                method='constTime', freqs_filter=list(range(1200000,2300000,100000)))

        if 'fluid' in p:
            perf_model.dataFrame= perf_model.dataFrame[perf_model.dataFrame['thr'].isin([1,2,4,8,16,32])]
        if 'x264' in p:
            perf_model.dataFrame['in_cat']= 6-perf_model.dataFrame['in_cat']

        if len(df['in_cat']) > 5: #limit to 5 inputs
            cats= perf_model.dataFrame['in_cat'].unique()[-5:]
            perf_model.dataFrame= perf_model.dataFrame[perf_model.dataFrame['in_cat'].isin(cats)]
        print("Program", p)
        print(df.head(5))
        perf_model.fit(C_=10e3,gamma_=0.1)
        print("MPE ", perf_model.error(method='mpe')*100)
        print("MAE ", perf_model.error(method='mae'))
        scores= perf_model.crossValidate(method='mpe')
        print("CrossValidation ", np.mean(scores)*100, scores)
        perf_model.saveDataframe('data/dataframes/'+p)
        perf_model.saveSVR('data/svr/'+p)


def energy_figures(appname=None):
    for app, title in zip(parsecapps,titles):
        if appname and not appname in app:
            continue
        pw_model= powerModel('data/ipmi_2-32_cpuload.pw')
        perf_model= performanceModel('data/dataframes/'+app, 'data/svr/'+app)
        en_model= energyModel(pw_model,perf_model,freq_range_=np.arange(1.2e6,2.3e6,0.1e6)/1e6)

        plotData.setProps(xlabel='Frequencies (GHz)', ylabel='Active threads',
                            zlabel='Energy (kJ)', title=title)
        df_= perf_model.dataFrame[perf_model.dataFrame['in_cat']==5].sort_values(['freq','thr'])
        df_pred_= en_model.dataFrame[en_model.dataFrame['in_cat']==5].sort_values(['freq','thr'])

        df_pred_= df_pred_[df_pred_['thr'].isin(list(range(8,33,2)))]
        df_= df_[df_['thr'].isin(list(range(8,33,2)))]
        plotData.plot3D(x=df_['freq'].unique(),y=df_['thr'].unique(),
                        z=df_['energy'].values/1e3,points=True,legend='Measurements')

        plotData.plot3D(x=df_pred_['freq'].unique(),y=df_pred_['thr'].unique(),
                        z=df_pred_['energy_model'].values/1e3,points=False,legend='Model')
        plotData.ax.view_init(30,60)
        plotData.savePlot('fotos/'+app+'.png',showLegend=True)


titles=['Blackscholes','Canneal','Dedup',
        'Ferret','Fluidanimate','Freqmine',
        'Raytrace','Swaptions','Vips',
        'x264','HPL','Openmc']
parsecapps=['completo_black_3.pkl','completo_canneal_2.pkl','completo_dedup_3.pkl',
            'completo_ferret_3.pkl','completo_fluid_2.pkl','completo_freq.pkl',
            'completo_rtview_2.pkl','completo_swaptions_1.pkl','completo_vips_3.pkl',
            'completo_x264_3.pkl','completo_xhpl.pkl','completo_openmc_kernel_novo.pkl']
parsecapps_argnum= [1, 4, 6, 0, 1, 1, 7, 3, 1, 23, 1, 0]

# energy_figures(parsecapps[0])
# createPerformanceModels(parsecapps[0])