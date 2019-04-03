import _pickle as pickle
import numpy as np
import pandas as pd
from sklearn.svm import SVR
from sklearn.model_selection import train_test_split
from sklearn.model_selection import cross_validate, cross_val_score

class performanceModel:
    def __init__(self):
        '''
           Creata a performance model 
        '''
        self.dataFrame= None
        self.svr= None
        self.header= None

    def loadData(self, filename, arg_num, verbose=0, method= 'constTime',
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
        freqs_filter: list, list of frequencies to load in GHz
        thrs_filter: list, list of threads to load

        return dataFrame if createDataFrame is True otherwise frequencies, threads, powers
        '''
        #TODO save all arguments
        with open(filename,'rb+') as f:
            data= pickle.load(f)

        if "header" in data[0].keys():
            self.header= data[0]["header"]
            if verbose > 1:
                print(self.header)

        has_ipmi= 'ipmi' in data[0]['threads'][0]['lpcpu'][0].keys()
        has_rapl= 'rapl' in data[0]['threads'][0]['lpcpu'][0].keys()

        df = []
        isClose= lambda x,y: abs(x-y)<0.01
        for d in data:
            # assert len(d['threads']) == len(self.threads)
            if len(freqs_filter) > 0 and not any(isClose(x,float(d['freq'])/1e6) for x in freqs_filter): continue
            for thr in d['threads']:
                if len(thrs_filter) > 0 and thr['nthread'] not in thrs_filter: continue
                for p in thr['lpcpu']:
                    pw = 0
                    pw_size = 0
                    if has_rapl:
                        for s in p['rapl']:
                            aux= float(s['sensor']) 
                            if aux > 0:
                                pw+=aux
                                pw_size+=1                                
                                df.append([d['freq'], thr['nthread'], p['arg'][arg_num], 
                                        s['time'], aux])

                    elif has_ipmi:
                        for s in p['ipmi']:
                            pot = float(s['sensor']['sources'][0]['dcOutPower']+
                                    s['sensor']['sources'][1]['dcOutPower'])
                            pw+=pot
                            df.append([d['freq'], thr['nthread'], p['arg'][arg_num], s['time'], pot])
                        pw_size= len(p['ipmi'])
                     
                    df.append([d['freq'], thr['nthread'], p['arg'][arg_num], 
                        p['total_time'], pw/pw_size])

                    if verbose > 0:
                        print(d['freq'], thr['nthread'], p['arg'][arg_num], 
                                'T', p['total_time'], 'P', pw, 'E', p['total_time']*pw/pw_size)

        self.dataFrame = pd.DataFrame(df, columns=['freq', 'thr', 'in', 'time', 'pw'])
        cat = pd.factorize(self.dataFrame['in'])
        self.dataFrame['in_cat'] = cat[0] + 1
        self.dataFrame['freq'] = self.dataFrame['freq'].astype(float)/1e6
        self.dataFrame= self.dataFrame.sort_values(['freq','thr','in_cat','time'])
        df_cat= self.dataFrame[['in','in_cat']].drop_duplicates()

        if method == 'constTime':
            df = self.dataFrame.groupby(['freq','thr','in_cat']).mean().reset_index()
            df['time'] = self.dataFrame.groupby(['freq','thr', 'in_cat']).tail(1)['time'].values

            self.dataFrame = df
            self.dataFrame['energy'] = self.dataFrame['time']*self.dataFrame['pw']

        elif method == 'timeDiff':
            def difftime(df):
                df['time_diff'] = np.hstack(([0], df['time'].values[1:]-df['time'].values[:-1]))
                df['energy']= df['time_diff']*df['pw']
                return df
            self.dataFrame= self.dataFrame.groupby(['freq','thr','in_cat']).apply(difftime)
            df = self.dataFrame.groupby(['freq','thr','in_cat']).mean().reset_index()
            df['time'] = self.dataFrame.groupby(['freq','thr','in_cat']).tail(1)['time'].values
            df['energy'] = self.dataFrame.groupby(['freq','thr','in_cat']).energy.sum().values
            self.dataFrame = df.drop(columns='time_diff')
        
        self.dataFrame = pd.merge(self.dataFrame,df_cat)
        return self.dataFrame

    def fit(self, C_=10e3, gamma_=0.1, train_size_= 0.9, dataframe=False):
        '''
        Fit the svr model with values from dataframe

        C_: svr parameter
        gamma_: svr parameter
        train_size_: percentage of samples used on train

        return svr
        '''
        assert self.dataFrame is not None
        self.svr= SVR(C=C_,gamma=gamma_)

        X = self.dataFrame[['freq', 'thr', 'in_cat']].values
        Y = self.dataFrame['time'].astype(float).values
        Xtrain, _, Ytrain, _ = train_test_split(X, Y, train_size=train_size_, random_state=0)
        self.svr.fit(Xtrain, Ytrain)

        if dataframe:
            Xtrain= pd.DataFrame(Xtrain, columns=['freq','thr','in_cat'])
            Xtrain['time']= Ytrain
            return Xtrain
            
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

    def estimate_(self, frs, thrs, ins, dataframe=False):
        '''
        Estimate the time from the list of freq, thr, in
        dataframe : bool, return a dataframe

        return list of estimatives
        '''
        X= np.array(np.meshgrid(frs,thrs,ins)).T.reshape(-1,3)
        Y= self.svr.predict(X)

        if dataframe:
            X= pd.DataFrame(X, columns=['freq','thr','in_cat'])
            X['time']= Y
            return X

        return Y

    def estimate(self, X, dataframe=False):
        '''
        Estimate the time from the list of [freq, thr, in]

        return list of estimatives
        '''
        assert self.svr is not None
        Y= self.svr.predict(X)

        if dataframe:
            X= pd.DataFrame(X, columns=['freq','thr','in_cat'])
            X['time']= Y
            return X

        return Y


    def error(self, method='mpe'):
        '''
            Calculate the error from the measured values, need svr and dataframe

            method: string
                    mae, mean abusolute error
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
