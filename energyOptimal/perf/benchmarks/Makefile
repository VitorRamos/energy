all: hello simple_dynamic_ld simple_static_ld

hello: hello.asm
	 nasm -f elf64 hello.asm -o hello.o && ld hello.o -o hello
	
simple_dynamic_ld: simple_loop.cpp
	g++ simple_loop.cpp -o simple_dynamic_ld

simple_static_ld: simple_loop.cpp
	g++ -static simple_loop.cpp -o simple_static_ld

clean:
	rm *.o hello simple_dynamic_ld simple_static_ld