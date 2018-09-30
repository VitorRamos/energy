import pickle
import pandas as pd
import numpy as np


class dvfsModel:
    def __init__(self):
        self.frequencies = []
        self.threads = []
        self.powers = []
        self.dataFrame = None

    def loadData(self, filename, arg_num, verbose=0, method='allSamples'):
        '''
        filename: string
        arg_num: argument that contains the problem size
        verbose: number, level of verbose mode #TODO
        method: string
            constTime : Average the power samples to estimate energy,
                        this assume the interval between samples are constant
            timeDiff : Uses time interval to estimate energy and accumulates
            allSamples : Keep all samples on the power array, energy it's not estimated

        return dataFrame if createDataFrame is True otherwise frequencies, threads, powers
        '''

        with open(filename, 'rb') as f:
            data = pickle.load(f)

        has_sensors = 'sensors' in data[0]['lpcpu'][0].keys()
        has_ipmi = 'ipmi' in data[0]['lpcpu'][0].keys()
        has_rapl = 'rapl' in data[0]['lpcpu'][0].keys()

        df = []
        for thr in data:
            for lpcpu in thr['lpcpu']:
                pw = []
                row = []
                if has_ipmi:
                    for s in lpcpu['ipmi']:
                        pot = float(s['sensor']['sources'][0]['dcOutPower'] +
                                    s['sensor']['sources'][1]['dcOutPower'])
                        pw.append(pot)
                        row = [float(s['freqs'][key][0]) for key in sorted(s['freqs'].keys())]
                        df.append([thr['nthread'], lpcpu['arg'][arg_num], s['time'], pot]+row)

                    pw = np.asarray(pw)
                    df.append([thr['nthread'], lpcpu['arg'][arg_num],
                              lpcpu['total_time'], pw.mean()] + row)

        self.dataFrame = pd.DataFrame(df,
                    columns=['thr', 'in', 'time', 'pw'] + ['cpu%i' % x for x in range(0, 32)])

        if method == 'constTime':
            self.dataFrame = self.dataFrame.sort_values(['thr', 'in', 'time'])
            freqs = pd.DataFrame(self.dataFrame.groupby(['thr', 'in']).mean().reset_index())
            freqs['time'] = self.dataFrame.groupby(['thr', 'in']).tail(1)['time'].values
            self.dataFrame = freqs
            self.dataFrame['energy'] = self.dataFrame['time']*self.dataFrame['pw']

        elif method == 'timeDiff':
            self.dataFrame = self.dataFrame.sort_values(['thr', 'in', 'time'])
            def difftime(df):
                df['time_diff']= np.hstack(([0], df['time'].values[1:]-df['time'].values[:-1]))
                df['energy']= df['time_diff']*df['pw']
                return df
            self.dataFrame=self.dataFrame.groupby(['thr', 'in']).apply(difftime)
            freqs= pd.DataFrame(self.dataFrame.groupby(['thr','in']).mean().reset_index())
            freqs['time']= self.dataFrame.groupby(['thr','in']).tail(1)['time'].values
            freqs['energy']= self.dataFrame.groupby(['thr','in']).energy.sum().values
            self.dataFrame= freqs.drop(columns='time_diff')
        
        return self.dataFrame
