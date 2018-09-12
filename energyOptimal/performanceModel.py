import pickle
import numpy as np
import pandas as pd
from sklearn.svm import SVR
from sklearn.model_selection import train_test_split
from sklearn.model_selection import cross_validate, cross_val_score

class performanceModel:
    def __init__(self, dataFramefile= '', svrfile=''):
        self.frequencies = []
        self.threads = []
        self.powers = []
        self.dataFrame= None
        self.svr= None
        if dataFramefile and svrfile:
            self.loadDataFrame(dataFramefile)
            self.loadSVR(svrfile)

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
            self.dataFrame = pd.DataFrame(df, columns=['freq', 'thr', 'in', 'time', 'pw'])
            cat = pd.factorize(self.dataFrame['in'])
            self.dataFrame['in_cat'] = cat[0] + 1
            self.dataFrame['freq'] = self.dataFrame['freq'].astype(float)/1e6
            return self.dataFrame
        
        return self.frequencies, self.threads, self.powers
    
    def saveDataframe(self, filename):
        assert self.dataFrame is not None
        with open(filename, 'wb+') as f:
            pickle.dump(self.dataFrame, f, pickle.HIGHEST_PROTOCOL)

    def loadDataFrame(self, filename):
        with open(filename, 'rb+') as f:
            self.dataFrame= pickle.load(f)
        return self.dataFrame

    def fit(self, C_=10e3, gamma_=0.1):
        '''
        Fit the svr model with values from dataframe

        C_: svr parameter
        gamma_: svr parameter
        test_size: percentage of samples used on test

        return svr
        '''
        assert self.dataFrame is not None
        self.svr= SVR(C=C_,gamma=gamma_)
        X = self.dataFrame[['freq', 'thr', 'in_cat']].values
        Y = self.dataFrame['time'].astype(float).values
        Xtrain, Xtest, Ytrain, Ytest = train_test_split(X, Y, test_size=0.1, random_state=0)
        self.svr.fit(Xtrain, Ytrain)

        return self.svr

    def saveSVR(self, filename):
        assert self.svr is not None
        with open(filename, 'wb+') as f:
            pickle.dump(self.svr, f, pickle.HIGHEST_PROTOCOL)

    def loadSVR(self, filename):
        with open(filename, 'rb+') as f:
            self.svr= pickle.load(f)
        return self.svr

    def mpe(self,clf, X, y):
        return np.sum(np.abs(y-clf.predict(X))/y)/len(y)
    def mae(self,clf, X, y):
        return np.sum(np.abs(y-clf.predict(X)))/len(y)

    def crossValidate(self, verbose=0, method='mpe'):
        '''
            Cross validate the performance model
            method: string
                 mab, mean abusolute error
                 mpe, mean percentage error

            return scores
        '''
        assert self.svr is not None

        X = self.dataFrame[['freq', 'thr', 'in_cat']].values
        Y = self.dataFrame['time'].astype(float).values
        scores= cross_val_score(self.svr,  X, Y, cv=10, scoring= self.mae if method == 'mae' else self.mpe, n_jobs=4)
        if verbose > 0:
            print('Cross validacao mpe', scores*100, np.mean(scores)*100)
        return scores

    def estimate2(self, frs, thrs, ins):
        X= np.array(np.meshgrid(frs,thrs,ins)).T.reshape(-1,3)
        Y= self.svr.predict(X)

        return Y

    def estimate(self, X):
        '''
        Estimate the time from the list of [freq, thr, in]
        
        return list of estimatives
        '''
        assert self.svr is not None
        Y= self.svr.predict(X)
        return Y
    

    def error(self, method='mab'):
        '''
            Calculate the error from the measured values, need svr and dataframe

            method: string
                    mab, mean abusolute error
                    mpe, mean percentage error
            return error
        '''
        assert self.svr is not None
        assert self.dataFrame is not None

        estimative= self.estimate(self.dataFrame[['freq', 'thr', 'in_cat']].values)
        real= np.array(self.dataFrame['time'].values)
        if method == 'mae':
            return np.sum(np.abs(real-estimative))/len(real)
        elif method == 'mpe':
            return np.sum(np.abs((real-estimative)/real))/len(real)