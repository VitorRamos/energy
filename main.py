import pandas as pd
import numpy as np
import os

from energyOptimal import plotData, powerModel, performanceModel, energyModel
from energyOptimal import monitorProcess

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



def monitor_all():
    args_black=\
    [\
        ["__nt__","in_5_10.txt","output.txt"],\
        ["__nt__","in_6_10.txt","output.txt"],\
        ["__nt__","in_7_10.txt","output.txt"],\
        ["__nt__","in_8_10.txt","output.txt"],\
        ["__nt__","in_9_10.txt","output.txt"]
    ]
    args_canneal=\
    [\
        ["__nt__","15000","2000","2500000.nets","128"],\
        ["__nt__","15000","2000","2500000.nets","256"],\
        ["__nt__","15000","2000","2500000.nets","384"],\
        ["__nt__","15000","2000","2500000.nets","512"],\
        ["__nt__","15000","2000","2500000.nets","640"]
    ]
    args_dedup=\
    [\
        ["-c","-p","-v","-t","__nt__","-i","FC-6-x86_64-disc1_05.iso","-o","output.dat.ddp"],\
        ["-c","-p","-v","-t","__nt__","-i","FC-6-x86_64-disc1_06.iso","-o","output.dat.ddp"],\
        ["-c","-p","-v","-t","__nt__","-i","FC-6-x86_64-disc1_07.iso","-o","output.dat.ddp"],\
        ["-c","-p","-v","-t","__nt__","-i","FC-6-x86_64-disc1_08.iso","-o","output.dat.ddp"],\
        ["-c","-p","-v","-t","__nt__","-i","FC-6-x86_64-disc1_09.iso","-o","output.dat.ddp"]
    ]
    args_ferret=\
    [\
        ["corel_5","lsh","queries_5","10","20","__nt__","output.txt"],\
        ["corel_6","lsh","queries_6","10","20","__nt__","output.txt"],\
        ["corel_7","lsh","queries_7","10","20","__nt__","output.txt"],\
        ["corel_8","lsh","queries_8","10","20","__nt__","output.txt"],\
        ["corel_9","lsh","queries_9","10","20","__nt__","output.txt"]
    ]
    args_fluid=\
    [\
        ["__nt__","200","in_500K.fluid","out.fluid"],\
        ["__nt__","300","in_500K.fluid","out.fluid"],\
        ["__nt__","400","in_500K.fluid","out.fluid"],\
        ["__nt__","500","in_500K.fluid","out.fluid"],\
        ["__nt__","600","in_500K.fluid","out.fluid"]
    ]
    args_freq=\
    [\
        ["webdocs_250k_05.dat","1100"],\
        ["webdocs_250k_06.dat","1100"],\
        ["webdocs_250k_07.dat","1100"],\
        ["webdocs_250k_08.dat","1100"],\
        ["webdocs_250k_09.dat","1100"]
    ]
    args_rtview=\
    [\
        ["thai_statue.obj","-automove","-nthreads","__nt__","-frames","10000","-res","100","100"],\
        ["thai_statue.obj","-automove","-nthreads","__nt__","-frames","10000","-res","200","200"],\
        ["thai_statue.obj","-automove","-nthreads","__nt__","-frames","10000","-res","300","300"],\
        ["thai_statue.obj","-automove","-nthreads","__nt__","-frames","10000","-res","400","400"],\
        ["thai_statue.obj","-automove","-nthreads","__nt__","-frames","10000","-res","500","500"]
    ]
    args_swap=\
    [\
        ["-ns","32","-sm","2000000","-nt","__nt__"],\
        ["-ns","32","-sm","3000000","-nt","__nt__"],\
        ["-ns","32","-sm","4000000","-nt","__nt__"],\
        ["-ns","32","-sm","5000000","-nt","__nt__"],\
        ["-ns","32","-sm","6000000","-nt","__nt__"]
    ]
    args_vips=\
    [\
        ["im_benchmark","orion_10800x10800.v","output.v"],\
        ["im_benchmark","orion_12600x12600.v","output.v"],\
        ["im_benchmark","orion_14400x14400.v","output.v"],\
        ["im_benchmark","orion_16200x16200.v","output.v"],\
        ["im_benchmark","orion_18000x18000.v","output.v"]
    ]
    args_x264=\
    [\
        ["--quiet","--qp","20","--partitions","b8x8,i4x4","--ref","5","--direct","auto","--b-pyramid","--weightb","--mixed-refs","--no-fast-pskip","--me","umh","--subme","7","--analyse","b8x8,i4x4","--threads","__nt__","-o","eledream.264","eledream_1920x1080_512.y4m"],\
        ["--quiet","--qp","20","--partitions","b8x8,i4x4","--ref","5","--direct","auto","--b-pyramid","--weightb","--mixed-refs","--no-fast-pskip","--me","umh","--subme","7","--analyse","b8x8,i4x4","--threads","__nt__","-o","eledream.264","eledream_1920x1080_459.y4m"],\
        ["--quiet","--qp","20","--partitions","b8x8,i4x4","--ref","5","--direct","auto","--b-pyramid","--weightb","--mixed-refs","--no-fast-pskip","--me","umh","--subme","7","--analyse","b8x8,i4x4","--threads","__nt__","-o","eledream.264","eledream_1920x1080_408.y4m"],\
        ["--quiet","--qp","20","--partitions","b8x8,i4x4","--ref","5","--direct","auto","--b-pyramid","--weightb","--mixed-refs","--no-fast-pskip","--me","umh","--subme","7","--analyse","b8x8,i4x4","--threads","__nt__","-o","eledream.264","eledream_1920x1080_357.y4m"],\
        ["--quiet","--qp","20","--partitions","b8x8,i4x4","--ref","5","--direct","auto","--b-pyramid","--weightb","--mixed-refs","--no-fast-pskip","--me","umh","--subme","7","--analyse","b8x8,i4x4","--threads","__nt__","-o","eledream.264","eledream_1920x1080_306.y4m"]
    ]
    args_xhpl= [['_nt_','7000'],\
            ['_nt_','8000'],\
            ['_nt_','9000'],\
            ['_nt_','10000'],\
            ['_nt_','11000'],\
    ]
    args_openmc= [['input1'],\
            ['input2'],\
            ['input3'],\
            ['input4'],\
            ['input5']
    ]
    
    programs= [monitorProcess(program_name_= 'openmc', sensor_type_='ipmi'),
               monitorProcess(program_name_= 'xhpl.sh', sensor_type_='ipmi'),
               monitorProcess(program_name_= 'canneal', sensor_type_='ipmi'),
               monitorProcess(program_name_= 'dedup', sensor_type_='ipmi'),
               monitorProcess(program_name_= 'ferret', sensor_type_='ipmi'),
               monitorProcess(program_name_= 'x264', sensor_type_='ipmi'),
               monitorProcess(program_name_= 'vips', sensor_type_='ipmi'),
               monitorProcess(program_name_= 'blackscholes', sensor_type_='ipmi'),
               monitorProcess(program_name_= 'fluidanimate', sensor_type_='ipmi'),
               monitorProcess(program_name_= 'swaptions', sensor_type_='ipmi'),
               monitorProcess(program_name_= 'rtview', sensor_type_='ipmi'),
               monitorProcess(program_name_= 'freqmine', sensor_type_='ipmi')]
    args= [args_openmc, args_xhpl, args_canneal, args_dedup,
            args_ferret, args_x264, args_vips, args_black, args_fluid, args_swap, args_rtview, args_freq]
    for p, a in zip(programs,args):
        try:
            if 'fluid' in p.program_name:
                thr= [1,2,4,8,16,32]
            else:
                thr= [1]+list(range(2,33,2))
            p.run_dvfs(list_threads= thr, list_args= a, idle_time= 30,
                        verbose=0, save_name='data/dvfs/{}_completo_2.pkl'.format(p.program_name))
        except Exception as e:
            print(e)

# createPowerModel()
# createPerformanceModels()
# visualizePeformanceModels()
# energyModels()
# energy_pics()
monitor_all()