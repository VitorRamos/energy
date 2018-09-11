#class dataProcessing:
#class monitoring:

import pickle
import numpy as np

class powerFitting:

    def getSensorIPMI(self, sensors, pos):
        ret = []
        for s in sensors:
            spl = s[pos].split('|')
            if 'degrees' in spl[2] or 'RPM' in spl[2] or 'Volts' in spl[2]:
                ret.append(float(spl[1]))
        return ret

    def getVectorIPMI(self, ipmi, name):
        ret1 = []
        ret2 = []
        for t in ipmi:
            ret1.append(t['sources'][0][name])
            ret2.append(t['sources'][1][name])
        ret1 = np.sort(ret1)
        ret2 = np.sort(ret2)
        return ret1[20:-20], ret2[20:-20]
    
    def getVectorRAPL(self, rapl):
        ret = []
        for t in rapl:
            ret.append(float(t))
        ret = np.sort(ret)
        return ret[20:-20]


    def loadData(self, filename, verbose=0, ipmi_source='dcOutPower'):
        with open(filename,'rb+') as f:
            data= pickle.load(f)

        frequencies = []
        threads = []
        powers = []
        sensors = [[] for x in range(58)]
        sensors_names = []

        has_sensors= 'sensors' in data[1]['threads'][0]['lpcpu'][0].keys()
        has_ipmi= 'ipmi' in data[1]['threads'][0]['lpcpu'][0].keys()
        has_rapl= 'rapl' in data[1]['threads'][0]['lpcpu'][0].keys()

        if verbose > 1 and has_ipmi:
            print("Amostras Frequencia nThreads Potencia 1 Potencia 2 Total Temperaturas")
        elif verbose > 1 and has_rapl:
            print("Amostras Frequencia nThreads Potencia")
        # get sensors name
        if has_sensors:
            for sn in data[1]['threads'][0]['lpcpu'][0]['sensors'][0]:
                sensors_names.append(sn.split('|')[0])
                if verbose > 2 and ('degrees' in sn.split('|')[2] or 
                                    'RPM' in sn.split('|')[2] or 
                                    'Volts' in sn.split('|')[2]):
                    print(sn.split('|')[0])

        for thr in data[0]['threads']:
            threads.append(thr['nthread'])

        for d in data:
            freq = float(d['freq'])/1e6
            frequencies.append(freq)
            for thr in d['threads'][:]:
                for pcpu in thr['lpcpu']:
                    pw = 0
                    if has_ipmi:
                        tmp1_1, tmp1_2 = getVectorIPMI(pcpu['ipmi'], 'temp1')
                        tmp2_1, tmp2_2 = getVectorIPMI(pcpu['ipmi'], 'temp2')
                        pw_1, pw_2 = getVectorIPMI(pcpu['ipmi'], ipmi_source)
                        tmp1 = (np.mean(tmp1_1) + np.mean(tmp1_2)) / 2.0
                        tmp2 = (np.mean(tmp2_1) + np.mean(tmp2_2)) / 2.0
                        pw = (np.mean(pw_1) + np.mean(pw_2))
                        pw_std = np.std(np.array(pw_1) + np.array(pw_2))

                        if verbose:
                            print("{} {} {} {} {} {} {} {} {}".format(len(pw_1), d['freq'], 
                                                    thr['nthread'], np.mean(pw_1),
                                                    np.std(pw_1), np.mean(pw_2),
                                                    np.std(pw_2), pw, pw_std,
                                                    tmp1, tmp2))
                            print("-"*100)


                    if has_rapl:
                        pw_vec = getVectorRAPL(pcpu['rapl'])
                        pw = np.mean(pw_vec)
                        pw_std = np.std(pw_vec)
                        if verbose:
                            print("{} {} {} {} {}".format(len(pw_vec),d['freq'],thr['nthread'],pw,pw_std))
                            print("-"*60)

                    if has_sensors:
                        s_info = ''
                        for l in range(0, len(pcpu['sensors'][0])):
                            lv = getSensorIPMI(pcpu['sensors'], l)
                            if len(lv) > 0:
                                sensors[l].append(np.mean(lv))

                    powers.append(pw)

        return frequencies, threads, powers, sensors, sensors_names



