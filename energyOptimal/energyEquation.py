from scipy.optimize import *
from performanceModel import performanceModel

class Equation:
    # with Victor hugo model
    # @staticmethod
    # parallel_eq= lambda x,p,N: x[0]+x[1]/p+x[2]*x[3]**N
    # def parallel_eq(x,p,N):
    #     z= x[0]+x[1]/p+x[2]*x[3]**N
    #     z[z<0]= 0
    #     z[z>1]= 1
    #     return z
    # pw_eq= lambda x,f,p: (x[0]*f**3+x[1]*f)*p+x[2]
    # over_eq= lambda x,p,N: x[0]+(x[1]*p)/x[2]**N
    # perf_eq= lambda x,N,f,p: (x[0]*p-Equation.parallel_eq(x[1:],p,N)*(p-1)+Equation.over_eq(x[5:],p,N)*p)/(f*p)
    # en_eq= lambda x,N,f,p: Equation.pw_eq(x,f,p)*Equation.perf_eq(x[3:],N,f,p)
    # err_eq= lambda x,N,f,p,y: Equation.en_eq(x,N,f,p)-y

    pw_eq= lambda x,f,p: (x[0]*f**3+x[1]*f)*p+x[2]
    perf_eq= lambda x,N,f,p: N**x[3]*(x[0]*p-x[1]*(p-1))/(f*p)
    # en_eq= lambda x,N,f,p: Equation.pw_eq(x,f,p)*Equation.perf_eq(x[3:],N,f,p)
    # err_eq= lambda x,N,f,p,y: Equation.en_eq(x,N,f,p)-y
    en_eq= lambda x,N,f,p: (x[0]*f**2*p+x[1]/(f*p)*N**x[7]+x[2]*f**2+x[3]*p+x[4]/f*N**x[6]+x[5])
    err_eq= lambda x,N,f,p,y: Equation.en_eq(x,N,f,p)-y

    def __init__(self):
        self.xs= np.ones(8)

    def fit(self, X, y):
        res= least_squares(Equation.err_eq, self.xs,  loss='soft_l1',
                            f_scale=0.1, args=(X[:,0],X[:,1],X[:,2],y))
        self.xs= res.x

        # Using search algorithms optimizing for the squared error
        # def optimizer(x,fuc,args,y):
        #     return np.sum(np.abs(fuc(x,*args)-y)/y)
        # to_opt= lambda x: optimizer(x,Equation.en_eq,args=(X[:,0],X[:,1],X[:,2]),y=y)
        # lw = [-100]*8
        # up = [100]*8
        # res= dual_annealing(to_opt,bounds=list(zip(lw,up)))
        # res= basinhopping(to_opt,self.x0,niter=1)

        # methods= ['Nelder-Mead', 'Powell' , 'CG' , 'BFGS' , 
        # 'L-BFGS-B', 'TNC' , 'COBYLA', 
        # 'SLSQP' , 'trust-constr' ]
        # for m in methods:
        #     res= minimize(to_opt,[1]*8,method=m)
        #     print(m, optimizer(res.x,Equation.en_eq,args=(X[:,0],X[:,1],X[:,2]),y=y))
        # self.xs= res.x

    def predict(self, X):
        return Equation.en_eq(self.xs, X[:,0],X[:,1],X[:,2])
    

class equationModel:
    def __init__(self, perf_model):
        self.model= Equation()
        self.perf_model= perf_model
        self.model.fit(self.perf_model.dataFrame[["in_cat","freq","thr"]].values, self.perf_model.dataFrame["energy"].values)
        self.dataframe= self.perf_model.dataFrame
        self.dataframe["energy_equation"]= self.model.predict(self.perf_model.dataFrame[["in_cat","freq","thr"]].values)