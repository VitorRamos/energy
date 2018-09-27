from energyOptimal.dvfsModel import dvfsModel
from energyOptimal.powerModel import powerModel
from energyOptimal.performanceModel import performanceModel
from energyOptimal.energyModel import energyModel
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt


parsec_models=['completo_black_5.pkl','completo_canneal_2.pkl','completo_dedup_3.pkl',
                    'completo_ferret_3.pkl','completo_fluid_3.pkl','completo_freq.pkl',
                    'completo_rtview_3.pkl','completo_swaptions_2.pkl','completo_vips_3.pkl',
                    'completo_x264_3.pkl','completo_xhpl.pkl','completo_openmc_kernel_novo.pkl']

parsec_dvfs=['blackscholes_completo_3.pkl', 'canneal_completo_3.pkl', 'dedup_completo_3.pkl',
             'ferret_completo_3.pkl', 'fluidanimate_completo_3.pkl', 'freqmine_completo_3.pkl',
             'rtview_completo_3.pkl', 'swaptions_completo_3.pkl', 'vips_completo_3.pkl',
             'x264_completo_3.pkl', 'xhpl_completo_3.pkl', 'openmc_completo_3.pkl']

parsecapps_argnum= [1, 4, 6, 0, 1, 1, 7, 3, 1, 23, 1, 0]
wapp= 0
plt.style.use('seaborn')

def ondemand32_comp():
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


        ond= ondemand.dataFrame[['in','thr','time','energy']].sort_values(['in','thr'])
        ond= pd.merge(ond,perf_model.dataFrame[['in','in_cat']]).drop_duplicates()
        ond= ond.rename(columns={'energy':'energy_ondemand','time':'time_ondemand'})
        ond= ond[ond['thr']==32]
        df= en_model.realMinimalEnergy()
        df= pd.merge(ond[['in_cat','energy_ondemand','time_ondemand']],df)
        df= df.rename(columns={'energy':'energy_real'})

        # df= ondemand.dataFrame
        # df= df[df['thr'] == 32][['in','time','energy']]
        # df.columns= ['in','time_ondemand','energy_ondemand']
        # df= pd.merge(df, perf_model.dataFrame[['in','in_cat','freq','thr','energy','time']])
        # df= df[['in_cat','freq','thr','energy','energy_ondemand','time','time_ondemand']]
        # df.columns= ['in_cat','freq','thr','energy_real','energy_ondemand','time','time_ondemand']
        # df1= en_model.minimalEnergy()[['in_cat','freq','thr','energy_model']]
        # df= pd.merge(df,df1)
        # df=df.sort_values(['in_cat','freq','thr'])
        df['saving_energy']= (df['energy_real']-df['energy_ondemand'])/df['energy_ondemand']*100
        df['saving_time']= (df['time']-df['time_ondemand'])/df['time_ondemand']*100
        # print(df)

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
        

        # print(model)
        # print(df.mean()['saving_energy'], df.mean()['saving_time'])
        row.append([model.split('_')[1], df.saving_energy.mean(), df.saving_time.mean(), perf_model.dataFrame.energy.sum()])

    df= pd.DataFrame(row,columns=['Program','Saving_mean', 'Saving_time', 'Total_train'])
    df= df.sort_values('Saving_mean')
    print(df)
    # df['Energy_saving']= (df['Energy(J)']-df['Ondemand(J)'])/df['Ondemand(J)']*100
    # df['Time_saving']= (df['Time(s)']-df['Ondemand(s)'])/df['Ondemand(s)']*100
    # df['Start_comp']= -df['Total_train']/(df['Energy_saving']/100.0*df['Energy(J)'])
    # df= df.sort_values('Energy_saving')
    df.to_csv('table.csv')
    # print(df)
    # print(df['Energy_saving'].mean(), df['Start_comp'].mean())

def relative_comp():
    for dvfs, model, arg in zip(parsec_dvfs,parsec_models,parsecapps_argnum):
        if 'freq' in model:
            continue
        ondemand= dvfsModel()
        ondemand.loadData(filename= 'data/dvfs/ondemand/'+dvfs, arg_num= arg, method='constTime')
        pw_model= powerModel('data/ipmi_2-32_cpuload.pw')
        perf_model= performanceModel('data/dataframes/'+model, 'data/svr/'+model)
        en_model= energyModel(pw_model,perf_model)

        ond= ondemand.dataFrame[['in','thr','time','energy']]
        ond= pd.merge(ond,perf_model.dataFrame[['in','in_cat']]).drop_duplicates().sort_values(['in_cat','thr'])
        nthreads= ond['thr'].unique().shape[0]
        ond= pd.crosstab(ond['in_cat'], ond['thr'], ond['energy'],aggfunc=min)
        df= en_model.realMinimalEnergy().sort_values('in_cat')['energy']
        df= pd.concat([df]*nthreads,axis=1)
        ond= pd.DataFrame(ond.values/df.values,columns=ond.columns)

        ond.plot.bar()
        plt.plot([-1,6],[1,1], '--',color='k',label='proposto')
        plt.title(dvfs)
        plt.tight_layout()
        plt.show()
        plt.savefig('fotos/comp2/%s.png'%dvfs)
        

ondemand32_comp()

# def avg_ondemand(onds, arg):
#     ond= dvfsModel()
#     ond.loadData(filename= 'data/dvfs/ondemand/'+onds[0], arg_num= arg, method='constTime')
#     df= ond.dataFrame
#     for f in onds[1:]:
#         ond.loadData(filename= 'data/dvfs/ondemand/'+onds[0], arg_num= arg, method='constTime')
#         df['energy']+= ond.dataFrame['energy']
#     df['energy']/=len(onds)
#     return df

# ondemand= avg_ondemand(['ferret_completo_2.pkl','ferret_completo_3.pkl'],6)
# pw_model= powerModel('data/ipmi_2-32_cpuload.pw')
# perf_model= performanceModel('data/dataframes/'+'completo_ferret_3.pkl', 'data/svr/'+'completo_ferret_3.pkl')
# en_model= energyModel(pw_model,perf_model)

# ond= ondemand[['in','thr','time','energy']].sort_values(['in','thr'])
# nthreads= ond['thr'].unique().shape[0]
# ond= pd.crosstab(ond['in'], ond['thr'], ond['energy'],aggfunc=min)
# df= en_model.realMinimalEnergy().sort_values('in_cat')['energy']
# df= pd.concat([df]*nthreads,axis=1)
# ond= pd.DataFrame(ond.values/df.values,columns=ond.columns)

# ond.plot.bar()
# plt.plot([-1,6],[1,1], '--',color='k',label='proposto')
# plt.title('Ferret')
# plt.tight_layout()
# plt.savefig('fotos/comp2/ferret.png')

