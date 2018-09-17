from energyOptimal import plotData
from energyOptimal.powerModel import powerModel

def createPowerModel():
    pw_model= powerModel()
    pw_model.loadData(filename='data/power_model/ipmi_2-32_cpuload.pkl',verbose=0,load_sensors=False,
                        freqs_filter=list(range(1200000,2300000,100000)))
    pw_model.fit()
    pw_model.save('data/ipmi_2-32_cpuload.pw')
    error= pw_model.error()
    print("Power model constants, ", pw_model.power_model_x)
    print("Erro, ", error)

    return pw_model

def visualizePowerModel(pw_model):
    # Plot the measured values and the model
    est= pw_model.estimate(pw_model.frequencies, pw_model.threads)
    plotData.setProps(xlabel= "Frequencies (GHz)", ylabel= "Active Cores", zlabel= "Power (W)")
    plotData.plot3D(x=pw_model.frequencies, y=pw_model.threads, z=pw_model.powers, legend='Measurements')
    plotData.plot3D(x=pw_model.frequencies, y=pw_model.threads, z=est, points=False, legend='Model')
    plotData.savePlot(filename= 'pw_model.png', showLegend= True)
    plotData.plotShow(showLegend= True)

pw_model= createPowerModel()
visualizePowerModel(pw_model)