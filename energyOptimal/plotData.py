import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.widgets import Slider
from matplotlib.ticker import FormatStrFormatter

fig = plt.figure()
ax = fig.gca(projection='3d')
legends= []

axInput = None
sin= None

def new_figure():
    global fig, ax, legends
    fig = plt.figure()
    ax = fig.gca(projection='3d')
    legends= []

def setProps(xlabel='', ylabel='', zlabel='', title='', fontsize=10):
    ax.set_title(title)
    ax.set_xlabel(xlabel, fontsize=fontsize)
    ax.set_ylabel(ylabel, fontsize=fontsize)
    ax.set_zlabel(zlabel, fontsize=fontsize)

def update_user(val):
    pass

def update_data(val):
    ax.clear()
    d = int(val)
    sin.val = d
    sin.poly.xy[2] = sin.val, 1
    sin.poly.xy[3] = sin.val, 0
    sin.valtext.set_text(sin.valfmt % sin.val)

    update_user(val)

    fig.canvas.draw_idle()

def createSlider(label_, valmin_, valmax_, valinit_=None):
    global sin, axInput
    if valinit_ == None: valinit_= valmin_
    axInput= plt.axes([0.25, 0.0, 0.65, 0.03], facecolor='lightgoldenrodyellow')
    sin = Slider(ax=axInput, label=label_, valmin=valmin_, valmax=valmax_, valinit=valinit_)
    sin.on_changed(update_data)
    update_data(valmin_)

def plot3D(x, y, z, legend='', points=True, color_='black'):
    z= np.reshape(z, (len(x), len(y)))
    X = np.arange(0, len(x), 1)
    Y = np.arange(0, len(y), 1)
    X, Y = np.meshgrid(X, Y)
    Z = z[X, Y]
    X, Y = np.meshgrid(x, y)

    if points:
        ax.scatter(X, Y, Z, antialiased=True, color=color_)
    else:
        ax.plot_wireframe(X, Y, Z, antialiased=True, color=color_)

    ax.xaxis.set_major_formatter(FormatStrFormatter('%.2f'))
    ax.set_xticks(x[::2])#np.arange(0, len(x), 2))
    # ax.set_xticklabels(x[::2], fontsize=10)

    ax.yaxis.set_major_formatter(FormatStrFormatter('%.2f'))
    ax.set_yticks(y[::2])#np.arange(0, len(y), 2))
    # ax.set_yticklabels(y[::2], fontsize=10)

    if legend:
        legends.append(legend)
        ax.legend(legends)

def plotShow(showLegend= False):
    if showLegend: ax.legend(legends)
    plt.show()

def savePlot(filename, showLegend= False):
    if showLegend: ax.legend(legends)
    plt.tight_layout()
    plt.savefig(filename)
    ax.clear()