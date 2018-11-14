#include <pthread.h>
#include <pthread.h>
#include <cstdlib>
#include <iostream>
#include <sys/time.h>
#include <unistd.h>
#include <math.h>

using namespace std;

bool shut= false;

void *idle(void *arg)
{
	long n= (long)arg;
//    cout << "Thread " << n << endl;
	double res= 0, i=0;
    while(!shut)
	{
		res+=sqrt(i)*sqrt(i);
		i++;
	}
}

int main(int argc, char** argv)
{
	int n= 1;
	float tempo_total= 0;
	if(argc == 3){
		n= atoi(argv[1]);
		tempo_total= atof(argv[2]);
	}
	n-=1;
    pthread_t th[n];

//    cout << "In main: creating thread" << endl;
	for(int i=0; i<n; i++)
        pthread_create(&th[i], NULL, &idle, (void*)(long)i);

	double diff_t;
	timeval t1, t2;
	gettimeofday(&t1, NULL);
	while(diff_t<tempo_total)
	{
		gettimeofday(&t2, NULL);
		diff_t = (t2.tv_sec - t1.tv_sec)+(t2.tv_usec - t1.tv_usec)/1000000.0;
		double res= 0, i=0;
		res+=sqrt(i)*sqrt(i);
	}
	shut= true;

	for(int i=0; i<n; i++)
        pthread_join(th[i], NULL);
	return 0;
}
