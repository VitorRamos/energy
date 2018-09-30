from energyOptimal import plotData
from energyOptimal.powerModel import powerModel
from energyOptimal.performanceModel import performanceModel
from energyOptimal.energyModel import energyModel
import numpy as np
import pandas as pd
import argparse

# titles=['Blackscholes','Canneal','Dedup', 'Ferret','Fluidanimate','Freqmine',
#                     'Raytrace','Swaptions','Vips',
#                     'x264','HPL','Openmc']
# parsecapps=['completo_black_3.pkl','completo_canneal_2.pkl','completo_dedup_3.pkl',
#                     'completo_ferret_3.pkl','completo_fluid_2.pkl','completo_freq.pkl',
#                     'completo_rtview_2.pkl','completo_swaptions_1.pkl','completo_vips_1.pkl',
#                     'completo_x264_1.pkl','completo_xhpl.pkl','completo_openmc_kernel_novo.pkl']
# 
# program= 'completo_xhpl.pkl'

parser= argparse.ArgumentParser(description='Show energy model from power model and performance model')
parser.add_argument('path_power',type=str,help='Path to power model fited')
parser.add_argument('path_dataframe',type=str,help='Path to power dataframe')
parser.add_argument('path_svr',type=str,help='Path to svr fited')
parser.add_argument('--title',type=str,help='Figure title', default='',nargs='?')
parser.add_argument('--freqs',type=str,help='Frequency range', default='1.2,2.3,0.1',nargs='?')
parser.add_argument('--thrs',type=str,help='Threads range', default='1;2,33,2',nargs='?')
args = parser.parse_args()

def get_range(str_range):
    _range=[]
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

pw_model= powerModel(args.path_power)
perf_model= performanceModel(args.path_dataframe, args.path_svr)
en_model= energyModel(pw_model,perf_model, thr_range_= get_range(args.thrs), freq_range_= get_range(args.freqs))
df= perf_model.dataFrame.sort_values(['freq','thr'])
df_pred= en_model.dataFrame.sort_values(['freq','thr'])

print(en_model.minimalEnergy())

def update_data(val):
    d= int(val)
    plotData.setProps(xlabel='Frequencies (GHz)', ylabel='Active threads',
                        zlabel='Energy (KJ)', title=args.title)
    df_pred_= df_pred[df_pred['in_cat']==d]
    df_= df[df['in_cat']==d]

    df_= df_[df_['thr'].isin(df_pred_['thr'].unique())]
    plotData.ax.view_init(30,60)

    if not df_.empty:
        plotData.plot3D(x=df_['freq'].unique(),y=df_['thr'].unique(),
                                        z=df_['energy'].values/1e3,points=True,legend='Measurements')
    plotData.plot3D(x=df_pred_['freq'].unique(),y=df_pred_['thr'].unique(),
                                        z=df_pred_['energy_model'].values/1e3,points=False,legend='Model')
    
plotData.update_user= update_data
plotData.createSlider(label_='in',valmin_=df_pred['in_cat'].min(),valmax_=df_pred['in_cat'].max())
plotData.plotShow(showLegend=True)
