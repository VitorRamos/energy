from energyOptimal import plotData
from energyOptimal.powerModel import powerModel

import _pickle as pickle 
import argparse
import numpy as np

parser= argparse.ArgumentParser(description='Create and visualize power model from monitor data')
parser.add_argument('--create',type=str,help='Create power model',nargs=2,metavar=('data','power_model'))
parser.add_argument('--show',type=str,help='Show power model')
parser.add_argument('--freqs',type=str,help='Frequency range', default='1.2,2.3,0.1',nargs='?')
parser.add_argument('--thrs',type=str,help='Threads range', default='',nargs='?')
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

def createPowerModel(path, save_model):
    pw_model= powerModel()
    # pw_model.power_model= lambda x,f,p: p*(x[0]*f**3+x[1]*f+x[2])+x[3]+x[4]*(np.floor(p/17)+1)
    # pw_model.power_mode_n = 5
    pw_model.power_model= lambda x,f,p: p*(x[0]*f**3+x[1]*f+x[2])+x[3]#+x[4]*(np.floor(p/17)+1)
    pw_model.power_mode_n = 4
    pw_model.loadData(filename=path, verbose=1, load_sensors=False, freqs_filter= get_range(args.freqs), 
                                                                    thrs_filter= get_range(args.thrs))
    pw_model.fit()
    pickle.dump(pw_model, open(save_model,"wb"))
    error= pw_model.error()
    print("Power model constants, ", pw_model.power_model_c)
    print("Erro, ", error)

    return pw_model

def visualizePowerModel(path):
    # Plot the measured values and the model
    pw_model = pickle.load(open(path,"rb"))
    # pw_model.power_model= lambda x,f,p: p*(x[0]*f**3+x[1]*f+x[2])+x[3]+x[4]*(np.floor(p/17)+1)
    # pw_model.power_mode_n = 5
    # pw_model.power_model_= lambda x,f,p: x[0]*f**3+x[1]*f+x[2]
    pw_model.power_model= lambda x,f,p: p*(x[0]*f**3+x[1]*f+x[2])+x[3]#+x[4]*(np.floor(p/17)+1)
    pw_model.power_mode_n = 4
    print(pw_model.power_model_c)
    freqs= get_range(args.freqs) if args.freqs else pw_model.frequencies
    thrs= get_range(args.thrs) if args.thrs else pw_model.threads
    est= pw_model.estimate(freqs, thrs)
    plotData.setProps(xlabel= "Frequencies (GHz)", ylabel= "Active Cores", zlabel= "Power (W)")
    plotData.plot3D(x=pw_model.frequencies, y=pw_model.threads, z=pw_model.powers, legend="Measurements")
    plotData.plot3D(x=freqs, y=thrs, z=est, points=False, legend="Model")
    plotData.plotShow(showLegend= True)
    # plotData.savePlot(filename= 'pw_model.png', showLegend= True)

if args.create:
    createPowerModel(*args.create)
elif args.show:
    visualizePowerModel(args.show)