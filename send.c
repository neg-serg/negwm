#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <stdbool.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>

typedef struct Arg {
    const char *name;
    const int num_param;
} Arg;

typedef Arg Args[16];

size_t len(const char* arr[]) {
    const char **s;
    for(s = arr; *s; ++s);
    return (s - arr);
}

signed int in_arr(const char *arg, const char * arr[], size_t len){
    if( arr != NULL && arg != NULL ) {
        for(int i = 0; i < len; i++){
            if (!strcmp(arr[i], arg)){
                return i;
            }
        }
    }
    return -1;
}

enum {
    CMD_ITSELF = 0
    , MOD_NAME = 1
    , MOD_FUNC = 2
};

enum {
    CIRCLE = 0
    , NS = 1
    , FLAST = 2
    , MENU = 3
    , I3INFO = 4
};

const char* docstr= \
    "Usage:\n" \
    "  send circle reload\n" \
    "  send circle next <name>\n" \
    "  send circle info <name>\n" \
    "  send circle run <name> <subtag>\n" \
    "  send ns show <name>\n" \
    "  send ns hide <name>\n" \
    "  send ns toggle <name>\n" \
    "  send ns run <name> <prog>\n" \
    "  send ns next\n" \
    "  send ns dialog\n" \
    "  send ns reload\n" \
    "  send ns geom_restore\n" \
    "  send ns geom_save\n" \
    "  send ns geom_dump\n" \
    "  send ns geom_autosave_mode\n" \
    "  send ns hide_current\n" \
    "  send ns add_prop\n" \
    "  send flast switch\n" \
    "  send flast reload\n" \
    "  send menu run\n" \
    "  send menu xprop\n" \
    "  send menu autoprop\n" \
    "  send menu ws\n" \
    "  send i3info request\n" \
    "  send (-h | --help)\n" \
    "  send --version\n" \
    "\n" \
    "Options:\n" \
    "  -h --help     Show this screen.\n" \
    "  --version     Show version.\n" \
    "\n" \
    "Created by :: Neg\n" \
    "email :: <serg.zorg@gmail.com>\n" \
    "github :: https://github.com/neg-serg?tab=repositories\n" \
    "year :: 2018\n"; \

const char *progs[] = {
    [CIRCLE] = "circle",
    [NS] = "ns",
    [FLAST] = "flast",
    [MENU] = "menu",
    [I3INFO] = "i3info",
    NULL
};

Args ArgMap[] = {
    [CIRCLE] = {
        { "reload", 0 } ,
        { "next", 1 },
        { "info", 1 },
        { "run", 2 },
        { NULL, 0 },
    },
    [NS] = {
        { "show", 1 },
        { "hide", 1 },
        { "toggle", 1 },
        { "run", 2 },
        { "next", 0 },
        { "reload", 0 },
        { "geom_restore", 0 },
        { "geom_dump", 0 },
        { "geom_save", 0 },
        { "geom_autosave_mode", 0 },
        { "hide_current", 0 },
        { "dialog", 0 },
        { "add_prop", 2 },
        { NULL, 0 },
    },
    [FLAST] = {
        { "switch", 0 },
        { "reload", 0 },
        { NULL, 0 },
    },
    [MENU] = {
        { "run", 0 },
        { "xprop", 0 },
        { "reload", 0 },
        { "autoprop", 0 },
        { "ws", 0 },
        { NULL, 0 },
    },
    [I3INFO] = {
        { "ns_list", 0 },
        { "reload", 0 },
        { NULL, 0 },
    }
};

char *get_fifo_name(int modnum){
    char *sock_path = calloc(128, 1);
    char *sock_path_after_readlink = calloc(128, 1);
    const char* home = getenv("HOME");
    strncat(sock_path, home, strlen(home));
    strncat(sock_path, "/", 1);
    strncat(sock_path, "tmp", strlen("tmp"));
    readlink(sock_path, sock_path_after_readlink, 128);
    strncat(sock_path_after_readlink, "/", 1);
    strncat(sock_path_after_readlink, progs[modnum], strlen(progs[modnum]));
    strncat(sock_path_after_readlink, ".fifo", strlen(".fifo"));
    free(sock_path);
    return sock_path_after_readlink;
}

int main(int argc, const char *argv[]) {
    if (argc == 1 || !strcmp(argv[1], "help")){
        printf("%s\n", docstr);
        return 0;
    }

    char *cmd = calloc(1024, 1);
    int mod = in_arr(argv[MOD_NAME], progs, len(progs));
    if (mod == -1){
        free(cmd);
        return -1;
    }

    const char *mod_funcs[16] = {0};
    int mod_funcs_len = 0;
    for (int i = 0; ArgMap[mod][i].name != NULL; i++) {
        mod_funcs[i] = ArgMap[mod][i].name;
        mod_funcs_len = i + 1;
    }

    int mod_func = in_arr(argv[MOD_FUNC], mod_funcs, mod_funcs_len);
    if (mod_func != -1) {
        if (argc == 3 + ArgMap[mod][mod_func].num_param) {
            for(int i = 2; i < argc; i++){
                strncat(cmd, argv[i], strlen(argv[i]));
                strncat(cmd, " ", 1);
            }
        } else {
            printf("%s\n", "bad number of parameters!");
            free(cmd);
            return -2;
        }
    } else {
        free(cmd);
        return -3;
    }

    char *sock_name = get_fifo_name(mod);
    cmd[strlen(cmd)]='\n';
    int out_fd = open(sock_name, O_WRONLY | O_NONBLOCK);
    write(out_fd, cmd, strlen(cmd)-1);
    close(out_fd);

    free(sock_name);
    free(cmd);
    return 0;
}
