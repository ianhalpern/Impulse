#make:
#	gcc -I./pulseaudio/pulseaudio-0.9.10/ pacat.c -g -O2 -std=gnu99 -Wall -W -Wextra -pedantic -pipe -Wformat -Wold-style-definition -Wdeclaration-after-statement -Wfloat-equal -Wmissing-declarations -Wmissing-prototypes -Wstrict-prototypes -Wredundant-decls -Wmissing-noreturn -Wshadow -Wendif-labels -Wpointer-arith -Wcast-align -Wwrite-strings -Winline -Wno-unused-parameter -ffast-math -lpulse

make:
	#python setup.py build
	gcc -pthread -fno-strict-aliasing -DNDEBUG -g -fwrapv -O2 -Wall -Wstrict-prototypes -fPIC -I/usr/include/python2.5 -c src/cimpulsemodule.c -o src/cimpulsemodule.o
	gcc -pthread -lpulse -lfftw3 -shared -Wl,-O1 -Wl,-Bsymbolic-functions src/cimpulsemodule.o -o cimpulse.so
	rm src/cimpulsemodule.o

