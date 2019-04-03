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
                                method='constTime')

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



def createReducedPerformanceModel(path, arg_num, title_='', save_df='', save_svr=''):
    perf_model= performanceModel()
    perf_model.loadData(filename=path, arg_num=int(arg_num))
    
    cats= perf_model.dataFrame['in_cat'].unique()[-5:]
    perf_model.dataFrame= perf_model.dataFrame[perf_model.dataFrame['in_cat'].isin(cats)]
    perf_model.dataFrame= perf_model.dataFrame[perf_model.dataFrame['freq']!=2.3]

    if 'fluid' in path:
        perf_model.dataFrame= perf_model.dataFrame[perf_model.dataFrame['thr'].isin([1,2,4,8,16,32])]
    if 'x264' in path:
        perf_model.dataFrame['in_cat']= 6-perf_model.dataFrame['in_cat']

    df_ori= perf_model.dataFrame.sort_values(['freq','thr','in_cat']).copy()
    
    x=[]
    y_time=[]
    y_en=[]
    less_5= 0
    for train_sz in range(0, perf_model.dataFrame.shape[0], 100)[1:]:
        # print("Program", path)
        aux= perf_model.fit(C_=10e3,gamma_=0.1,train_size_=train_sz,dataframe=True)
        aux= pd.merge(aux[['freq','thr','in_cat']],df_ori)

        perf_model.estimate(df_ori[['freq','thr','in_cat']],dataframe=True).sort_values(['freq','thr','in_cat'])
        x.append(train_sz)
        y_time.append(perf_model.error()*100)
        y_en.append( aux['energy'].sum()/1e6 )
        # print(y_en[-1])
        # print( x[-1], y_time[-1] )
        if y_time[-1] <= 6 and less_5 == 0:
            less_5= y_time[-1]
            print('%s_%i.pkl'%(title_,train_sz))
            perf_model.saveDataframe('data/dataframes/%s_%i.pkl'%(title_,train_sz))
            perf_model.saveSVR('data/svr/%s_%i.pkl'%(title_,train_sz))
            break
        # scores= perf_model.crossValidate(method='mpe')
        # print("CrossValidation ", np.mean(scores)*100, scores)
    
    fig, ax1 = plt.subplots()
    ax1.plot(x,y_time)
    # ax1.plot([min(x),max(x)],[less_5, less_5],'-')
    ax1.set_ylabel('Mean error (%)')

    ax2 = ax1.twinx()
    ax2.plot(x,y_en)
    ax2.set_ylabel('Energy (KJ)')

    plt.xlabel('Train size')
    plt.title(title_)
    plt.savefig('fotos/over/%s.png'%title_)
    # plt.show()


def mean_df():
    def avg_ondemand(onds, arg):
        ond= dvfsModel()
        ond.loadData(filename= 'data/dvfs/ondemand/'+onds[0], arg_num= arg, method='constTime')
        df= ond.dataFrame
        for f in onds[1:]:
            ond.loadData(filename= 'data/dvfs/ondemand/'+onds[0], arg_num= arg, method='constTime')
            df['energy']+= ond.dataFrame['energy']
        df['energy']/=len(onds)
        return df

    ondemand= avg_ondemand(['ferret_completo_2.pkl','ferret_completo_3.pkl'],6)
    pw_model= powerModel('data/ipmi_2-32_cpuload.pw')
    perf_model= performanceModel('data/dataframes/'+'completo_ferret_3.pkl', 'data/svr/'+'completo_ferret_3.pkl')
    en_model= energyModel(pw_model,perf_model)

    ond= ondemand[['in','thr','time','energy']].sort_values(['in','thr'])
    nthreads= ond['thr'].unique().shape[0]
    ond= pd.crosstab(ond['in'], ond['thr'], ond['energy'],aggfunc=min)
    df= en_model.realMinimalEnergy().sort_values('in_cat')['energy']
    df= pd.concat([df]*nthreads,axis=1)
    ond= pd.DataFrame(ond.values/df.values,columns=ond.columns)

    ond.plot.bar()
    plt.plot([-1,6],[1,1], '--',color='k',label='proposto')
    plt.title('Ferret')
    plt.tight_layout()
    plt.savefig('fotos/comp2/ferret.png')


def createReducedPerformanceModel2(path, arg_num, title_='', save_df='', save_svr=''):
    perf_model= performanceModel()
    perf_model.loadData(filename=path, arg_num=int(arg_num))

    cats= perf_model.dataFrame['in_cat'].unique()[-5:]
    perf_model.dataFrame= perf_model.dataFrame[perf_model.dataFrame['in_cat'].isin(cats)]
    perf_model.dataFrame= perf_model.dataFrame[perf_model.dataFrame['freq']<2.3]

    if 'fluid' in path:
        perf_model.dataFrame= perf_model.dataFrame[perf_model.dataFrame['thr'].isin([1,2,4,8,16,32])]
    if 'x264' in path:
        perf_model.dataFrame['in_cat']= 6-perf_model.dataFrame['in_cat']
    df_ori= perf_model.dataFrame.sort_values(['freq','thr','in_cat']).copy()

    ori= perf_model.dataFrame.copy()
    freqs= perf_model.dataFrame['freq'].unique()
    x= []
    y_time= []
    y_en= []
    for f in range(1,len(freqs),1):
        use_freq= list(freqs[:int(f)])+list(freqs[-int(f):])
        perf_model.dataFrame= perf_model.dataFrame[perf_model.dataFrame['freq'].isin(use_freq)]
        # print(perf_model.dataFrame['freq'].unique())
        
        aux= perf_model.fit(C_=10e3,gamma_=0.1,train_size_=0.9,dataframe=True)
        aux= pd.merge(aux[['freq','thr','in_cat']],df_ori)
        perf_model.dataFrame= ori.copy()

        df_est= perf_model.estimate(df_ori[['freq','thr','in_cat']],dataframe=True).sort_values(['freq','thr','in_cat'])
        error= sum( (abs(df_est['time']-df_ori['time']))/df_ori['time'] )/df_ori.shape[0]*100

        x.append(aux.shape[0])
        y_time.append(error)
        y_en.append(aux['energy'].sum()/1e6)
        # scores= perf_model.crossValidate(method='mpe')

        print('%s_%i.pkl'%(title_,f), aux.shape, aux['energy'].sum()/1e6, error, perf_model.error()*100)
        print(use_freq)

        perf_model.saveDataframe('data/dataframes/%s_%i.pkl'%(title_,f))
        perf_model.saveSVR('data/svr/%s_%i.pkl'%(title_,f))


    fig, ax1 = plt.subplots()
    ax1.plot(x,y_time)
    ax1.set_ylabel('Mean error (%)')

    ax2 = ax1.twinx()
    ax2.plot(x,y_en)
    ax2.set_ylabel('Energy (KJ)')

    plt.xlabel('Train size')
    plt.title(title_)
    plt.savefig('fotos/over/%s.png'%title_)
    # plt.show()

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

        plt.xlabel('Inputs',fontsize=18)
        plt.ylabel('Energy relative' if relative else 'Eenergy (J)',fontsize=18)
        plt.xticks(fontsize=18)
        plt.yticks(fontsize=18)
        plt.title(title,fontsize=22)
        plt.legend(loc='center right',bbox_to_anchor=(1.2,0.55),fontsize=12)
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
        df= pd.concat( (df,pd.DataFrame([['mean']+list(df.mean().values)],columns=df.columns)) )
        df.to_csv('tables/relative.csv')
        print(df)

titles=['Blackscholes','Canneal','Dedup',
        'Ferret','Fluidanimate','Freqmine',
        'Raytrace','Swaptions','Vips',
        'x264','HPL','Openmc',
        'Bodytrack']
# parsecapps=['completo_black_3.pkl','completo_canneal_2.pkl','completo_dedup_3.pkl',
#             'completo_ferret_3.pkl','completo_fluid_2.pkl','completo_freq.pkl',
#             'completo_rtview_2.pkl','completo_swaptions_1.pkl','completo_vips_3.pkl',
#             'completo_x264_3.pkl','completo_xhpl.pkl','completo_openmc_kernel_novo.pkl']
# parsec_models=['completo_black_5.pkl','completo_canneal_2.pkl','completo_dedup_3.pkl',
#                 'completo_ferret_3.pkl','completo_fluid_3.pkl','completo_freq.pkl',
#                 'completo_rtview_3.pkl','completo_swaptions_2.pkl','completo_vips_3.pkl',
#                 'completo_x264_3.pkl','completo_xhpl.pkl','completo_openmc_kernel_novo.pkl',
#                 'bodytrack_completo.pkl']
parsecapps=['completo_black_5.pkl','completo_canneal_2.pkl','completo_dedup_3.pkl',
            'completo_ferret_3.pkl','completo_fluid_3.pkl','completo_freqmine_1.pkl',
            'completo_rtview_3.pkl','completo_swaptions_2.pkl','completo_vips_3.pkl',
            'completo_x264_3.pkl','completo_xhpl.pkl','completo_openmc_kernel_novo.pkl',
            'completo_bodytrack_1.pkl']
parsec_models=['Blackscholes_2.pkl', 'Canneal_2.pkl', 'Dedup_2.pkl',
                'Ferret_2.pkl', 'Fluidanimate_2.pkl', 'Freqmine_2.pkl',
                'Raytrace_2.pkl', 'Swaptions_2.pkl', 'Vips_2.pkl',
                'x264_2.pkl', 'HPL_2.pkl', 'Openmc_3.pkl',
                'Bodytrack_2.pkl']
# parsec_models= parsecapps
parsec_dvfs=['blackscholes_completo_3.pkl', 'canneal_completo_3.pkl', 'dedup_completo_3.pkl',
             'ferret_completo_3.pkl', 'fluidanimate_completo_3.pkl', 'freqmine_completo_5.pkl',
             'rtview_completo_3.pkl', 'swaptions_completo_3.pkl', 'vips_completo_3.pkl',
             'x264_completo_3.pkl', 'xhpl_completo_3.pkl', 'openmc_completo_2.pkl',
             'bodytrack_completo_5.pkl']
parsecapps_argnum= [1, 4, 6, 
                    0, 1, 0,
                    7, 3, 1,
                    23, 1, 0,
                    2]
# energy_figures(parsecapps[0])
# createPerformanceModels(parsecapps[-1])
# comparation(appname='dedup',proposed_bar=False,relative=True,thrs_filter=[])
# figures(energy=False, in_cmp=3)
comparation(appname="", proposed_bar=False,relative=True)
# for app,arg,title in zip(parsecapps,parsecapps_argnum,titles):
#     if not 'freq' in app:
#         continue
#     createReducedPerformanceModel2('data/performance_model/%s'%app,arg,title_=title)