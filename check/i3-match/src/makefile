
SRCDIR = .

TARGETS = i3-match

LIBS = json-c xcb-util

SRCS = $(shell find $(SRCDIR) -name '*.c')

OBJS = $(patsubst %.c,%.o,$(SRCS))

# objs with a main definition
TARGET_OBJS = $(patsubst %,$(SRCDIR)/%.o,$(TARGETS))

# objs without a main definition
SHARE_OBJS = $(filter-out $(TARGET_OBJS),$(OBJS))

CFLAGS += -Wall -pedantic -Wextra -Wshadow -Wpointer-arith -Wcast-qual -Wstrict-prototypes -Wmissing-prototypes -Wformat -Werror=format-security

CFLAGS += $(shell pkg-config --cflags $(LIBS))

LDFLAGS += $(shell pkg-config --libs-only-other --libs-only-L $(LIBS))
LD_LIBS = $(shell pkg-config --libs-only-l $(LIBS))

ifdef ASCII_TREE
CFLAGS += -DASCII_TREE
endif

ifdef DONT_USE_MALLOC_USABLE_SIZE
CFLAGS += -DDONT_USE_MALLOC_USABLE_SIZE
endif

ifdef DEBUG
CFLAGS += -g -ggdb -DDEBUG
else
CFLAGS += -O2 -flto
endif

.PHONY: all strip info clean depend

all: $(TARGETS) swaymatch

strip: all
	strip -s $(TARGETS)

info:
	@echo TARGET_OBJS: $(TARGET_OBJS)
	@echo SHARE_OBJS: $(SHARE_OBJS)

clean:
	rm -f -- $(TARGETS) swaymatch $(OBJS) makefile.depend

depend: makefile.depend

makefile.depend: $(SRCS)
	rm -f makefile.depend
	$(CC) $(CFLAGS) -MM $^ >makefile.depend

-include makefile.depend

i3-match: $(SRCDIR)/i3-match.o $(SHARE_OBJS)
	$(CC) -o $@ $(LDFLAGS) $(patsubst %,$(SRCDIR)/%.o,$@) $(SHARE_OBJS) $(LD_LIBS)

swaymatch: i3-match
	ln -sfTr i3-match swaymatch
