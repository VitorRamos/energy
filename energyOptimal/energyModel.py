import pickle
import numpy as np
import pandas as pd

class energyModel:
    def __init__(self):
        self.frequencies = []
        self.threads = []
        self.powers = []

    def loadData(self, filename, arg_num, verbose=0, method= 'constTime', createDataFrame= True,
                 freqs_filter=[], thrs_filter=[]):
        '''
        filename: string
        arg_num: argument that contains the problem size
        verbose: number, level of verbose mode
        method: string
            constTime : Average the power samples to estimate energy,
                        this assume the interval between samples are constant
            timeDiff : Uses time interval to estimate energy and accumulates
            allSamples : Keep all samples on the power array, energy it's not estimated
        createDataFrame: boolean
        freqs_filter: list, list of frequencies to load
        thrs_filter: list, list of threads to load

        return dataFrame if createDataFrame is True otherwise frequencies, threads, powers
        '''

        with open(filename,'rb+') as f:
            data= pickle.load(f)
        
        has_ipmi= 'ipmi' in data[0]['threads'][0]['lpcpu'][0].keys()
        has_rapl= 'rapl' in data[0]['threads'][0]['lpcpu'][0].keys()
        
        for thr in data[0]['threads']:
            if len(thrs_filter) > 0 and thr['nthreads'] not in thrs_filter: continue
            self.threads.append(thr['nthread'])

        df = []
        for d in data:
            assert len(d['threads']) == len(self.threads)
            freq = int(d['freq'])
            if len(freqs_filter) > 0 and freq not in freqs_filter: continue
            freq= freq/1e6
            self.frequencies.append(freq)
            for thr in d['threads']:
                if len(thrs_filter) > 0 and thr['nthreads'] not in thrs_filter: continue
                for p in thr['lpcpu']:
                    pw = []
                    if has_rapl:
                        if method == 'constTime':
                            pw= 0
                            for i in range(len(p['rapl'])):
                                pot = p['rapl'][i]['sensor']
                                if i - 1 >= 0:
                                    pw += (p['rapl'][i]['time']-p['rapl'][i - 1]['time'])*pot
                                if i == len(p['rapl']) - 1:
                                    pw += pot * (p['total_time']-p['rapl'][i]['time'])
                        else:
                            for s in p['rapl']:
                                if float(s['sensor']) > 0:
                                    if createDataFrame and method == 'allSamples':
                                        row = [d['freq'], thr['nthread'], p['arg'][arg_num], s['time'], pot]
                                        df.append(row)
                                    pw.append(float(s['sensor']))
                            if method == 'timeDiff':
                                pw= np.mean(pw)
                            elif method == 'allSamples':
                                if createDataFrame:
                                    pw= np.mean(pw)

                    elif has_ipmi:
                        if method == 'constTime':
                            pw= 0
                            for i in range(len(p['ipmi'])):
                                pot = p['ipmi'][i]['sensor']['sources'][0]['dcOutPower']
                                pot += p['ipmi'][i]['sensor']['sources'][1]['dcOutPower']
                                if i - 1 >= 0:
                                    pw += (p['ipmi'][i]['time']-p['ipmi'][i - 1]['time'])*pot
                                if i == len(p['ipmi']) - 1:
                                    pw += pot * (p['total_time']-p['ipmi'][i]['time'])

                        else:    
                            for s in p['ipmi']:
                                pot = float(s['sensor']['sources'][0]['dcOutPower']+
                                            s['sensor']['sources'][1]['dcOutPower'])
                                if createDataFrame and method == 'allSamples':
                                    row = [d['freq'], thr['nthread'], p['arg'][arg_num], s['time'], pot]
                                    df.append(row)
                                pw.append(pot)

                            if method == 'timeDiff':
                                pw= np.mean(pw)
                            elif method == 'allSamples':
                                if createDataFrame:
                                    pw= np.mean(pw)
                    
                    if createDataFrame:
                        row = [d['freq'], thr['nthread'], p['arg'][arg_num], p['total_time'], pw]
                        df.append(row)

                    self.powers.append(pw)

                    if verbose > 0:
                        if type(pw) == list:
                            pw= np.mean(pw)
                        print(d['freq'], thr['nthread'], p['arg'][arg_num], 
                        'T', p['total_time'], 'P', pw, 'E', p['total_time']*pw)

        if createDataFrame:
            df = pd.DataFrame(df, columns=['freq', 'thr', 'in', 'time', 'pw'])
            return df
        
        return self.frequencies, self.threads, self.powers