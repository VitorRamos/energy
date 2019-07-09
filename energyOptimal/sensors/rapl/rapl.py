from shutil import which
import subprocess
import time
import os

class RAPL:
	RAPL_ENERGY_DIR= '/sys/class/powercap/intel-rapl/intel-rapl:0/energy_uj'
	PKG_ENERGY_SCALE= 2.3283064365386962890625e-10
		
	def __init__(self, name_=None, method=None):

		if method == None:
			if os.stat(RAPL.RAPL_ENERGY_DIR):
				self.method= 'RAPL'
			elif which('scontrol') and name_ is not None:
				self.method= 'SCONTROL'
			else:
				self.method= 'PERF'
		else:
			self.method= method
		
		if method == 'PERF':
			import profiler
			try:
				self.prof= profiler.Profiler(events_groups=[["SYSTEMWIDE:RAPL_ENERGY_PKG"]])
				self.prof.start_counters(0)
			except:
				raise "Cant measure energy"

		self.sensor_name= name_ if name_ is not None else "rapl"
		self.data= []
		self.init_rapl= 0
		self.end_rapl= 0
		self.init_perf= 0
		self.end_perf= 0
	
	def get_data_scontrol(self):
		data= subprocess.check_output(["scontrol","show","node", self.name])
		try:
			currentWatts= data.split("\n")[8].split("")[3].split("=")[1]
			self.data= currentWatts
			return currentWatts
		except:
			print("Erro ao ler do slurm")
			print(data)
			return 0
	
	def get_data_rapl(self):
		val= float(open(RAPL.RAPL_ENERGY_DIR).read())
		time.sleep(0.1)
		val= float(open(RAPL.RAPL_ENERGY_DIR).read())-val
		self.data= val/1e6/0.1
		return self.data
	
	def get_data_perf(self):
		val= self.prof.read_events()[0]
		time.sleep(0.1)
		val= self.prof.read_events()[0]-val
		self.data= val*RAPL.PKG_ENERGY_SCALE/0.1
		return self.data
	
	def start_en_rapl(self):
		self.init_rapl= float(open(RAPL.RAPL_ENERGY_DIR).read())
		return self.init_rapl

	def end_en_rapl(self):
		self.end_rapl= float(open(RAPL.RAPL_ENERGY_DIR).read())
		return (self.end_rapl-self.init_rapl)/1e6

	def start_en_perf(self):
		self.init_perf= self.prof.read_events()[0]
		return self.init_perf
	
	def end_en_perf(self):
		self.end_perf= self.prof.read_events()[0]
		return (self.end_perf-self.init_perf)*RAPL.PKG_ENERGY_SCALE

	def get_data(self):
		if self.method == 'RAPL':
			return self.get_data_rapl()
		elif self.method == 'SCONTROL':
			return self.get_data_scontrol()
		elif self.method == 'PERF':
			return self.get_data_perf()

	def print_data(self):
		print("Power consumption", self.data)
	
	def print_pot(self):
		print("Power consumption", self.data)
