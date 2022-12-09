#include "util.h"

#include <signal.h>
#include <sys/wait.h>

static void signal_child(__unused int sig) {
    while (waitpid(-1, NULL, WNOHANG) > 0);
}

extern void set_default_sigchld_handler(void) {
    signal(SIGCHLD, &signal_child);
}

extern void push_whole_file(string_builder *sb, FILE *f) {
    char buf[BUFSIZ];
    size_t n;
    while (!ferror(f) && !feof(f)) {
        n = fread(buf, sizeof(char), BUFSIZ, f);
        if (n > 0) {
            sb_pushn(sb, buf, n);
        }
    }
}
