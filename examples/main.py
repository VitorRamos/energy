from energyOptimal.powerModel import powerModel
from energyOptimal.performanceModel import performanceModel
from energyOptimal.energyModel import energyModel
from energyOptimal.monitor import monitorProcess
from energyOptimal.dvfsModel import dvfsModel

from matplotlib import pyplot as plt
import pandas as pd
import numpy as np
import os

# plt.style.use('seaborn')

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

        perf_model.fit(C_=10e3,gamma_=0.1)
        scores= perf_model.crossValidate(method='mpe')
        perf_model.saveDataframe('data/dataframes/'+p)
        perf_model.saveSVR('data/svr/'+p)

        print("Program", p)
        print(df.head(5))
        print("MPE ", perf_model.error(method='mpe')*100)
        print("MAE ", perf_model.error(method='mae'))
        print("CrossValidation ", np.mean(scores)*100, scores)


def figures(appname=None, energy= True, in_cmp=3):
    from energyOptimal import plotData
    for app, title in zip(parsec_models,titles):
        if (appname and not appname in app) or (not app):
            continue
        pw_model= powerModel('data/ipmi_2-32_cpuload.pw')
        perf_model= performanceModel('data/dataframes/'+app, 'data/svr/'+app)
        en_model= energyModel(pw_model,perf_model,freq_range_=np.arange(1.2e6,2.3e6,0.1e6)/1e6)

        plotData.setProps(xlabel='Frequencies (GHz)', ylabel='Active threads',
                            zlabel='Energy (kJ)' if energy else 'Time (s)', title=title)
        df_= perf_model.dataFrame[perf_model.dataFrame['in_cat']==in_cmp].sort_values(['freq','thr'])
        df_pred_= en_model.dataFrame[en_model.dataFrame['in_cat']==in_cmp].sort_values(['freq','thr'])

        # df_pred_= df_pred_[df_pred_['thr'].isin(list(range(8,33,2)))]
        # df_= df_[df_['thr'].isin(list(range(8,33,2)))]
        plotData.plot3D(x=df_['freq'].unique(),y=df_['thr'].unique(),
                        z=df_['energy'].values/1e3 if energy else df_['time'].values,
                        points=True,legend='Measurements')

        plotData.plot3D(x=df_pred_['freq'].unique(),y=df_pred_['thr'].unique(),
                        z=df_pred_['energy_model'].values/1e3 if energy else df_pred_['time'].values,
                        points=False,legend='Model')
        plotData.ax.view_init(30,60)
        if 'HPL' in app:
            plotData.ax.set_zlim(0,15)
        aux= 'energy' if energy else 'time'
        plotData.savePlot('fotos/{}/{}.png'.format(aux, app),showLegend=True)
    
def comparation(appname=None, proposed_bar=False, relative=True, thrs_filter= []):
    row=[]
    for title, dvfs, model, arg in zip(titles,parsec_dvfs,parsec_models,parsecapps_argnum):
        if 'freq' in model or not model:
            continue
        if appname and not appname in dvfs:
            continue
        ondemand= dvfsModel()
        ondemand.loadData(filename= 'data/dvfs/ondemand/'+dvfs, arg_num= arg, method='constTime')
        pw_model= powerModel('data/ipmi_2-32_cpuload.pw')
        perf_model= performanceModel('data/dataframes/'+model, 'data/svr/'+model)
        en_model= energyModel(pw_model,perf_model)

        #TODO verify if arguments match
        
        ond= ondemand.dataFrame[['in','thr','time','energy']]
        ond= pd.merge(ond,perf_model.dataFrame[['in','in_cat']]).drop_duplicates().sort_values(['in_cat','thr'])
        if thrs_filter:
            ond= ond[ond['thr'].isin(thrs_filter)]
        ond_en= pd.crosstab(ond['in_cat'], ond['thr'], ond['energy'],aggfunc=min)
        ond_time= pd.crosstab(ond['in_cat'], ond['thr'], ond['time'],aggfunc=min)
        min_df= en_model.realMinimalEnergy().sort_values('in_cat')
        
        if proposed_bar:
            ond_en['proposed']= min_df['energy'].values
            ond_time['proposed']= min_df['time'].values
        if relative:
            aux= pd.concat([min_df['energy']]*(len(ond_en.columns)),axis=1)
            saving= pd.DataFrame(ond_en.values-aux.values,columns=ond_en.columns)
            ond_en= pd.DataFrame(ond_en.values/aux.values,columns=ond_en.columns)
            aux= pd.concat([min_df['time']]*(len(ond_en.columns)),axis=1)
            ond_time= pd.DataFrame(ond_time.values/aux.values,columns=ond_time.columns)

            row.append([dvfs, ond_en.max(axis=1).mean(), ond_en.mean(axis=1).mean(), ond_en[32].mean(), ond_en.min(axis=1).mean(), 
                    ond_time.max(axis=1).mean(), ond_time.mean(axis=1).mean(), ond_time[32].mean(), ond_time.min(axis=1).mean(),
                    saving.max(axis=1).sum(), saving.median(axis=1).sum(), saving[32].sum(), saving.min(axis=1).sum(),
                    perf_model.dataFrame.energy.sum()])
        
        ond_en.plot.bar(figsize=(12,7))
        if relative:
            plt.plot([-1,6],[1,1], '--',color='k',label='proposed')
            plt.plot([-1,6],[ond_en.mean().mean(),ond_en.mean().mean()], ':',color='k',label='average gain')
        plt.xlabel('Inputs')
        plt.ylabel('Energy relative' if relative else 'Eenergy (J)')
        plt.title(title)
        plt.legend(loc='center right',bbox_to_anchor=(1.15,0.6))
        plt.tight_layout()
        plt.savefig('fotos/relative/%s.png'%dvfs)
        # plt.show()

    if relative and not proposed_bar:
        df= pd.DataFrame(row,columns=['app','max_en','mean_en','32_en','min_en',
                                            'max_time','mean_time','32_time','min_time',
                                            'max_save','median_save','32_save','min_save', 'train_energy'])
        df[['max_en','mean_en','32_en','min_en',
            'max_time','mean_time','32_time','min_time']]-=1
        df[['max_en','mean_en','32_en','min_en',
            'max_time','mean_time','32_time','min_time']]*=100
        df['max_run']= df['train_energy']/df['max_save']
        df['median_run']= df['train_energy']/df['median_save']
        df['32_run']= df['train_energy']/df['32_save']
        df['min_run']= df['train_energy']/df['min_save']

        df= df.sort_values('32_en',ascending=False)
        df= pd.concat( (df,pd.DataFrame([['mean']+list(df[df>0].mean().values)],columns=df.columns)) )
        df.to_csv('tables/relative.csv')
        print(df)

titles=['Blackscholes','Canneal','Dedup',
        'Ferret','Fluidanimate','Freqmine',
        'Raytrace','Swaptions','Vips',
        'x264','HPL','Openmc']
parsecapps=['completo_black_3.pkl','completo_canneal_2.pkl','completo_dedup_3.pkl',
            'completo_ferret_3.pkl','completo_fluid_2.pkl','completo_freq.pkl',
            'completo_rtview_2.pkl','completo_swaptions_1.pkl','completo_vips_3.pkl',
            'completo_x264_3.pkl','completo_xhpl.pkl','completo_openmc_kernel_novo.pkl']
parsec_models=['completo_black_5.pkl','completo_canneal_2.pkl','completo_dedup_3.pkl',
                'completo_ferret_3.pkl','completo_fluid_3.pkl','completo_freq.pkl',
                'completo_rtview_3.pkl','completo_swaptions_2.pkl','completo_vips_3.pkl',
                'completo_x264_3.pkl','completo_xhpl.pkl','completo_openmc_kernel_novo.pkl']
parsec_models=['Blackscholes_2.pkl', 'Canneal_2.pkl', 'Dedup_2.pkl',
                'Ferret_2.pkl', 'Fluidanimate_2.pkl', '',
                'Raytrace_2.pkl', 'Swaptions_2.pkl', 'Vips_2.pkl',
                'x264_2.pkl', 'HPL_2.pkl', 'Openmc_3.pkl']
parsec_dvfs=['blackscholes_completo_3.pkl', 'canneal_completo_3.pkl', 'dedup_completo_3.pkl',
             'ferret_completo_3.pkl', 'fluidanimate_completo_3.pkl', 'freqmine_completo_3.pkl',
             'rtview_completo_3.pkl', 'swaptions_completo_3.pkl', 'vips_completo_3.pkl',
             'x264_completo_3.pkl', 'xhpl_completo_3.pkl', 'openmc_completo_2.pkl']
parsecapps_argnum= [1, 4, 6, 
                    0, 1, 1,
                    7, 3, 1,
                    23, 1, 0]

# energy_figures(parsecapps[0])
# createPerformanceModels(parsecapps[0])
# comparation(appname='',proposed_bar=False,relative=True,thrs_filter=[])
figures(energy=True, in_cmp=5)