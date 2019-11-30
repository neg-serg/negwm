CFLAGS += -std=gnu11 -march=native -Os -pedantic
GLFW3 := $(shell pkg-config --libs glfw3)
LIBS := $(GLFW3) -lGL -lm -lGLU -lGLEW

.PHONY: all

all: wm_class send
generate: clean
clean: 
	@rm -rfv wm_class send

wm_class: wm_class.c
	$(CC) $(CFLAGS) -lX11 $@.c -o $@ -Os -s
	strip $@

send: send.c
	$(CC) $(CFLAGS) $@.c -lbsd -o $@ -Os -s
	strip $@
