CC=g++
 
all: cache_test list_events papi_rapl read_rapl sample_teste

papi_rapl: papi_rapl.cpp
	g++ papi_rapl.cpp libpapi.a -o papi_rapl

cache_test: cache_test.o
cache_test.o: cache_test.cpp

list_events: list_events.o
	$(CC) $< -lpfm -o $@
list_events.o: list_events.cpp

read_rapl: read_rapl.o
read_rapl.o: read_rapl.c

sample_teste: sample_teste.o
	$(CC) $< -lpfm -o $@
sample_teste.o: sample_teste.cpp

clean:
	rm *.o
	rm cache_test list_events papi_rapl read_rapl sample_teste