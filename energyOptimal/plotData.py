import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D

fig = plt.figure()
ax = fig.gca(projection='3d')
legends= []

def setProps(xlabel='', ylabel='', zlabel='', title=''):
    plt.title(title)
    ax.set_xlabel(xlabel, fontsize=10)
    ax.set_ylabel(ylabel, fontsize=10)
    ax.set_zlabel(zlabel, fontsize=10)

def plot3D(x, y, z, legend='', points=True):

    z= np.reshape(z, (len(x), len(y)))
    X = np.arange(0, len(x), 1)
    Y = np.arange(0, len(y), 1)
    X, Y = np.meshgrid(X, Y)
    Z = z[X, Y]

    if points:
        surf = ax.scatter(X, Y, Z, antialiased=True, color='b')
    else:
        surf = ax.plot_wireframe(X, Y, Z, antialiased=True, color='black')
    
    ax.set_xticks(np.arange(0, len(x), 2))
    ax.set_xticklabels(x[::2], fontsize=10)

    ax.set_yticks(np.arange(0, len(y), 2))
    ax.set_yticklabels(y[::2], fontsize=10)

    legends.append(legend)

def plotShow(showLegend= False):
    if showLegend: plt.legend(legends)
    plt.show()

def savePlot(filename, showLegend= False):
    if showLegend: plt.legend(legends)
    plt.tight_layout()
    plt.savefig(filename)