CFLAGS += -std=gnu11 -march=native -Os -pedantic
LIBS := -lGL -lm -lGLU -lGLEW
SRC_DIR := src
BIN_DIR := bin

.PHONY: all

all: wm_class send
generate: clean
clean: 
	@rm -rfv \
		$(BIN_DIR)/wm_class \
		$(BIN_DIR)/send

wm_class: $(SRC_DIR)/wm_class.c
	$(CC) $(CFLAGS) -lX11 $(SRC_DIR)/$@.c -o $(BIN_DIR)/$@ -Os -s
	strip $(BIN_DIR)/$@

send: $(SRC_DIR)/send.c
	$(CC) $(CFLAGS) $(SRC_DIR)/$@.c -lbsd -o $(BIN_DIR)/$@ -Os -s
	strip $(BIN_DIR)/$@
