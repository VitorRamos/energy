
.SUFFIXES:
.SUFFIXES: .c .cpp

CC = gcc
CXX = g++
LIBS=-lpthread -fopenmp

.c:
	$(CC) $< $(LIBS) -lm -o $@

.cpp:
	$(CXX) $< $(LIBS) -o $@

all: cpu_load cpubound3 blackscholes

clean:
	rm *.o cpu_load cpubound3 blackscholes