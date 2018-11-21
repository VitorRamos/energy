CC=g++

all: myperf

myperf: myperf.o rapl.o event_group.o event_single.o list_events.o
	$(CC) $^ -lpfm -o $@
myperf.o: myperf.cpp
rapl.o: rapl.cpp
event_group.o: event_group.cpp
event_single.o: event_single.cpp
list_events.o: list_events.cpp

clean:
	rm *.o