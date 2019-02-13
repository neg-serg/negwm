CFLAGS += -std=gnu11 -march=native -Os -pedantic -D_FORCE_OCLOEXEC
GLFW3 := $(shell pkg-config --libs glfw3)
LIBS := $(GLFW3) -lGL -lm -lGLU -lGLEW

.PHONY: all

all:  \
	wm_class \
	send

generate: clean

clean:
	@rm -rfv \
	    wm_class \
	    send

wm_class: wm_class.c
	$(CC) $(CFLAGS) -lX11 $@.c -o $@

send: send.c
	$(CC) $(CFLAGS) $@.c -o $@

