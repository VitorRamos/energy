import pickle
import numpy as np
from scipy.optimize import least_squares

class powerFitting:
    def __init__(self, filename= ''):
        self.frequencies = []
        self.threads = []
        self.powers = []
        self.sensors = []
        self.power_model= lambda x,f,p: x[0]*f**3*p+x[1]*f*p+x[2]+x[3]*(np.floor(p/17)+1)
        self.power_model_x= []
        if filename:
            self.loadData(filename)

    def getVectorIPMI(self, ipmi, name):
        ret1 = []
        ret2 = []
        for t in ipmi:
            ret1.append(t['sources'][0][name])
            ret2.append(t['sources'][1][name])
        ret1 = np.sort(ret1)  # median
        ret2 = np.sort(ret2)
        return ret1[20:-20], ret2[20:-20] 
    
    def getVectorRAPL(self, rapl):
        ret = []
        for t in rapl:
            ret.append(float(t))
        ret = np.sort(ret) # median
        return ret[20:-20]

    def loadData(self, filename, verbose=0, ipmi_source='dcOutPower',
                load_sensors= True, freqs_allow=[], thrs_allow=[]):
        with open(filename,'rb+') as f:
            data= pickle.load(f)

        has_sensors= 'sensors' in data[0]['threads'][0]['lpcpu'][0].keys()
        has_ipmi= 'ipmi' in data[1]['threads'][0]['lpcpu'][0].keys()
        has_rapl= 'rapl' in data[1]['threads'][0]['lpcpu'][0].keys()

        if verbose > 1 and has_ipmi:
            print("Amostras Frequencia nThreads Potencia 1 Potencia 2 Total Temperaturas")
        elif verbose > 1 and has_rapl:
            print("Amostras Frequencia nThreads Potencia")
        # get sensors name

        for thr in data[0]['threads']:
            if len(thrs_allow) > 0 and thr['nthreads'] not in thrs_allow: continue
            self.threads.append(thr['nthread'])

        for d in data:
            assert len(d['threads']) == len(self.threads)
            freq = int(d['freq'])
            if len(freqs_allow) > 0 and freq not in freqs_allow: continue
            freq= freq/1e6
            self.frequencies.append(freq)
            for thr in d['threads']:
                if len(thrs_allow) > 0 and thr['nthreads'] not in thrs_allow: continue
                for pcpu in thr['lpcpu']:
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
        err= lambda x,f,p,y: self.power_model(x,f,p)-y
        x0= np.ones(4)
        f= np.repeat(self.frequencies,len(self.threads))
        p= np.tile(self.threads,len(self.frequencies))
        res_robust= least_squares(err, x0, loss='soft_l1', f_scale=0.1, args=(f, p, self.powers))
        self.power_model_x= res_robust.x
        if verbose > 0:
            res_robust
        return self.power_model_x
    
    def power_estimate(self, f, p):
        assert len(self.power_model_x)>0
        f= np.repeat(self.frequencies,len(self.threads))
        p= np.tile(self.threads,len(self.frequencies))
        return self.power_model(self.power_model_x,f,p)
    
    def error(self):
        assert len(self.power_model_x)>0
        estimative= np.array(self.power_estimate(self.frequencies, self.threads))
        real= np.array(self.powers)
        return np.sum(np.abs(real-estimative))/len(real)