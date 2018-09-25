from energyOptimal.dvfsModel import dvfsModel
from energyOptimal.powerModel import powerModel
from energyOptimal.performanceModel import performanceModel
from energyOptimal.energyModel import energyModel
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt


parsec_models=['completo_black_5.pkl','completo_canneal_2.pkl','completo_dedup_3.pkl',
                    'completo_ferret_3.pkl','completo_fluid_2.pkl','completo_freq.pkl',
                    'completo_rtview_3.pkl','completo_swaptions_2.pkl','completo_vips_3.pkl',
                    'completo_x264_3.pkl','completo_xhpl.pkl','completo_openmc_kernel_novo.pkl']

parsec_dvfs=['blackscholes_completo_3.pkl', 'canneal_completo_3.pkl', 'dedup_completo_3.pkl',
             'ferret_completo_3.pkl', 'fluidanimate_completo_3.pkl', 'freqmine_completo_3.pkl',
             'rtview_completo_3.pkl', 'swaptions_completo_3.pkl', 'vips_completo_3.pkl',
             'x264_completo_3.pkl', 'xhpl_completo_3.pkl', 'openmc_completo_3.pkl']

parsecapps_argnum= [1, 4, 6, 0, 1, 1, 7, 3, 1, 23, 1, 0]
wapp= 0
plt.style.use('seaborn')

row= []
for dvfs, model, arg in zip(parsec_dvfs,parsec_models,parsecapps_argnum):
    if 'freq' in model:
        continue
    ondemand= dvfsModel()
    ondemand.loadData(filename= 'data/dvfs/ondemand/'+dvfs, arg_num= arg, method='constTime')
    pw_model= powerModel('data/ipmi_2-32_cpuload.pw')
    perf_model= performanceModel('data/dataframes/'+model, 'data/svr/'+model)
    en_model= energyModel(pw_model,perf_model)#,
                        #thr_range_= np.hstack(([1],np.arange(2,33,2))),
                        #freq_range_= np.arange(1.2e6,2.3e6,0.1e6)/1e6)

    df= ondemand.dataFrame
    df= df[df['thr'] == 32]
    df= df[['in','time','energy']]
    df.columns= ['in','time_ondemand','energy_ondemand']
    df= pd.merge(df, perf_model.dataFrame[['in','in_cat','freq','thr','energy','time']])
    df= df[['in_cat','freq','thr','energy','energy_ondemand','time','time_ondemand']]
    df.columns= ['in','freq','thr','energy_real','energy_ondemand','time','time_ondemand']
    df2= en_model.minimalEnergy()[['in','freq','thr','energy']]
    df2.columns= ['in','freq','thr','energy_model']
    df= pd.merge(df,df2)
    df=df.sort_values(['in','freq','thr'])

    # df= df[['in','energy_ondemand','energy_real']]
    # df=df.set_index('in')
    # df.plot.bar(width=0.8)
    # plt.xlabel('Inputs')
    # plt.ylabel('Energy (J)')
    # plt.title(dvfs)
    # plt.tight_layout()
    # print('fotos/comp'+dvfs+'.png')
    # plt.savefig('fotos/comp/'+dvfs+'.png')

    # x3= pd.crosstab(df['in'],df['thr'],values=df['energy_real'],aggfunc=min)
    # print(x3)
    # plot_side_by_side_comp(df_model= en_model.dataFrame, df_ondemand= df_ond, thrs=[32], title=dvfs)
    # plt.show()
    df['saving_energy']= (df['energy_real']-df['energy_ondemand'])/df['energy_ondemand']*100
    df['saving_time']= (df['time']-df['time_ondemand'])/df['time_ondemand']*100

    print(model)
    print(df.mean()['saving_energy'], df.mean()['saving_time'])
    row.append([model.split('_')[1], df.energy_real.sum(), df.energy_ondemand.sum(), df.time.sum(), df.time_ondemand.sum(),
    perf_model.dataFrame.energy.sum()])
    print( (df.energy_real.sum()-df.energy_ondemand.sum())/df.energy_ondemand.sum()*100 )

# df= pd.DataFrame(row,columns=['Program','Energy(J)','Ondemand(J)', 'Time(s)', 'Ondemand(s)', 'Total_train'])
# df['Energy_saving']= (df['Energy(J)']-df['Ondemand(J)'])/df['Ondemand(J)']*100
# df['Time_saving']= (df['Time(s)']-df['Ondemand(s)'])/df['Ondemand(s)']*100
# df['Start_comp']= -df['Total_train']/(df['Energy_saving']/100.0*df['Energy(J)'])
# df= df.sort_values('Energy_saving')
# df.to_csv('table.csv')
# print(df)
# print(df['Energy_saving'].mean(), df['Start_comp'].mean())