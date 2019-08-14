from energyOptimal.performanceModel import performanceModel
from scipy.optimize import least_squares, nnls
import _pickle as pickle
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import pyplot as plt

parsecapps=['completo_black_5.pkl','completo_canneal_2.pkl','completo_dedup_3.pkl',
            'completo_ferret_3.pkl','completo_fluid_3.pkl',
            'completo_rtview_3.pkl','completo_swaptions_2.pkl','completo_vips_3.pkl',
            'completo_x264_3.pkl','completo_xhpl.pkl','completo_openmc_kernel_novo.pkl',
            'completo_bodytrack_1.pkl']
titles=['Blackscholes','Canneal','Dedup',
        'Ferret','Fluidanimate',
        'Raytrace','Swaptions','Vips',
        'x264','HPL','Openmc',
        'Bodytrack']
fmax= 2.2
tmax= 16

for p,title in zip(parsecapps,titles):
    if not "rt" in p: continue

    fig = plt.figure()
    ax = fig.gca(projection='3d')

    var= "energy"
    f= open("data/dataframes/"+p,"rb")
    data= pickle.load(f)
    data= data[data["in_cat"]==3]
    data= data[["freq","thr","time","energy"]]
    data= data[data["thr"]<=16]
    data[var]= data[var]/data[var].max()

    # data= data[data["thr"].isin([1,2,4,8,16])]
    # data= data[data["freq"].isin([1.3, 1.5, 1.7, 1.9, 2.1])]

    train_data= data
    train_data= train_data.query(" (freq == 1.3 and thr == 1) or (freq == 2.1 and thr == 16) ")
    # train_data= train_data[train_data["thr"].isin([1,16])]
    # train_data= train_data[train_data["freq"].isin([1.3])]
    print(train_data)
    # train_data= data[data["thr"].isin( [data["thr"].min(), data["thr"].max()] )]
    # train_data= train_data[train_data["freq"].isin( [data["freq"].min(), data["freq"].max()] )]
    # print(train_data)

    if var == "energy":
        err= lambda x,f,p,y: x[0]*(( (0.29*f**3+0.97*f)*p+198 )*( x[4]/p-x[4]+1 ))/f-y
        x0= [1,0.29,0.97,198,0.5]
        # err= lambda x,f,p,y: x[0]*(( (x[1]*f**3+x[2]*f)*p+x[3] )*( x[4]/p-x[4]+1 ))/f-y
        # x0= [1,0.29,0.97,198,0.5]
    elif var == "time":
        err= lambda x,f,p,y: x[0]*( x[1]/p-x[1]+1 )/f-y
        x0= [1,1]

    res_robust= least_squares(err, x0, loss='soft_l1',
        f_scale=1,
        #bounds= ( [0, 0, 0, 0, 0], [np.inf, np.inf, np.inf, np.inf, 1] ),
        args=(train_data["freq"], train_data["thr"], train_data[var]))

    xs= res_robust.x
    # print(p, xs)
    if var == "energy":
        t= lambda f,p: xs[0]*(( (xs[1]*f**3+xs[2]*f)*p+xs[3] )*( xs[4]/p-xs[4]+1 ))/f
    elif var == "time":
        t= lambda f,p: xs[0]*( xs[1]/p-xs[1]+1 )/f
    # var="energy"
    # t= lambda f,p: xs[0]*( xs[1]/p-xs[1]+1 )/f*((0.29*f**3+0.97*f)*p+198)

    # LIENAR LEATS SQUARES
    f= train_data["freq"]
    p_= train_data["thr"]
    A= np.hstack( (f**2*p_, 1/(f*p_), f**2, p_, 1/f, np.ones(f.shape)) ).reshape((-1,6),order='F')
    b= train_data["energy"]
    # reslin= [[0.01421882712431667, 653.072187564777, 0.9565198706756833, 0.04755952520892127, 9.708026795223106, 3.199394050191078]]
    # reslin= [np.dot(np.dot(np.linalg.inv(np.dot(A.T,A)),A.T),b)]
    reslin= np.linalg.lstsq(A,b,rcond=None)
    tlin= lambda x,f,p: x[0]*f**2*p+x[1]/(f*p)+x[2]*f**2+x[3]*p+x[4]/f+x[5]
    
    data= data.sort_values(["freq","thr"])
    x1= np.arange(1.2,fmax,0.1)
    x2= np.arange(1,tmax+1,1)
    X,Y= np.meshgrid(x1,x2)
    Z1= t(X,Y)
    # Z1= tlin(reslin[0],X,Y)
    ax.plot_wireframe(X, Y, Z1, antialiased=True, color="r", label="Equation")


    x, y= data["freq"].unique(), data["thr"].unique()
    z= np.reshape(data[var].values, (len(x), len(y)))
    X = np.arange(0, len(x), 1)
    Y = np.arange(0, len(y), 1)
    X, Y = np.meshgrid(X, Y)
    Z = z[X, Y]
    # X, Y = np.meshgrid(x, y)
    ax.scatter(data["freq"], data["thr"], data[var], antialiased=True, color="b", label="Measurements")


    x1= data["freq"].unique() #np.arange(1.2,fmax,0.1)
    x2= data["thr"].unique()#np.arange(1,tmax+1,1)
    X,Y= np.meshgrid(x1,x2)
    Z1= t(X,Y)
    print(p, np.sum(np.abs(Z1-Z)/Z)*100/Z.size, np.sum((Z1-Z)**2)/Z.size )
    # Z1= tlin(reslin[0],X,Y)
    # print(p, np.sum((Z1-Z)/Z)*100/Z.size, np.sum((Z1-Z)**2)/Z.size )


    # x, y= train_data["freq"].unique(), train_data["thr"].unique()
    # z= np.reshape(train_data[var].values, (len(x), len(y)))
    # X = np.arange(0, len(x), 1)
    # Y = np.arange(0, len(y), 1)
    # X, Y = np.meshgrid(X, Y)
    # Z = z[X, Y]
    # X, Y = np.meshgrid(x, y)
    ax.scatter(train_data["freq"], train_data["thr"], train_data[var], color="black", label="TrainData",s=100)

    ax.set_xlabel('Frequency (GHz)',fontsize=12)
    ax.set_ylabel('Cores', fontsize=12)
    ax.set_zlabel(var, fontsize=12)
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.title(title,fontsize=16,loc='left')
    ax.legend(loc='upper right',fontsize=12) # bbox_to_anchor=(1.2,0.55)
    ax.view_init(30,60)
    if 'hpl' in p:
        ax.set_zlim(np.min(Z),15)
    plt.tight_layout()
    plt.show()
    # plt.savefig("%s.png"%(title.lower()))
