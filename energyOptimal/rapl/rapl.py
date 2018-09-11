import subprocess

class RAPL:
	def __init__(self, name_):
		self.name= name_
		self.data= []
	
	def get_data(self):
		data= subprocess.check_output(["scontrol","show","node", self.name])
		try:
			currentWatts= data.split("\n")[8].split("")[3].split("=")[1]
			self.data= currentWatts
			return currentWatts
		except:
			print("Erro ao ler do slurm")
			print(data)
			return 0
	
	def print_data(self):
		print("Consumo potencia", self.data)
