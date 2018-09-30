from energyOptimal.dvfsModel import dvfsModel
from energyOptimal.powerModel import powerModel
from energyOptimal.performanceModel import performanceModel
from energyOptimal.energyModel import energyModel

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

plt.style.use('seaborn')

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


def createPerformanceModel(path, arg_num, title_='', save_df='', save_svr=''):
    perf_model= performanceModel()
    perf_model.loadData(filename=path, arg_num=int(arg_num))#, freqs_filter=get_range(args.freqs),
                                                            # thrs_filter= get_range(args.thrs))
    #perf_model.dataFrame= perf_model.dataFrame[perf_model.dataFrame['in_cat'].isin(get_range(args.ins))]
    
    cats= perf_model.dataFrame['in_cat'].unique()[-5:]
    perf_model.dataFrame= perf_model.dataFrame[perf_model.dataFrame['in_cat'].isin(cats)]
    perf_model.dataFrame= perf_model.dataFrame[perf_model.dataFrame['freq']!=2.3]

    if 'fluid' in path:
        perf_model.dataFrame= perf_model.dataFrame[perf_model.dataFrame['thr'].isin([1,2,4,8,16,32])]
    if 'x264' in path:
        perf_model.dataFrame['in_cat']= 6-perf_model.dataFrame['in_cat']

    df_ori= perf_model.dataFrame.sort_values(['freq','thr','in_cat']).copy()
    
    # print("Program", path)
    # perf_model.fit(C_=10e3,gamma_=0.1,train_size_=0.9)
    # df_est= perf_model.estimate(df_ori[['freq','thr','in_cat']],dataframe=True).sort_values(['freq','thr','in_cat'])
    # print( sum(( abs(df_est['time']-df_ori['time']) )/df_ori['time'])/df_ori.shape[0]*100 )
    
    # perf_model.dataFrame= perf_model.dataFrame[perf_model.dataFrame['freq'].isin([2.2,1.8,1.4,1.2])]
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
            print('%s_%i.pkl'%(title,train_sz))
            perf_model.saveDataframe('data/dataframes/%s_%i.pkl'%(title,train_sz))
            perf_model.saveSVR('data/svr/%s_%i.pkl'%(title,train_sz))
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
    plt.savefig('fotos/over/%s.png'%title)
    # plt.show()

def createPerformanceModel2(path, arg_num, title_='', save_df='', save_svr=''):
    perf_model= performanceModel()
    perf_model.loadData(filename=path, arg_num=int(arg_num))#, freqs_filter=get_range(args.freqs),
                                                            # thrs_filter= get_range(args.thrs))
    #perf_model.dataFrame= perf_model.dataFrame[perf_model.dataFrame['in_cat'].isin(get_range(args.ins))]
    
    cats= perf_model.dataFrame['in_cat'].unique()[-5:]
    perf_model.dataFrame= perf_model.dataFrame[perf_model.dataFrame['in_cat'].isin(cats)]
    perf_model.dataFrame= perf_model.dataFrame[perf_model.dataFrame['freq']!=2.3]

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
        error= sum( (abs(df_est['time']-df_ori['time']))/df_ori['time'] )/df_ori.shape[0]

        x.append(aux.shape[0])
        y_time.append(error)
        y_en.append(aux['energy'].sum()/1e6)
        # scores= perf_model.crossValidate(method='mpe')

        print('%s_%i.pkl'%(title,f), aux.shape, aux['energy'].sum()/1e6, error*100, perf_model.error()*100)
        # print(use_freq)

        perf_model.saveDataframe('data/dataframes/%s_%i.pkl'%(title,f))
        perf_model.saveSVR('data/svr/%s_%i.pkl'%(title,f))


    fig, ax1 = plt.subplots()
    ax1.plot(x,y_time)
    ax1.set_ylabel('Mean error (%)')

    ax2 = ax1.twinx()
    ax2.plot(x,y_en)
    ax2.set_ylabel('Energy (KJ)')

    plt.xlabel('Train size')
    plt.title(title_)
    plt.savefig('fotos/over/%s.png'%title)
    # plt.show()

parsecapps=['completo_black_5.pkl','completo_canneal_2.pkl','completo_dedup_3.pkl',
                'completo_ferret_3.pkl','completo_fluid_3.pkl','completo_freq.pkl',
                'completo_rtview_3.pkl','completo_swaptions_2.pkl','completo_vips_3.pkl',
                'completo_x264_3.pkl','completo_xhpl.pkl','completo_openmc_kernel_novo.pkl']
titles=['Blackscholes','Canneal','Dedup',
        'Ferret','Fluidanimate','Freqmine',
        'Raytrace','Swaptions','Vips',
        'x264','HPL','Openmc']
parsecapps_argnum= [1, 4, 6, 0, 1, 1, 7, 3, 1, 23, 1, 0]
for app,arg,title in zip(parsecapps,parsecapps_argnum,titles):
    createPerformanceModel2('data/performance_model/%s'%app,arg,title_=title)