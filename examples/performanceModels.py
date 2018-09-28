from energyOptimal.performanceModel import performanceModel
from energyOptimal import plotData
import numpy as np

def createPerformanceModels(appname=None):
    for p,idx in zip(parsecapps,parsecapps_argnum):
        if appname and not appname in p:
            continue
        en_model= performanceModel()
        df= en_model.loadData(filename='data/performance_model/'+p, arg_num=idx, verbose=0,
                                                createDataFrame=True, method='constTime',
                                                freqs_filter=list(range(1200000,2300000,100000)))

        if 'fluid' in p:
            en_model.dataFrame= en_model.dataFrame[en_model.dataFrame['thr'].isin([1,2,4,8,16,32])]
        if 'x264' in p:
            en_model.dataFrame['in_cat']= 6-en_model.dataFrame['in_cat']

        if len(df['in_cat']) > 5: #limit to 5 inputs
            cats= en_model.dataFrame['in_cat'].unique()[-5:]
            en_model.dataFrame= en_model.dataFrame[en_model.dataFrame['in_cat'].isin(cats)]
        print("Program", p)
        print(df.head(5))
        en_model.fit(C_=10e3,gamma_=0.1)
        print("MPE ", en_model.error(method='mpe')*100)
        print("MAE ", en_model.error(method='mae'))
        scores= en_model.crossValidate(method='mpe')
        print("CrossValidation ", np.mean(scores)*100, scores)
        en_model.saveDataframe('data/dataframes/'+p)
        en_model.saveSVR('data/svr/'+p)

def visualizePeformanceModels(program, title_):
    en_model= performanceModel()
    df= en_model.loadDataFrame('data/dataframes/'+program)
    en_model.loadSVR('data/svr/'+program)

    df = df.sort_values(['freq', 'thr'])
    df_pred= df[['freq', 'thr', 'in_cat', 'in']].copy()
    df_pred['time']= en_model.estimate(df[['freq', 'thr', 'in_cat']].values).copy()

    def update_data(val):
        d = int(val)
        plotData.setProps(xlabel='Frequencies (GHz)', ylabel='Active threads', 
                            zlabel='Time (S)', title=title_)
        df_= df[df['in_cat']==d]
        df_pred_= df_pred[df_pred['in_cat']==d]

        df_pred_= df_pred_[df_pred_['thr'].isin(list(range(8,33,2)))]
        df_= df_[df_['thr'].isin(list(range(8,33,2)))]

        plotData.plot3D(x=df_['freq'].unique(),y=df_['thr'].unique(),
                                            z=df_['time'].values)
        plotData.plot3D(x=df_pred_['freq'].unique(),y=df_pred_['thr'].unique(),
                                            z=df_pred_['time'].values,points=False)
    plotData.update_user= update_data
    plotData.createSlider(label_='in', valmin_=df['in_cat'].min(), valmax_=df['in_cat'].max())

    plotData.ax.view_init(30,60)
    plotData.plotShow()

import sys
n= int(sys.argv[1])

titles=['Blackscholes','Canneal','Dedup', 'Ferret','Fluidanimate','Freqmine',
                    'Raytrace','Swaptions','Vips',
                    'x264','HPL','Openmc']
parsecapps=['completo_black_3.pkl','completo_canneal_2.pkl','completo_dedup_3.pkl',
                    'completo_ferret_3.pkl','completo_fluid_2.pkl','completo_freq.pkl',
                    'completo_rtview_3.pkl','completo_swaptions_2.pkl','completo_vips_3.pkl',
                    'completo_x264_1.pkl','completo_xhpl.pkl','completo_openmc_kernel_novo.pkl']
parsecapps_argnum= [1, 4, 6, 0, 1, 1, 7, 3, 1, 23, 1, 0]

# createPerformanceModels(parsecapps[n])
visualizePeformanceModels(parsecapps[n], titles[n])