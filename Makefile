CFLAGS += -std=gnu11 -march=native -Os -pedantic
LIBS := -lGL -lm -lGLU -lGLEW
SRC_DIR := src
BIN_DIR := bin

.PHONY: all

all: send
generate: clean
clean: 
	@rm -rfv \
		$(BIN_DIR)/send

send: $(SRC_DIR)/send.c
	$(CC) $(CFLAGS) $(SRC_DIR)/$@.c -lbsd -o $(BIN_DIR)/$@ -Os -s
	strip $(BIN_DIR)/$@
