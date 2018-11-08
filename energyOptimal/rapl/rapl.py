from shutil import which
import subprocess
import time
import os

class RAPL:
	RAPL_ENERGY_DIR= '/sys/class/powercap/intel-rapl/intel-rapl:0/energy_uj'
		
	def __init__(self, name_):
		if os.stat(RAPL.RAPL_ENERGY_DIR):
			self.method= 'RAPL'
		elif which('scontrol'):
			self.method= 'SCONTROL'
		elif which('perf'):
			self.method= 'PERF'
		else:
			raise "Cant measure energy"
		self.name= name_
		self.data= []
		self.init_rapl= 0
		self.end_rapl= 0
	
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
	
	def start_en_rapl(self):
		self.init_rapl= float(open(RAPL.RAPL_ENERGY_DIR).read())
		return self.init_rapl

	def end_en_rapl(self):
		self.end_rapl= float(open(RAPL.RAPL_ENERGY_DIR).read())
		return self.end_rapl-self.init_rapl

	def get_data(self):
		if self.method == 'RAPL':
			return self.get_data_rapl()
		elif self.method == 'SCONTROL':
			return self.get_data_scontrol()
		elif self.method == 'PERF':
			raise 'Not implemented'

	def print_data(self):
		print("Power consumption", self.data)
	
	def print_pot(self):
		print("Power consumption", self.data)
