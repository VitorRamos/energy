import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D

fig = plt.figure()
ax = fig.gca(projection='3d')

def plot3D(x, y, z, points=True):
    z= np.reshape(z, (len(x), len(y)))

    X = np.arange(0, len(x), 1)
    Y = np.arange(0, len(y), 1)
    X, Y = np.meshgrid(X, Y)
    Z = z[X, Y]

    if points:
        surf = ax.scatter(X, Y, Z, antialiased=True, color='r')
    else:
        surf = ax.plot_wireframe(X, Y, Z, antialiased=True)

    ax.set_xlabel('Frequency (GHz)', fontsize=10)
    ax.set_xticks(np.arange(0, len(x), 2))
    ax.set_xticklabels(x[::2], fontsize=10)

    ax.set_ylabel('Active cores', fontsize=10)
    ax.set_yticks(np.arange(0, len(y), 2))
    ax.set_yticklabels(y[::2], fontsize=10)

def plotShow():
    plt.show()