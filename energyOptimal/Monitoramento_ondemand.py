from .rapl import RAPL
from .ipmi import IPMI
from .cpufreq import CPUFreq

import subprocess
import threading
import pickle
import time
import os

class programa(threading.Thread):
        def __init__(self, program_, args_):
                threading.Thread.__init__(self)
                self.args= args_
                self.program= program_

        def run(self):
                print( ["./"+str(self.program)]+self.args)
                subprocess.call(["./"+str(self.program)]+self.args)

def save_data(name, data):
		with open("data/"+ name +".pkl","wb") as f:
			pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)


def monitoring(program_name, list_threads, list_args, idle_time, sensor_type):
	if sensor_type =="rapl":
		sensor= RAPL("service1")
	if sensor_type =="ipmi":
		sensor= IPMI("http://localhost:8081")

	cpu= CPUFreq()
	for xcpu in range(1,64):
		cpu.enable_cpu(xcpu)

#	cpu.change_governo("ondemand")
#	cpu.change_max_frequency("2301000")
	for xcpu in range(32,64):
                cpu.disable_cpu(xcpu)
	models= []
	try:
		info_threads= []
		for thr in list_threads:
			for xcpu in range(thr,32):
				cpu.disable_cpu(xcpu)
			info_pcpu= []
			for arg in list_args:
#				arg[0]= str(thr)
				arg= map(lambda s: str.replace(s,"_nt_", str(thr)), arg)
				print("Argumentos", arg)
				program= programa(program_name,arg)
				program.start()
				info_sensor= []
				ti = time.time()
				while program.is_alive():
					freqs= []
					for xcpu in range(0, thr):
						freqs.append(cpu.get_current_frequencies(xcpu))
					print("Tempo", time.time()-ti, "Frequencia ", freqs, " nThreads", thr)
					tg= time.time()
					info= {"time": time.time()-ti,"freqs":list(freqs),"sensor":sensor.get_data()}
					info_sensor.append(info.copy())
#					sensor.print_data()
					sensor.print_pot()
					tg= time.time()-tg
					if 1-tg >= 0:
						time.sleep(1-tg)
				tt= time.time()-ti
				program.join()
				print("Tempo total", tt)
				l1= {"arg":list(arg),"total_time":tt, sensor_type:info_sensor}
				info_pcpu.append(l1.copy())
				time.sleep(idle_time)

			for xcpu in range(1,32):
				cpu.enable_cpu(xcpu)
#			cpu.change_governo("ondemand")
#			cpu.change_max_frequency("2301000")
			l2= {"nthread":thr,"lpcpu":info_pcpu}
			info_threads.append(l2.copy())
	except Exception as e:
		print( e)

#	save_data("teste_ondemand", info_threads)
	print("Saving")
	save_data("completo_"+program_name+"_ondemand", info_threads)
	for xcpu in range(1,64):
		cpu.enable_cpu(xcpu)
	cpu.change_governo("ondemand")

# args_black= [["_nt_","in_156K.txt","out_156K.txt"],\
# 	["_nt_","in_312K.txt","out_312K.txt"],\
# 	["_nt_","in_625K.txt","out_625K.txt"],\
# 	["_nt_","in_1M.txt","out_1M.txt"],\
# 	["_nt_","in_2M.txt","out_2M.txt"],\
# 	["_nt_","in_5M.txt","out_5M.txt"],\
# 	["_nt_","in_10M.txt","out_10M.txt"]]

args_rtview= [["thai_statue.obj","-automove","-nthreads","_nt_","-frames","10000","-res","100","100"],\
        ["thai_statue.obj","-automove","-nthreads","_nt_","-frames","10000","-res","140","140"],\
        ["thai_statue.obj","-automove","-nthreads","_nt_","-frames","10000","-res","196","196"],\
        ["thai_statue.obj","-automove","-nthreads","_nt_","-frames","10000","-res","274","274"],\
        ["thai_statue.obj","-automove","-nthreads","_nt_","-frames","10000","-res","384","384"],\
        ["thai_statue.obj","-automove","-nthreads","_nt_","-frames","10000","-res","537","537"]]
args_black=\
[\
    ["__nt__","in_5_10.txt","output.txt"],\
    ["__nt__","in_6_10.txt","output.txt"],\
    ["__nt__","in_7_10.txt","output.txt"],\
    ["__nt__","in_8_10.txt","output.txt"],\
    ["__nt__","in_9_10.txt","output.txt"]]
args_canneal=\
[\
	["__nt__","15000","2000","2500000.nets","128"],\
	["__nt__","15000","2000","2500000.nets","256"],\
	["__nt__","15000","2000","2500000.nets","384"],\
	["__nt__","15000","2000","2500000.nets","512"],\
	["__nt__","15000","2000","2500000.nets","640"]]
args_dedup=\
[\
	["-c","-p","-v","-t","__nt__","-i","FC-6-x86_64-disc1_05.iso","-o","output.dat.ddp"],\
	["-c","-p","-v","-t","__nt__","-i","FC-6-x86_64-disc1_06.iso","-o","output.dat.ddp"],\
	["-c","-p","-v","-t","__nt__","-i","FC-6-x86_64-disc1_07.iso","-o","output.dat.ddp"],\
	["-c","-p","-v","-t","__nt__","-i","FC-6-x86_64-disc1_08.iso","-o","output.dat.ddp"],\
	["-c","-p","-v","-t","__nt__","-i","FC-6-x86_64-disc1_09.iso","-o","output.dat.ddp"]]
args_ferret=\
[\
	["corel_5","lsh","queries_5","10","20","__nt__","output.txt"],\
	["corel_6","lsh","queries_6","10","20","__nt__","output.txt"],\
	["corel_7","lsh","queries_7","10","20","__nt__","output.txt"],\
	["corel_8","lsh","queries_8","10","20","__nt__","output.txt"],\
	["corel_9","lsh","queries_9","10","20","__nt__","output.txt"]]
args_fluid=\
[\
	["__nt__","200","in_500K.fluid","out.fluid"],\
	["__nt__","300","in_500K.fluid","out.fluid"],\
	["__nt__","400","in_500K.fluid","out.fluid"],\
	["__nt__","500","in_500K.fluid","out.fluid"],\
	["__nt__","600","in_500K.fluid","out.fluid"]]
args_freq=\
[\
	["webdocs_250k_05.dat","1100"],\
	["webdocs_250k_06.dat","1100"],\
	["webdocs_250k_07.dat","1100"],\
	["webdocs_250k_08.dat","1100"],\
	["webdocs_250k_09.dat","1100"]]
args_rtview=\
[\
	["thai_statue.obj","-automove","-nthreads","__nt__","-frames","10000","-res","100","100"],\
	["thai_statue.obj","-automove","-nthreads","__nt__","-frames","10000","-res","200","200"],\
	["thai_statue.obj","-automove","-nthreads","__nt__","-frames","10000","-res","300","300"],\
	["thai_statue.obj","-automove","-nthreads","__nt__","-frames","10000","-res","400","400"],\
	["thai_statue.obj","-automove","-nthreads","__nt__","-frames","10000","-res","500","500"]]
args_swap=\
[\
	["-ns","32","-sm","2000000","-nt","__nt__"],\
	["-ns","32","-sm","3000000","-nt","__nt__"],\
	["-ns","32","-sm","4000000","-nt","__nt__"],\
	["-ns","32","-sm","5000000","-nt","__nt__"],\
	["-ns","32","-sm","6000000","-nt","__nt__"]]
args_vips=\
[\
	["im_benchmark","orion_10800x10800.v","output.v"],\
	["im_benchmark","orion_12600x12600.v","output.v"],\
	["im_benchmark","orion_14400x14400.v","output.v"],\
	["im_benchmark","orion_16200x16200.v","output.v"],\
	["im_benchmark","orion_18000x18000.v","output.v"]]
args_x264=\
[\
	["--quiet","--qp","20","--partitions","b8x8,i4x4","--ref","5","--direct","auto","--b-pyramid","--weightb","--mixed-refs","--no-fast-pskip","--me","umh","--subme","7","--analyse","b8x8,i4x4","--threads","__nt__","-o","eledream.264","eledream_1920x1080_512.y4m"],\
	["--quiet","--qp","20","--partitions","b8x8,i4x4","--ref","5","--direct","auto","--b-pyramid","--weightb","--mixed-refs","--no-fast-pskip","--me","umh","--subme","7","--analyse","b8x8,i4x4","--threads","__nt__","-o","eledream.264","eledream_1920x1080_459.y4m"],\
	["--quiet","--qp","20","--partitions","b8x8,i4x4","--ref","5","--direct","auto","--b-pyramid","--weightb","--mixed-refs","--no-fast-pskip","--me","umh","--subme","7","--analyse","b8x8,i4x4","--threads","__nt__","-o","eledream.264","eledream_1920x1080_408.y4m"],\
	["--quiet","--qp","20","--partitions","b8x8,i4x4","--ref","5","--direct","auto","--b-pyramid","--weightb","--mixed-refs","--no-fast-pskip","--me","umh","--subme","7","--analyse","b8x8,i4x4","--threads","__nt__","-o","eledream.264","eledream_1920x1080_357.y4m"],\
	["--quiet","--qp","20","--partitions","b8x8,i4x4","--ref","5","--direct","auto","--b-pyramid","--weightb","--mixed-refs","--no-fast-pskip","--me","umh","--subme","7","--analyse","b8x8,i4x4","--threads","__nt__","-o","eledream.264","eledream_1920x1080_306.y4m"]]
args_xhpl= [['_nt_','7000'],\
        ['_nt_','8000'],\
        ['_nt_','9000'],\
        ['_nt_','10000'],\
        ['_nt_','11000']]
args_openmc= [['input1'],\
        ['input2'],\
        ['input3'],\
        ['input4'],\
        ['input5']]

monitoring(program_name='openmc', list_threads= [1]+[2*x for x in range(1,17)], list_args=args_openmc, idle_time= 30, sensor_type= 'ipmi')
monitoring(program_name='xhpl.sh',list_threads= [1]+[2*x for x in range(1,17)], list_args=args_xhpl, idle_time= 30, sensor_type= 'ipmi')
monitoring(program_name="canneal",list_threads= [1]+[2*x for x in range(1,17)], list_args= args_canneal, idle_time= 30, sensor_type="ipmi")
monitoring(program_name="dedup",list_threads= [1]+[2*x for x in range(1,17)], list_args= args_dedup, idle_time= 30, sensor_type="ipmi")
monitoring(program_name="ferret",list_threads= [1]+[2*x for x in range(1,17)], list_args= args_ferret, idle_time= 30, sensor_type="ipmi")
monitoring(program_name="vips",list_threads= [1]+[2*x for x in range(1,17)], list_args= args_vips, idle_time= 30, sensor_type="ipmi")
monitoring(program_name="x264",list_threads= [1]+[2*x for x in range(1,17)], list_args= args_x264, idle_time= 30, sensor_type="ipmi")
monitoring(program_name="blackscholes",list_threads= [1]+[2*x for x in range(1,17)], list_args= args_black, idle_time= 30, sensor_type="ipmi")
monitoring(program_name="fluidanimate",list_threads= [1,2,4,8,16,32], list_args= args_fluid, idle_time= 30, sensor_type="ipmi")
monitoring(program_name="rtview",list_threads= [1]+[2*x for x in range(1,17)], list_args= args_rtview, idle_time= 30, sensor_type="ipmi")
monitoring(program_name="swaptions",list_threads= [1]+[2*x for x in range(1,17)], list_args= args_swap, idle_time= 30, sensor_type="ipmi")
monitoring(program_name="freqmine",list_threads= [1]+[2*x for x in range(1,17)], list_args= args_freq, idle_time= 30, sensor_type="ipmi")