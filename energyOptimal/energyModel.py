from . import performanceModel, powerModel
import numpy as np
import pandas as pd

class energyModel:
    def __init__(self, pw_model, perf_model, freq_range_=None, thr_range_=None, inputs_range_=None):
        '''
            TODO
        '''
        self.power_model= pw_model
        self.performace_model= perf_model
        if freq_range_ is None:
            self.freq_range= perf_model.dataFrame['freq'].unique()
        else:
            self.freq_range= freq_range_

        if thr_range_ is None:
            self.thr_range= perf_model.dataFrame['thr'].unique()
        else:
            self.thr_range= thr_range_

        if inputs_range_ is None:
            self.inputs_range= perf_model.dataFrame['in_cat'].unique()
        else:
            self.inputs_range= inputs_range_

        self.createDataframe()

    def createDataframe(self):
        self.dataFrame= pd.DataFrame(np.array(np.meshgrid(self.freq_range,
                                        self.thr_range,self.inputs_range)).T.reshape(-1,3),
                                        columns=['freq', 'thr', 'in'])
        self.dataFrame['time']= self.performace_model.estimate(self.dataFrame[['freq','thr','in']])
        self.dataFrame['pw']= np.tile(self.power_model.estimate(self.freq_range,self.thr_range), 
                                                        len(self.inputs_range))
        self.dataFrame['energy']= self.dataFrame['time']*self.dataFrame['pw']
        return self.dataFrame
    
    def minimalEnergy(self):
        return self.dataFrame[self.dataFrame.energy.isin( self.dataFrame.groupby('in').energy.min() )]
    