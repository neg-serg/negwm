/*
 * Source: https://github.com/treep/wm-class
 *
 * wm_class.c -- setting the WM_CLASS property by PID or by running a program.
 *
 * compile:
 *
 *   $ gcc -lX11 wm_class.c -o wm_class
 *
 * usage:
 *
 *   $ wm_class --set <name> <class> <pid>
 *   $ wm_class --run <name> <class> <program> <argument>*
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>
#include <errno.h>
#include <unistd.h>

#include <sys/types.h>
#include <signal.h>

#include <X11/Xlib.h>
#include <X11/Xatom.h>
#include <X11/Xutil.h>

/*
 * Utils.
 */

long *parse_long(long *res, const char *str)
{
    char *ptr;
    long val = strtol(str, &ptr, 10);

    if ((errno == ERANGE && (val == LONG_MAX || val == LONG_MIN)) ||
        (errno != 0 && val == 0) || (ptr == str))
        return NULL;

    *res = val;

    return res;
}

void print_error(const char *message)
{
    fprintf(stderr, "%s\n", message);
}

/*
 * Generic functions.
 */

typedef struct window {
    Display *display;
    Window window;
} window;

typedef void(window_action)(window*, void*);

void match_pid(window *win, Atom atom, pid_t pid, window_action act, void *ctx)
{
    Atom type;
    int format;
    unsigned long n_items, n_bytes;
    unsigned char *prop = NULL;

    if (Success == XGetWindowProperty
        (win->display, win->window, atom, 0, 1, False, XA_CARDINAL, &type,
         &format, &n_items, &n_bytes, &prop))
    {
        if (prop != NULL) {
            if (pid == *(pid_t*)prop)
                act(win, ctx);
            XFree(prop);
        }
    }
}

void traverse(window *win, window_action act, void* ctx)
{
    unsigned n, i;
    Window root, parent, *childs;

    act(win, ctx);

    if (0 != XQueryTree(win->display, win->window, &root, &parent, &childs, &n)) {
        for (i = 0; i < n; i++) {
            // traverse destructively:
            win->window = childs[i];
            traverse(win, (void (*)(struct window *, void *))act, ctx);
        }
        XFree(childs);
    }
}

/*
 * Concrete functions.
 */

typedef struct wm_class_context {
    pid_t pid;
    Atom atom;
    unsigned *done;
    char *name;
    char *class;
} wm_class_context;

void set_wm_class(window *win, wm_class_context *ctx)
{
    XClassHint *hint = XAllocClassHint();

    if (hint == NULL) {
        print_error("system error: XAllocClassHint");
        exit(EXIT_FAILURE);
    }

    hint->res_name = ctx->name;
    hint->res_class = ctx->class;
    XSetClassHint(win->display, win->window, hint);

    *(ctx->done) += 1;

    XFree(hint);
}

void match_pid_set_wm_class(window *win, wm_class_context *ctx)
{
    match_pid(
        win,
        ctx->atom,
        ctx->pid,
        (void (*)(struct window *, void *))set_wm_class,
        ctx
    );
}

/*
 * Top-level functions.
 */

void set_wm_class_by_pid(char *name, char *class, pid_t pid)
{
    unsigned done = 0;
    Display *display = XOpenDisplay(NULL);

    if (display == NULL) {
        print_error("system error: XOpenDisplay");
        goto fail;
    }

    Window window = XDefaultRootWindow(display);

    struct window win = {
        .display = display,
        .window = window
    };

    Atom net_wm_pid = XInternAtom(display, "_NET_WM_PID", True);

    if (net_wm_pid == None) {
        print_error("can't find the _NET_WM_PID property");
        goto fail;
    }

    struct wm_class_context ctx = {
        .pid = pid,
        .atom = net_wm_pid,
        .done = &done,
        .name = name,
        .class = class
    };

    traverse(
        &win,
        (void (*)(struct window *, void *))match_pid_set_wm_class,
        &ctx
    );

    if (done == 0) {
        print_error("can't find the program windows (or maybe the program don't set the _NET_WM_PID property)");
        goto fail;
    }

    XCloseDisplay(display);

    printf("change properties of %i windows\n", done);

    return;

fail:
    XCloseDisplay(display);
    exit(EXIT_FAILURE);
}

void run_with_wm_class(char *name, char *class, char **argv)
{
    pid_t pid = fork();

    switch (pid) {
    case -1:
        print_error("system error: fork");
        exit(EXIT_FAILURE);
    case 0:
        execvp(argv[0], argv);
        print_error("can't execute the program");
        kill(getppid(), SIGKILL);
        exit(EXIT_FAILURE);
    }

    sleep(1);

    set_wm_class_by_pid(name, class, pid);
}

/*
 * CLI.
 */

void usage(void)
{
    puts("usage: wm_class --set <name> <class> <pid>");
    puts("     | wm_class --run <name> <class> <program> [<argument>*]");
}

int main(int argc, char **argv)
{
    if (argc < 5) {
        usage();
        exit(EXIT_FAILURE);
    }

    char *opt = argv[1], *name = argv[2], *class = argv[3];

    if (strcmp(opt, "--set") == 0) {
        long pid;
        if (NULL == parse_long(&pid, argv[4])) {
            printf("not a number: %s\n", argv[4]);
            exit(EXIT_FAILURE);
        }
        set_wm_class_by_pid(name, class, pid);
    } else if (strcmp(opt, "--run") == 0) {
        run_with_wm_class(name, class, &argv[4]);
    } else {
        usage();
        exit(EXIT_FAILURE);
    }

    exit(EXIT_SUCCESS);
}

// KLUDGE:
//   total heap usage: 1,425 allocs, 1,424 frees
//   definitely lost: 124 bytes in 1 blocks
