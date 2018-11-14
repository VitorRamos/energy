CXX=g++
LIBS=libpapi.a

all: pmcs
pmcs: pmcs.o
	$(CXX) $< $(LIBS) -o $@
pmcs.o: pmcs.cpp

clean:
	rm *.o pmcs