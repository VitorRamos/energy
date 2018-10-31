
all: hello papi event teste_ld teste_static

hello: hello.asm
	 nasm -f elf64 hello.asm -o hello.o && ld hello.o -o hello

papi: papi.cpp
	g++ papi.cpp -lpapi -o papi_perf

event: event.cpp
	g++ event.cpp -o event_perf

teste_ld: teste.cpp
	g++ teste.cpp -o teste

teste_static: teste.cpp
	g++ -static teste.cpp -o teste