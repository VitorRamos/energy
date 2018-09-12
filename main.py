import pandas as pd
import numpy as np
import os

from energyOptimal import plotData, powerModel, performanceModel, energyModel

parsecapps=['completo_black_3.pkl','completo_canneal_2.pkl','completo_dedup_3.pkl',
                    'completo_ferret_3.pkl','completo_fluid_2.pkl','completo_freq.pkl',
                    'completo_rtview_2.pkl','completo_swaptions_1.pkl','completo_vips_3.pkl',
                    'completo_x264_3.pkl','completo_xhpl.pkl','completo_openmc_kernel_novo.pkl']
parsecapps_argnum= [1, 4, 6, 0, 1, 1, 7, 3, 1, 23, 1, 0]
warg= 10

def createPowerModel():
    pw_model= powerModel()
    pw_model.loadData(filename='data/power_model/ipmi_2-32_cpuload.pkl',verbose=0,load_sensors=False,
                        freqs_filter=np.arange(1200000,2300000,100000))
    pw_model.fit()
    pw_model.save('ipmi_2-32_cpuload.pw')
    error= pw_model.error()
    print("Power model constants, ", pw_model.power_model_x)
    print("Erro, ", error)
    est= pw_model.estimate(pw_model.frequencies, pw_model.threads)

    # Plot the measured values and the model
    plotData.setProps(xlabel= "Frequencies (GHz)", ylabel= "Active Cores", zlabel= "Power (W)")
    plotData.plot3D(x=pw_model.frequencies, y=pw_model.threads, z=pw_model.powers, legend='Measurements')
    plotData.plot3D(x=pw_model.frequencies, y=pw_model.threads, z=est, points=False, legend='Model')
    plotData.savePlot(filename= 'pw_model.png', showLegend= True)
    plotData.plotShow(showLegend= True)

def createPerformanceModels():
    for l,idx in zip(parsecapps,parsecapps_argnum):
        if l.endswith('pkl') and 'swap' in l:
            en_model= performanceModel()
            df= en_model.loadData(filename='data/performance_model/'+l, arg_num=idx, verbose=0,
                                                    createDataFrame=True, method='constTime',
                                                    freqs_filter=np.arange(1200000,2300000,100000))

            if 'fluid' in l:
                en_model.dataFrame= en_model.dataFrame[en_model.dataFrame['thr'].isin([1,2,4,8,16,32])]

            if len(df['in_cat']) > 5: #limit to 5 inputs
                cats= en_model.dataFrame['in_cat'].unique()[-5:]
                en_model.dataFrame= en_model.dataFrame[en_model.dataFrame['in_cat'].isin(cats)]
            print(l)
            print(df.head(5))
            en_model.fit(C_=10e3,gamma_=0.1)
            print("MPE ", en_model.error(method='mpe')*100)
            print("MAE ", en_model.error(method='mae'))
            scores= en_model.crossValidate(method='mpe')
            print("CrossValidation ", np.mean(scores)*100, scores)
            en_model.saveDataframe('data/dataframes/'+l)
            en_model.saveSVR('data/svr/'+l)

def visualizePeformanceModels():
    en_model= performanceModel()
    df= en_model.loadDataFrame('data/dataframes/'+parsecapps[warg])
    en_model.loadSVR('data/svr/'+parsecapps[warg])

    df = df.sort_values(['freq', 'thr'])
    df_pred= df[['freq', 'thr', 'in_cat', 'in']].copy()
    df_pred['time']= en_model.estimate(df[['freq', 'thr', 'in_cat']].values).copy()

    def update_data(val):
        d = int(val)
        plotData.setProps(xlabel='Frequencies (GHz)', ylabel='Active threads', 
                            zlabel='Time (S)', title=parsecapps[warg])
        df_= df[df['in_cat']==d]
        df_pred_= df_pred[df_pred['in_cat']==d]
        plotData.plot3D(x=df_['freq'].unique(),y=df_['thr'].unique(),
                                            z=df_['time'].values)
        plotData.plot3D(x=df_pred_['freq'].unique(),y=df_pred_['thr'].unique(),
                                            z=df_pred_['time'].values,points=False)
    plotData.update_user= update_data
    plotData.createSlider(label_='in', valmin_=df['in_cat'].min(), valmax_=df['in_cat'].max())

    plotData.plotShow()

def energyModels():
    pw_model= powerModel('data/ipmi_2-32_cpuload.pw')
    perf_model= performanceModel('data/dataframes/'+parsecapps[warg], 'data/svr/'+parsecapps[warg])
    en_model= energyModel(pw_model,perf_model)#,
                        #thr_range_= np.hstack(([1],np.arange(2,33,2))),
                        #freq_range_= np.arange(1.2e6,2.3e6,0.1e6)/1e6)
    df= perf_model.dataFrame.sort_values(['freq','thr'])
    df_pred= en_model.dataFrame.sort_values(['freq','thr'])

    print(en_model.minimalEnergy())

    def update_data(val):
        d= int(val)
        plotData.setProps(xlabel='Frequencies (GHz)', ylabel='Active threads',
                            zlabel='Time (s)', title=parsecapps[warg])
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


# createPowerModel()
# createPerformanceModels()
# visualizePeformanceModels()
# energyModels()
# energy_pics()