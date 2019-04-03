from . import performanceModel, powerModel
import numpy as np
import pandas as pd

class energyModel:
    def __init__(self, pw_model, perf_model, freq_range_=None, thr_range_=None, inputs_range_=None):
        '''
            pw_model: power model fited
            perf_model: performance model fited
            freq_range_: frequency range for estimation dataframe
            thr_range_: threads range for estimation dataframe
            inputs_range_: inputs range for estimation dataframe
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

        self.__createDataframe()

    def __createDataframe(self):
        '''
            Return dataframe with estimated energy
        '''
        self.dataFrame= pd.DataFrame(np.array(np.meshgrid(self.freq_range,
                                        self.thr_range,self.inputs_range)).T.reshape(-1,3),
                                        columns=['freq', 'thr', 'in_cat'])
        self.dataFrame['time_model']= self.performace_model.estimate(self.dataFrame[['freq','thr','in_cat']])
        self.dataFrame['pw_model']= np.tile(self.power_model.estimate(self.freq_range,self.thr_range), len(self.inputs_range))
        self.dataFrame['energy_model']= self.dataFrame['time_model']*self.dataFrame['pw_model']
        return self.dataFrame
    
    def minimalEnergy(self):
        '''
            Return dataframe with minimal energy for all inputs
        '''
        return self.dataFrame[self.dataFrame.energy_model.isin( self.dataFrame.groupby('in_cat').energy_model.min() )]
    
    def realMinimalEnergy(self):
        '''
            Return dataframe with minimal energy for all inputs with real energy consumed from perf model
        '''
        df= self.minimalEnergy()[['in_cat','thr','freq','energy_model']]
        df= pd.merge(df,self.performace_model.dataFrame[['in_cat','thr','freq','time','energy']])
        return df