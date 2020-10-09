CFLAGS += -static -std=gnu18 -march=native -Ofast -pedantic
SRC_DIR := src
BIN_DIR := bin

.PHONY: all

all: send
generate: clean
clean:
	@rm -rfv \
		$(BIN_DIR)/send

send: $(SRC_DIR)/send.c
	$(CC) $(CFLAGS) $(SRC_DIR)/$@.c -o $(BIN_DIR)/$@ -s
	strip $(BIN_DIR)/$@
