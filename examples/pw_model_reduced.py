from energyOptimal.powerModel import powerModel
from energyOptimal import plotData 
import numpy as np
import pandas as pd
import _pickle as pickle

pw_model_full= pickle.load(open("data/models/power_model/ipmi_2-32_cpuload.pkl","rb"))
print("Percetage error pw_mode full: {}".format(pw_model_full.error()))

thrs_filter=[
    [2,32],
    [2,16,32],
    [2,8,16,32],
    [2,8,16,24,32]
]

freq_filter=[
    [1.2,2.2],
    [1.2,1.7,2.2],
    [1.2,1.5,1.7,2.2],
    [1.2,1.5,1.7,2.0,2.2],
]

table= []
for freq in freq_filter:
    for thr in thrs_filter:
        n_points= len(freq)*len(thr)

        print("points {} freqs {} thrs {}".format(n_points, freq, thr))

        pw_model= powerModel()
        pw_model.loadData(filename='data/power_model/ipmi_2-32_cpuload.pkl',freqs_filter=freq,thrs_filter=thr)
        pw_model.fit()

        f_est, p_est = pw_model_full.frequencies, pw_model_full.threads
        pws_est= pw_model.estimate(f_est, p_est)

        df_est= pw_model.estimate(f_est,p_est,dataFrame=True)
        df_full= pw_model_full.get_Dataframe()
        df= pd.merge(df_est,df_full)
        df['diff']= np.abs((df['pw_est']-df['pw'])/df['pw']*100)

        print("Max error from all measured points {} ".format(df['diff'].max()))

        plotData.setProps(xlabel='Frequency', ylabel='Threads',zlabel='Power')
        plotData.plot3D(pw_model_full.frequencies,pw_model_full.threads,pw_model_full.powers,color_='blue',legend='Measurement')
        plotData.plot3D(pw_model.frequencies,pw_model.threads,pw_model.powers,color_='red',legend='Chosen points')
        plotData.plot3D(f_est,p_est,pws_est,points=False,legend='Estimative')
        plotData.savePlot('figures/pwmodel_{}_{}.png'.format(len(freq),len(thr)),showLegend=True)
        table.append([len(freq), len(thr), df['diff'].max()])
        # plotData.plotShow()
        # plotData.fig = plotData.plt.figure()
        # plotData.ax = plotData.fig.gca(projection='3d')

table= pd.DataFrame(table,columns=['freq','thr','error'])
table.to_csv('table.csv')
crosstable= pd.crosstab(table['freq'],table['thr'],table['error'],aggfunc=min)
crosstable.to_csv('cross.csv')
print(crosstable)