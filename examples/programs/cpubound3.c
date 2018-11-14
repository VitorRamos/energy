#include<stdlib.h>
#include<stdio.h>
#include<sys/time.h>
#include<math.h>

double convert_time_to_sec(struct timeval tv){
    double elapsed_time = (double)(tv.tv_sec) + ((double)(tv.tv_usec)/1000000);
    return elapsed_time;
}

int main(int argc, const char* argv[] ){
    float result = 0;
    unsigned int nthreads;
    unsigned long long i,niter,npiter,nsiter;
    float fparallel;
    double start, end;
    struct timeval tvs,tve;
    
    nthreads = atoi(argv[1]);
    niter = atoll(argv[2]);
    fparallel = atof(argv[3]);
    npiter = niter*fparallel;
    nsiter = niter-npiter;
//     printf("Initializing %d threads to deal with %lld iterations, being %lld in parallel\n",nthreads,niter,npiter);
    gettimeofday(&tvs, NULL);
    #pragma omp parallel num_threads(nthreads)
    {
        #pragma omp for reduction(+:result)
        for(i=0;i<npiter;i++){
            result+=sqrt(i);
        }
        #pragma omp for reduction(+:result)
        for(i=0;i<nsiter;i++){
            #pragma omp critical
                result+=sqrt(i);
        }
    }
    gettimeofday(&tve, NULL);
    start = convert_time_to_sec(tvs);
    end = convert_time_to_sec(tve);
    printf("%d,%.4f,%.4lf,%.4lf,%.4lf\n",nthreads,fparallel,start,end,end-start);
    return(result);
}