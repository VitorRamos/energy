from .rapl import RAPL
from .ipmi import IPMI
from .cpufreq import cpuFreq

import subprocess
import threading
import pickle
import time
import os

class monitorProcess:
    def __init__(self, program_name_, sensor_type_='ipmi'):
        self.sensor_type = sensor_type_
        if self.sensor_type == "rapl":
            self.sensor = RAPL("service3")
        elif self.sensor_type == "ipmi":
            self.sensor = IPMI(server= "http://localhost:8080", name_="admin", password_="admin")
        else:
            raise(Exception("Invalid sensor type"))

        self.cpu = cpuFreq()
        self.models = []
        self.header = []
        self.program_name = program_name_

    def run(self, list_threads, list_args, idle_time, save_name, verbose=0):
        try:
            self.cpu.reset()
            self.cpu.disable_hyperthread()
            self.cpu.set_governors("userspace")
            freq = self.cpu.get_available_frequencies()
            cpus = self.cpu.get_online_cpus()
        except Exception as e:
            raise(Exception("Unable to control cpu", e))

        for f in freq:
            info_threads = []
            for thr in list_threads:
                try:
                    self.cpu.enable_cpu(cpus)
                    self.cpu.set_governors("userspace")
                    self.cpu.disable_cpu(cpus[thr:])
                    self.cpu.set_frequencies(f)
                except Exception as e:
                    print("Unable to control frequency", e)
                    raise(Exception("Unable to control frequency", e))

                info_pcpu = []
                for arg in list_args:
                    info_sensor = []

                    arg = list(map(lambda s: str.replace(s, "__nt__", str(thr)), arg))
                    if verbose > 0:
                        print("Argumentos", arg)

                    program = subprocess.Popen(["./"+str(self.program_name)]+arg)
                    ti = time.time()
                    while program.poll() == None:
                        if verbose > 0:
                            print("Tempo", time.time()-ti,
                                  "Frequencia ", f, " nThreads", thr)

                        tg = time.time()
                        info = {"time": time.time()-ti,
                                "sensor": self.sensor.get_data()}
                        info_sensor.append(info.copy())
                        if verbose > 2:
                            self.sensor.print_data()
                        elif verbose > 1:
                            self.sensor.print_pot()

                        tg = time.time()-tg
#						if 1-tg >= 0:
#							time.sleep(1-tg)
                    program.wait()
                    tt = time.time()-ti
                    if verbose > 0:
                        print("Tempo total", tt)

                    l1 = {"arg": list(arg), "total_time": tt,
                          self.sensor_type: info_sensor}
                    info_pcpu.append(l1.copy())

                    time.sleep(idle_time)

                l2 = {"nthread": thr, "lpcpu": info_pcpu}
                info_threads.append(l2.copy())

            model = {"freq": f, "threads": info_threads}
            self.models.append(model.copy())

        self.save(save_name)
        self.cpu.reset()
        # cpu.set_governors("userspace")

    def run_dvfs(self, list_threads, list_args, idle_time, save_name, verbose= 0):
        try:
            self.cpu.reset()
            self.cpu.disable_hyperthread()
            self.cpu.set_governors("ondemand")
            cpus = self.cpu.get_online_cpus()
        except Exception as e:
            raise(Exception("Unable to control cpu", e))

        info_threads = []
        for thr in list_threads:
            try:
                self.cpu.reset()
                self.cpu.set_governors("ondemand")
                self.cpu.disable_cpu(cpus[thr:])
            except Exception as e:
                print("Unable to control frequency", e)
                raise(Exception("Unable to control frequency", e))
            info_pcpu = []
            for arg in list_args:
                arg = map(lambda s: str.replace(s, "_nt_", str(thr)), arg)
                print("Argumentos", arg)

                program = subprocess.Popen(["./"+str(self.program_name)]+arg)
                info_sensor = []
                ti = time.time()
                while program.poll() == None:
                    freqs = cpu.get_frequencies()
                    if verbose > 1:
                        print("Tempo", time.time()-ti, "Frequencia ", freqs, " nThreads", thr)
                    tg = time.time()
                    info = {"time": time.time()-ti, "freqs": list(freqs),
                            "sensor": self.sensor.get_data()}
                    info_sensor.append(info.copy())
                    
                    if verbose > 2:
                        self.sensor.print_data()
                    elif verbose > 1:
                        self.sensor.print_pot()

                    tg = time.time()-tg
                    if 1-tg >= 0:
                        time.sleep(1-tg)

                program.wait()
                tt = time.time()-ti
                if verbose > 0:
                    print("Tempo total", tt)

                l1 = {"arg": list(arg), "total_time": tt, self.sensor_type: info_sensor}
                info_pcpu.append(l1.copy())
                time.sleep(idle_time)

            l2 = {"nthread": thr, "lpcpu": info_pcpu}
            info_threads.append(l2.copy())

        if verbose > 0:
            print("Saving")
        self.models= info_threads
        self.save(save_name)
        
        self.cpu.reset()
        self.cpu.set_governors("ondemand")

    def save(self, save_name):
        try:
            import platform
            from datetime import datetime
            self.models[0]["header"]= {"kernel":platform.platform(), 
                                        "date":datetime.now().strftime("%I:%M%p on %B %d, %Y")}
            save_path = os.path.dirname(save_name)
            if not os.path.exists(save_path):
                os.makedirs(save_path)
            with open(save_name, "wb") as f:
                pickle.dump(self.models, f, pickle.HIGHEST_PROTOCOL)
        except Exception as e:
            print("Error on saving", e)


# args_black= [["_nt_","in_156K.txt","out_156K.txt"],\
# 	["_nt_","in_312K.txt","out_312K.txt"],\
# 	["_nt_","in_625K.txt","out_625K.txt"],\
# 	["_nt_","in_1M.txt","out_1M.txt"],\
# 	["_nt_","in_2M.txt","out_2M.txt"],\
# 	["_nt_","in_5M.txt","out_5M.txt"],\
# 	["_nt_","in_10M.txt","out_10M.txt"]]