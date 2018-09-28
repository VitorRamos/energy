import pickle
import numpy as np
from scipy.optimize import least_squares

class powerModel:
    def __init__(self, filename= ''):
        self.frequencies = []
        self.threads = []
        self.powers = []
        self.sensors = []
        self.power_model= lambda x,f,p: x[0]*f**3*p+x[1]*f*p+x[2]+x[3]*(np.floor(p/17)+1)
        self.power_model_x= []
        if filename:
            self.load(filename)

    def getVectorIPMI(self, ipmi, name):
        ret1 = []
        ret2 = []
        for t in ipmi:
            if 'sensor' in t.keys():
                ret1.append(t['sensor']['sources'][0][name])
                ret2.append(t['sensor']['sources'][1][name])
            else:
                ret1.append(t['sources'][0][name])
                ret2.append(t['sources'][1][name])
        ret1 = np.sort(ret1)  # median
        ret2 = np.sort(ret2)
        if len(ret1) > 40:
            return ret1[20:-20], ret2[20:-20]
        return ret1, ret2
    
    def getVectorRAPL(self, rapl):
        ret = []
        for t in rapl:
            ret.append(float(t))
        ret = np.sort(ret) # median
        return ret[20:-20]

    def loadData(self, filename, verbose=0, freqs_filter=[], thrs_filter=[],
                ipmi_source='dcOutPower', load_sensors= True):
        '''
            loads the power measuments from file

            filename: string
            verbose: number, level of verbose mode
            freqs_filter: list, list of frequencies to load
            thrs_filter: list, list of threads to load
            ipmi_source: string, source name on IPMI sensor can be dcOutPower or acInPower
            load_sensors: boolean, load the sensors data

            return frequencies, threads, powers, sensors
        '''
        with open(filename,'rb+') as f:
            data= pickle.load(f)

        has_sensors= 'sensors' in data[0]['threads'][0]['lpcpu'][0].keys()
        has_ipmi= 'ipmi' in data[0]['threads'][0]['lpcpu'][0].keys()
        has_rapl= 'rapl' in data[0]['threads'][0]['lpcpu'][0].keys()

        if verbose > 1 and has_ipmi:
            print("Amostras Frequencia nThreads Potencia 1 Potencia 2 Total Temperaturas")
        elif verbose > 1 and has_rapl:
            print("Amostras Frequencia nThreads Potencia")
        # get sensors name

        for thr in data[0]['threads']:
            if len(thrs_filter) > 0 and thr['nthreads'] not in thrs_filter: continue
            self.threads.append(thr['nthread'])

        for d in data:
            assert len(d['threads']) == len(self.threads)
            freq = int(d['freq'])
            if len(freqs_filter) > 0 and freq not in freqs_filter: continue
            freq= freq/1e6
            self.frequencies.append(freq)
            for thr in d['threads']:
                if len(thrs_filter) > 0 and thr['nthreads'] not in thrs_filter: continue
                for pcpu in thr['lpcpu'][0:1]: #TODO choose wich argument 
                    pw = 0
                    sensors_dict= {}

                    if has_ipmi:
                        tmp1_1, tmp1_2 = self.getVectorIPMI(pcpu['ipmi'], 'temp1')
                        tmp2_1, tmp2_2 = self.getVectorIPMI(pcpu['ipmi'], 'temp2')
                        pw_1, pw_2 = self.getVectorIPMI(pcpu['ipmi'], ipmi_source)
                        tmp1 = (np.mean(tmp1_1) + np.mean(tmp1_2)) / 2.0
                        tmp2 = (np.mean(tmp2_1) + np.mean(tmp2_2)) / 2.0
                        pw = (np.mean(pw_1) + np.mean(pw_2))
                        pw_std = np.std(np.array(pw_1) + np.array(pw_2))

                        if verbose:
                            print("{} {} {} {:.3f}±{:.3f} {:.3f}±{:.3f} {:.3f}±{:.3f} {:.3f} {:.3f}"
                                                    .format(len(pw_1), d['freq'], 
                                                    thr['nthread'], np.mean(pw_1),
                                                    np.std(pw_1), np.mean(pw_2),
                                                    np.std(pw_2), pw, pw_std,
                                                    tmp1, tmp2))
                            print("-"*70)

                    if has_rapl:
                        pw_vec = self.getVectorRAPL(pcpu['rapl'])
                        pw = np.mean(pw_vec)
                        pw_std = np.std(pw_vec)
                        if verbose:
                            print("{} {} {} {} {}".format(len(pw_vec),d['freq'],thr['nthread'],pw,pw_std))
                            print("-"*60)

                    if has_sensors and load_sensors:
                        for sample in pcpu['sensors']:
                            for s in sample:
                                s_split= s.split('|')
                                name= s_split[0].strip()
                                value= s_split[1].strip()
                                if name not in sensors_dict.keys():
                                    sensors_dict[name]= []
                                try:
                                    value= float(value)
                                    sensors_dict[name].append(value)
                                except:
                                    pass

                        for k in sensors_dict.keys():
                            if len(sensors_dict[k]) > 0:
                                sensors_dict[k]= np.mean(sensors_dict[k])
                            else:
                                sensors_dict[k]= 0
                    
                    self.sensors.append(sensors_dict)
                    self.powers.append(pw)
                    
        return self.frequencies, self.threads, self.powers, self.sensors

    def fit(self, verbose= 0):
        '''
        Fits the power model equation with the values loaded, need to call loadData first.

        verbose: number, level of verbose mode

        return constants fitted
        '''
        assert len(self.powers) > 0
        err= lambda x,f,p,y: self.power_model(x,f,p)-y
        x0= np.ones(4)
        f= np.repeat(self.frequencies,len(self.threads))
        p= np.tile(self.threads,len(self.frequencies))
        res_robust= least_squares(err, x0, loss='soft_l1', f_scale=0.1, args=(f, p, self.powers))
        self.power_model_x= res_robust.x
        if verbose > 0:
            res_robust
        return self.power_model_x
    
    def save(self,filename):
        assert self.power_model_x is not None
        with open(filename, 'wb+') as f:
            pickle.dump(self.power_model_x, f, pickle.HIGHEST_PROTOCOL)

    def load(self,filename):
        with open(filename, 'rb+') as f:
            self.power_model_x= pickle.load(f)
        return self.power_model_x
    
    def estimate(self, f, p):
        '''
        Estimetes the power with the model fited, need to call fit first

        f: list, frequency list
        p: list, number of cores list

        return list of estimatives
        '''
        assert len(self.power_model_x)>0
        f_len= len(f)
        f= np.repeat(f,len(p))
        p= np.tile(p,f_len)
        return self.power_model(self.power_model_x,f,p)
    
    def error(self):
        '''
        Calculates the error from the measured values to the model

        return error value
        '''
        assert len(self.power_model_x)>0
        estimative= np.array(self.estimate(self.frequencies, self.threads))
        real= np.array(self.powers)
        return np.sum(np.abs(real-estimative))/len(real)