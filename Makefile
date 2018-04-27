CFLAGS += -std=gnu11 -march=native -Os -pedantic -D_FORCE_OCLOEXEC
GLFW3 := $(shell pkg-config --libs glfw3)
LIBS := $(GLFW3) -lGL -lm -lGLU -lGLEW

.PHONY: all 

all:  \
	placeholder \
	wm_class \
	send

generate: clean

clean:
	@rm -rfv \
	    placeholder \
	    wm_class \
	    send 

placeholder: placeholder.c 
	$(CC) $(CFLAGS) $(LIBS) $@.c -o $@

wm_class: wm_class.c 
	$(CC) $(CFLAGS) -lX11 $@.c -o $@

send: send.c 
	$(CC) $(CFLAGS) $@.c -o $@

