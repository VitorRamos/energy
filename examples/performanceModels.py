from energyOptimal.performanceModel import performanceModel
from energyOptimal import plotData

import numpy as np
import argparse

# titles=['Blackscholes','Canneal','Dedup', 'Ferret','Fluidanimate','Freqmine',
#                     'Raytrace','Swaptions','Vips',
#                     'x264','HPL','Openmc']
# parsecapps=['completo_black_3.pkl','completo_canneal_2.pkl','completo_dedup_3.pkl',
#                     'completo_ferret_3.pkl','completo_fluid_2.pkl','completo_freq.pkl',
#                     'completo_rtview_3.pkl','completo_swaptions_2.pkl','completo_vips_3.pkl',
#                     'completo_x264_1.pkl','completo_xhpl.pkl','completo_openmc_kernel_novo.pkl']
# parsecapps_argnum= [1, 4, 6, 0, 1, 1, 7, 3, 1, 23, 1, 0]

parser= argparse.ArgumentParser(description='Create and visualize performance model from monitor data')
parser.add_argument('--create',type=str,help='Create performance model',nargs=4,metavar=('data','arg_num','dataframe','svr'))
parser.add_argument('--show',type=str,help='Show performance model',nargs=3,metavar=('dataframe','svr','title'))
parser.add_argument('--freqs',type=str,help='Frequency range', default='1.2,2.3,0.1',nargs='?')
parser.add_argument('--thrs',type=str,help='Threads range', default='',nargs='?')
parser.add_argument('--ins',type=str,help='Input range', default='',nargs='?')
args= parser.parse_args()

def get_range(str_range):
    _range=[]
    if not str_range:
        return _range
    for r in str_range.split(';'):
        sr= r.split(',')
        if len(sr) >= 2:
            start= float(sr[0])
            stop= float(sr[1])
            if len(sr) == 3:
                step= float(sr[2])
            else:
                step= 1.0
            _range+= list(np.arange(start,stop,step))
        elif len(sr) > 0:
            _range+= list([float(sr[0])])
    return _range

def createPerformanceModel(path, idx, save_df, save_svr):
    perf_model= performanceModel()
    perf_model.loadData(filename=path, arg_num=int(idx), verbose=0, method='constTime',
                            freqs_filter=get_range(args.freqs), thrs_filter= get_range(args.thrs))
    if args.ins:
        perf_model.dataFrame= perf_model.dataFrame[perf_model.dataFrame['in_cat'].isin(get_range(args.ins))]
    print("Program", path)
    print(perf_model.dataFrame.head(5))
    perf_model.fit(C_=10e3,gamma_=0.1)
    print("MPE ", perf_model.error(method='mpe')*100)
    print("MAE ", perf_model.error(method='mae'))
    scores= perf_model.crossValidate(method='mpe')
    print("CrossValidation ", np.mean(scores)*100, scores)
    perf_model.saveDataframe(save_df)
    perf_model.saveSVR(save_svr)

def visualizePeformanceModel(path_df, path_svr, title_):
    perf_model= performanceModel(path_df, path_svr)
    df= perf_model.dataFrame.sort_values(['freq', 'thr'])
    
    freqs= get_range(args.freqs) if args.freqs else df['freq'].unique()
    thrs= get_range(args.thrs) if args.thrs else df['thr'].unique()
    ins= get_range(args.ins) if args.ins else  df['in_cat'].unique()
    df_pred= perf_model.estimate_(freqs, thrs, ins, dataframe=True).sort_values(['freq', 'thr'])
    print(df_pred.head(5))
    
    def update_data(val):
        d = int(val)
        plotData.setProps(xlabel='Frequencies (GHz)', ylabel='Active threads', 
                            zlabel='Time (S)', title=title_)
        df_= df[df['in_cat']==d]
        df_pred_= df_pred[df_pred['in_cat']==d]
        df_= df_[df_['thr'].isin(df_pred_['thr'].unique())]

        if not df_.empty:
            plotData.plot3D(x=df_['freq'].unique(),y=df_['thr'].unique(),
                                                    z=df_['time'].values)
        plotData.plot3D(x=df_pred_['freq'].unique(),y=df_pred_['thr'].unique(),
                                            z=df_pred_['time'].values,points=False)
    plotData.update_user= update_data
    plotData.createSlider(label_='in', valmin_=df_pred['in_cat'].min(), valmax_=df_pred['in_cat'].max())

    plotData.ax.view_init(30,60)
    plotData.plotShow()

if args.create:
    createPerformanceModel(*args.create)
elif args.show:
    visualizePeformanceModel(*args.show)