CFLAGS += -std=c11 -pedantic -O2
LIBS :=
GLFW3 := $(shell pkg-config --libs glfw3)
LIBS := $(GLFW3) -lGL -lm -lGLU -lGLEW

all: placeholder

generate: clean

clean:
	@rm -rf placeholder

placeholder: generate
	$(CC) $(CFLAGS) -o placeholder placeholder.c $(LIBS)

