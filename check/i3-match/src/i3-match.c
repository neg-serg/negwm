/*
 * Match and query i3/sway window properties and events.
 *
 * needed libraries: json-c
 */

#include "i3util.h"
#include "i3ipc.h"
#include "i3json.h"
#include "debug.h"
#include "jsonutil.h"
#include "util.h"
#include "sb.h"

#include <json-c/json_tokener.h>
#include <json-c/json_util.h>

#include <assert.h>
#include <fcntl.h>
#include <getopt.h>
#include <unistd.h>
#include <stdlib.h>
#include <string.h>

#ifndef ASCII_TREE
// Unicode version of indent tree strings.
// Strings used for nodes.
#define IT_MID_CHILD "\u251c\u2500"
#define IT_LAST_CHILD "\u2514\u2500"
// String used for the root node. Should be one
// cell shorter than IT_BAR and IT_EMPTY.
#define IT_ROOT "\u2500"
// Strings used for indenting, the last character
// is removed when indenting for the root node.
#define IT_BAR "\u2502  "
#define IT_EMPTY "   "
#else
// Ascii version of indent tree strings.
#define IT_ROOT "-"
#define IT_MID_CHILD "+-"
#define IT_BAR "|  "
#define IT_EMPTY "   "
#define IT_LAST_CHILD "`-"
#endif

#define COL_BOLD "\x1b[1m"
#define COL_NORMAL "\x1b[m"

#define CH_SPACE ' '
#define CH_BAR '|'

const char *ALL_EVENTS_SUB_JSON_I3 = "[\"workspace\",\"output\",\"mode\",\"window\",\"barconfig_update\",\"binding\",\"shutdown\",\"tick\"]";
const char *ALL_EVENTS_SUB_JSON_SWAY = "[\"workspace\",\"mode\",\"window\",\"barconfig_update\",\"binding\",\"shutdown\",\"tick\",\"bar_state_update\",\"input\"]";

#define EVENT_TYPE_COUNT 8
const char *EVENT_NAMES[EVENT_TYPE_COUNT] = {
    "workspace", // (I3_IPC_EVENT_MASK | 0)
    "output", // (I3_IPC_EVENT_MASK | 1)
    "mode", // (I3_IPC_EVENT_MASK | 2)
    "window", // (I3_IPC_EVENT_MASK | 3)
    "barconfig_update", // (I3_IPC_EVENT_MASK | 4)
    "binding", // (I3_IPC_EVENT_MASK | 5)
    "shutdown", // (I3_IPC_EVENT_MASK | 6)
    "tick", // (I3_IPC_EVENT_MASK | 7)
};
#define EVENT_TYPE_SWAY_COUNT 2
#define EVENT_TYPE_SWAY_OFFSET 0x14
const char *EVENT_NAMES_SWAY[EVENT_TYPE_SWAY_COUNT] = {
    "bar_state_update", // (I3_IPC_EVENT_MASK | 0x14)
    "input", // (I3_IPC_EVENT_MASK | 0x15)
};

#define TREE_OUTPUTS_COUNT 2
char *TREE_OUTPUTS[TREE_OUTPUTS_COUNT] = { ":itree", "name" };

#define DEFAULT_MONITOR_OUTPUT_COUNT 8
char *DEFAULT_MONITOR_OUTPUTS[DEFAULT_MONITOR_OUTPUT_COUNT] = {
    ":evtype", "change", "current/name", "container/name", "binding/command", "payload", "input/identifier", "id"
};

enum mode {
    MODE_MATCH = 0,
    MODE_SUBSCRIBE = 1,
};

enum outmode {
    OUT_NONE = 0,
    OUT_FIELDS = 1,
};

enum flags {
    F_PRINTALL = 1<<0,
    F_HIGHLIGHT = 1<<1,
    F_FLUSH = 1<<2,
};

struct context {
    const char *sock_path;
    const char *in_file;
    i3json_matcher *matchers;
    int matcherc;
    enum outmode outmode;
    char **outputs;
    int outputc;
    int flags;
    int almostall;
    int mincount;
    int maxcount;
    char *field_sep;
    size_t field_sep_len;
    int swaymode;
    string_builder sb;
    string_builder itree;
    int objcount;
    int matchcount;
    struct i3json_print_tree_context pt_context;
    i3_msg *msg;
};

static const char *eventtype2name(unsigned int type) {
    if ((type & I3_IPC_EVENT_MASK) != I3_IPC_EVENT_MASK) {
        return "none";
    }
    unsigned int i = type & ~I3_IPC_EVENT_MASK;
    if (i >= EVENT_TYPE_SWAY_OFFSET) {
        i -= EVENT_TYPE_SWAY_OFFSET;
        if (i < EVENT_TYPE_SWAY_COUNT) {
            return EVENT_NAMES_SWAY[i];
        }
    } else if (i < EVENT_TYPE_COUNT) {
        return EVENT_NAMES[i];
    }
    return "unknown";
}

static void push_value(string_builder *sb, const char *key,
                       json_object *node, iter_info *info,
                       struct context *ctx, int match) {
    debug_print("key=%s\n", key);
    if (strcmp(":match", key) == 0) {
        sb_pushf(sb, "%d", !!match);
    } else if (strcmp(":level", key) == 0) {
        sb_pushf(sb, "%d", info->level);
    } else if (strcmp(":floating", key) == 0) {
        sb_pushf(sb, "%d", ctx->pt_context.floating);
    } else if (strcmp(":scratch", key) == 0) {
        sb_pushf(sb, "%d", ctx->pt_context.scratch);
    } else if (strcmp(":workspace", key) == 0) {
        if (ctx->pt_context.ws) {
            sb_pushf(sb, "%s", ctx->pt_context.ws);
        }
    } else if (strcmp(":output", key) == 0) {
        if (ctx->pt_context.output) {
            sb_pushf(sb, "%s", ctx->pt_context.output);
        }
    } else if (strcmp(":sibi", key) == 0) {
        sb_pushf(sb, "%d", info->nodei);
    } else if (strcmp(":sibc", key) == 0) {
        sb_pushf(sb, "%d", info->nodec);
    } else if (strcmp(":childc", key) == 0) {
        sb_pushf(sb, "%d", info->subnodec);
    } else if (strcmp(":indent", key) == 0) {
        const char *str = match ? "--" : "  ";
        int j = info->level; // indent level + 1 times
        for (; j >= 0; j--) {
            sb_pushn(sb, str, 2);
        }
    } else if (strcmp(":itree", key) == 0) {
        string_builder *isb = &ctx->itree;
        int n = info->level;
        int j;
        for (j = 0; j < n; j++) {
            if (isb->buf[j] == CH_SPACE) {
                sb_pushn(sb, IT_EMPTY, strlen(IT_EMPTY) - !j);
            } else {
                sb_pushn(sb, IT_BAR, strlen(IT_BAR) - !j);
            }
        }
        if (info->level == 0) {
            sb_push(sb, IT_ROOT);
        } else if (info->nodei < info->nodec - 1) {
            sb_push(sb, IT_MID_CHILD);
        } else {
            sb_push(sb, IT_LAST_CHILD);
        }
    } else if (strcmp(":evtype", key) == 0) {
        i3_msg *msg = ctx->msg;
        if (msg) {
            sb_push(sb, eventtype2name(msg->type));
        } else {
            sb_pushn(sb, "none", 4);
        }
    } else if (strcmp(":nodei", key) == 0) {
        sb_pushf(sb, "%d", ctx->objcount);
    } else if (strcmp(":matchc", key) == 0) {
        sb_pushf(sb, "%d", ctx->matchcount);
    } else if (strncmp(":json", key, 5) == 0 && (key[5] == '\0' || key[5] == ':')) {
        json_object *n = node;
        if (key[5]) {
            n = jsonutil_path_get(node, key + 6);
        }
        if (n) {
            size_t len;
            const char *str = json_object_to_json_string_length(
                 n, JSON_C_TO_STRING_PLAIN, &len);
            malloc_check(str);
            sb_pushn(sb, str, len);
        } else {
            sb_pushn(sb, "null", 4);
        }
    } else {
        json_object *n = jsonutil_path_get(node, key);
        const char *str = jsonutil_get_string(n);
        if (!str) {
            // n is array or object
            size_t len;
            str = json_object_to_json_string_length(
                 n, JSON_C_TO_STRING_PLAIN, &len);
            malloc_check(str);
            sb_pushn(sb, str, len);
        } else {
            sb_push(sb, str);
        }
    }
}

static void format_fields(json_object *node, iter_info *info, struct context *ctx, int match) {
    int i;
    string_builder *sb = &ctx->sb;
    if (match && ctx->flags & F_HIGHLIGHT) {
        sb_push(sb, COL_BOLD);
    }
    for (i = 0; i < ctx->outputc; i++) {
        if (i) sb_pushn(sb, ctx->field_sep, ctx->field_sep_len);
        const char *key = ctx->outputs[i];
        push_value(sb, key, node, info, ctx, match);
    }
    if (match && ctx->flags & F_HIGHLIGHT) {
        sb_push(sb, COL_NORMAL);
    }
}

static void accum_itree(iter_info *info, struct context *context) {
    sb_trunc(&context->itree, info->level);
    char ch = CH_SPACE;
    if (info->level && info->nodei < info->nodec - 1) {
        ch = CH_BAR;
    }
    sb_pushn(&context->itree, &ch, 1);
}

struct node_getter_args {
    json_object *node;
    iter_info *info;
    struct context *ctx;
};

static const char *node_value_getter(const char *key, void *ptr) {
    struct node_getter_args *args = ptr;
    string_builder *sb = &args->ctx->sb;
    sb_trunc(sb, 0);
    push_value(sb, key, args->node, args->info, args->ctx, 1);
    return sb->buf;
}

static iter_advice process_node(json_object *node, iter_info *info, struct context *ctx) {
    ++ctx->objcount;
    struct node_getter_args gargs = {
        .node = node,
        .info = info,
        .ctx = ctx,
    };
    int match = 0;
    if (i3json_matchers_match_ex(ctx->matcherc, ctx->matchers, &node_value_getter, &gargs)) {
        ++ctx->matchcount;
        match = 1;
    }
    accum_itree(info, ctx);
    if (match || ctx->flags & F_PRINTALL) {
        switch (ctx->outmode) {
        case OUT_NONE:
            break;
        case OUT_FIELDS:
            sb_trunc(&ctx->sb, 0);
            format_fields(node, info, ctx, match);
            sb_pushn(&ctx->sb, "\n", 1);
            fwrite(ctx->sb.buf, sizeof(char), ctx->sb.len, stdout);
            if (ctx->flags & F_FLUSH) {
                fflush(stdout);
            }
            break;
        }
    }
    if (match && ctx->maxcount > 0 && ctx->matchcount >= ctx->maxcount) {
        return ITER_ABORT_SUCCESS;
    }
    return ITER_CONT;
}

static int subscribe_eventloop(struct context *ctx, int sock) {
    i3_msg msg = EMPTY_I3_MSG;
    ctx->msg = &msg;
    // iter_info values not meaningful for events
    iter_info info = { 0, 0, 0, 0, 0 };
    json_tokener *tokener = json_tokener_new_ex(JSON_TOKENER_DEPTH);
    malloc_check(tokener);
    int status = 0;
    for (;;) {
        if (i3ipc_recv_message(sock, &msg) == -1) {
            status = 2;
            goto cleanup;
        }
        json_tokener_reset(tokener);
        json_object *event = json_tokener_parse_ex(tokener, msg.data, msg.len);
        if (!event) {
            jsonutil_print_error("event parse error", json_tokener_get_error(tokener));
            // continue matching against NULL value
        }
        iter_advice advice = process_node(event, &info, ctx);
        json_object_put(event);
        i3ipc_msg_recycle(&msg);
        switch (advice) {
        case ITER_ABORT_SUCCESS:
            status = 0;
            goto cleanup;
        case ITER_ABORT:
            status = 1;
            goto cleanup;
        case ITER_CONT:
            break;
        case ITER_NODESC:
            fprintf(stderr, "invalid return value from process_node\n");
            abort();
        }
    }
cleanup:
    json_tokener_free(tokener);
    del_i3_msg(&msg);
    ctx->msg = NULL;
    return status;
}

static int match_evtype_only(i3json_matcher *matchers, int matcherc, const char *type) {
    int i;
    for (i = 0; i < matcherc; i++) {
        i3json_matcher *matcher = matchers + i;
        if (i3json_matcher_cmp_key(matcher, ":evtype") == 0) {
            if (!i3json_matcher_match_value(type, matcher)) {
                return 0;
            }
        }
    }
    return 1;
}

static json_object *get_matching_evtypes(i3json_matcher *matchers, int matcherc, int swaymode) {
    int i;
    json_object *array = json_object_new_array();
    malloc_check(array);
    for (i = 0; i < EVENT_TYPE_COUNT + EVENT_TYPE_SWAY_COUNT; i++) {
        if (swaymode) {
            // no output events on sway
            if (i == 1) continue;
        } else {
            // no sway events on i3
            if (i >= EVENT_TYPE_COUNT) break;
        }
        const char *name = i < EVENT_TYPE_COUNT ? EVENT_NAMES[i]
             : EVENT_NAMES_SWAY[i - EVENT_TYPE_COUNT];
        if (match_evtype_only(matchers, matcherc, name)) {
            debug_print("%s matches\n", name);
            json_object_array_add(array, json_object_new_string(name));
        }
    }
    return array;
}

struct matchmode_iter_pred_args {
    struct context *context;
    json_object *scratch_ids;
};

static iter_advice matchmode_iter_pred(json_object *node, iter_info *info, void *ptr) {
    struct matchmode_iter_pred_args *args = ptr;
    struct context *ctx = args->context;
    i3json_tree_accum_data(node, args->scratch_ids, info, &ctx->pt_context);
    return process_node(node, info, ctx);
}

static json_object *get_scratch_ids(json_object *tree) {
    if (!jsonutil_object_prop_is_str(tree, "name", "root")
        || !jsonutil_object_prop_is_str(tree, "type", "root")) {
        return NULL;
    }
    json_object *nodes;
    if (!json_object_object_get_ex(tree, "nodes", &nodes)
        || !json_object_is_type(nodes, json_type_array)) {
        return NULL;
    }
    json_object *output_obj = json_object_array_get_idx(nodes, 0);
    if (!jsonutil_object_prop_is_str(output_obj, "name", "__i3")
        || !jsonutil_object_prop_is_str(output_obj, "type", "output")) {
        return NULL;
    }
    if (!json_object_object_get_ex(output_obj, "nodes", &nodes)
        || !json_object_is_type(nodes, json_type_array)) {
        return NULL;
    }
    json_object *workspace_obj = json_object_array_get_idx(nodes, 0);
    if (!jsonutil_object_prop_is_str(workspace_obj, "name", "__i3_scratch")
        || !jsonutil_object_prop_is_str(workspace_obj, "type", "workspace")) {
        return NULL;
    }
    json_object *focus_ids;
    if (!json_object_object_get_ex(workspace_obj, "focus", &focus_ids)
        || !json_object_is_type(focus_ids, json_type_array)) {
        return NULL;
    }
    return focus_ids;
}

static int match_mode_main(struct context *context) {
    if (context->outmode == OUT_NONE) {
        context->maxcount = context->mincount;
    }
    i3_msg msg = EMPTY_I3_MSG;
    json_object *tree = NULL;
    int close_fd = -1;
    int sock = -1;
    int result = 2;
    if (context->in_file) {
        int fd = -1;
        if (strcmp(context->in_file, "-") == 0) {
            fd = STDIN_FILENO;
        } else {
            close_fd = fd = open(context->in_file, O_RDONLY);
            if (fd == -1) {
                perror("open");
                goto cleanup;
            }
        }
        tree = json_object_from_fd(fd);
        const char *err = json_util_get_last_err();
        if (err) {
            fprintf(stderr, "tree parse error: %s", err);
            goto cleanup;
        }
    } else {
        set_default_sigchld_handler();
        sock = i3ipc_open_socket(context->sock_path, context->swaymode);
        if (sock == -1) {
            goto cleanup;
        }
        if (i3util_request_json(sock, I3_IPC_MESSAGE_TYPE_GET_TREE, "", &msg, &tree) == -1) {
            goto cleanup;
        }
        debug_print("%s\n", "close sock...");
    }

    struct matchmode_iter_pred_args args = {
        .context = context,
        .scratch_ids = get_scratch_ids(tree),
    };
    i3json_iter_nodes(tree, &matchmode_iter_pred, &args);
    result = context->matchcount >= context->mincount ? 0 : 1;

cleanup:
    if (close_fd != -1) {
        if (close(close_fd) == -1) {
            perror("close");
        }
    }
    if (sock != -1) close(sock);
    json_object_put(tree);
    del_i3_msg(&msg);
    return result;
}

static int subscribe_start(struct context *context, int sock) {
    const char *body = NULL;
    json_object *tmparray = NULL;

    int result = -1;
    if (context->flags & F_PRINTALL && !context->almostall) {
        body = context->swaymode ? ALL_EVENTS_SUB_JSON_SWAY
            : ALL_EVENTS_SUB_JSON_I3;
    } else {
        tmparray = get_matching_evtypes(
            context->matchers, context->matcherc, context->swaymode);
        if (!json_object_array_length(tmparray)) {
            fprintf(stderr, ":evtype never matches\n");
            goto cleanup;
        }
        body = json_object_to_json_string_ext(
            tmparray, JSON_C_TO_STRING_PLAIN);
    }
    debug_print("body=%s\n", body);
    if (i3util_subscribe(sock, body) == -1) {
        fprintf(stderr, "subscribe request failed\n");
        goto cleanup;
    }

    result = 0;

cleanup:
    json_object_put(tmparray);
    return result;
}

static int subscribe_mode_main(struct context *context) {
    set_default_sigchld_handler();
    int result = 2;

    int sock = i3ipc_open_socket(context->sock_path, context->swaymode);
    if (sock == -1) {
        goto cleanup;
    }
    if (subscribe_start(context, sock) == -1) {
        goto cleanup;
    }

    result = subscribe_eventloop(context, sock);

cleanup:
    close(sock);
    return result;
}

int main(int argc, char *argv[]) {
    i3json_matcher *matchers = calloc(argc - 1, sizeof(i3json_matcher));
    if (argc > 1) malloc_check(matchers);

    struct context context = {
        .sock_path = NULL,
        .in_file = NULL,
        .matchers = matchers,
        .matcherc = 0,
        .outmode = OUT_NONE,
        .outputs = NULL,
        .outputc = 0,
        .flags = 0,
        .almostall = 0,
        .mincount = 1,
        .maxcount = 0,
        .field_sep = " ",
        .field_sep_len = 1,
        .swaymode = 0,
        .sb = EMPTY_STRING_BUILDER,
        .itree = EMPTY_STRING_BUILDER,
        .matchcount = 0,
        .pt_context = I3JSON_EMPTY_PRINT_TREE_CONTEXT,
    };

    debug_print("BUFSIZ=%d\n", BUFSIZ);

    if ((argv[0] && strcmp("swaymatch", argv[0]) == 0)) {
        context.swaymode = 1;
    } else {
        const char *env_swaysock = getenv("SWAYSOCK");
        if (env_swaysock && *env_swaysock) {
             context.swaymode = 1;
        }
    }

    #define EXIT_MODE_ERROR(mode, option) \
        do { fprintf(stderr, option " can only be used in " mode "\n"); goto cleanup; } while (0)
    enum mode mode = MODE_MATCH;
    int printtree = 0;
    char **aoutputs = NULL;
    int c;
    int have_modearg = 0;
    optind = 1;
    int result = 2;
    while (optind < argc) {
        int prevind = optind;
        if ((c = getopt(argc, argv, "+s:Si:ahml:n:d:e:toIW")) != -1) {
            debug_print("option: ind=%d c=%c\n", optind, c);
            switch (c) {
            case 's':
                context.sock_path = optarg;
                break;
            case 'S':
                if (have_modearg) {
                    fprintf(stderr, "cannot specify mode after mode-specific arguments\n");
                    goto cleanup;
                }
                context.maxcount = 1;
                context.flags |= F_FLUSH;
                mode = MODE_SUBSCRIBE;
                break;
            case 'i':
                if (mode != MODE_MATCH) EXIT_MODE_ERROR("match-mode", "-i");
                have_modearg = 1;
                context.in_file = optarg;
                break;
            case 'a':
                if (context.flags & F_PRINTALL) {
                    context.almostall = 1;
                }
                context.flags |= F_PRINTALL;
                break;
            case 'h':
                context.flags |= F_HIGHLIGHT;
                break;
            case 'm':
                if (mode != MODE_SUBSCRIBE) EXIT_MODE_ERROR("subscribe-mode", "-m");
                context.maxcount = -1;
                context.outmode = OUT_FIELDS;
                context.outputs = DEFAULT_MONITOR_OUTPUTS;
                context.outputc = DEFAULT_MONITOR_OUTPUT_COUNT;
                break;
            case 'l': {
                if (mode != MODE_MATCH) EXIT_MODE_ERROR("match-mode", "-l");
                int value, count;
                if (sscanf(optarg, "%d%n", &value, &count) < 1 || optarg[count] != '\0') {
                    fprintf(stderr, "invalid min count (-l) - %s\n", optarg);
                    goto cleanup;
                }
                have_modearg = 1;
                context.mincount = value;
                break;
            }
            case 'n': {
                int value, count;
                if (sscanf(optarg, "%d%n", &value, &count) < 1 || optarg[count] != '\0') {
                    fprintf(stderr, "invalid max count (-n) - %s\n", optarg);
                    goto cleanup;
                }
                have_modearg = 1;
                context.maxcount = value;
                break;
            }
            case 'd':
                context.field_sep = optarg;
                context.field_sep_len = strlen(optarg);
                break;
            case 'e': {
                have_modearg = 1;
                if (argc - optind < 2) {
                    fprintf(stderr, "missing %d arguments for -e\n", 2 + optind - argc);
                    goto cleanup;
                }
                int op = i3json_parse_operator(argv[optind]);
                if (op == -1) {
                    fprintf(stderr, "invalid operator: %s\n", argv[optind]);
                    goto cleanup;
                }
                i3json_make_matcher(optarg, argv[optind + 1], op, matchers + context.matcherc);
                ++context.matcherc;
                optind += 2;
                break;
            }
            case 't':
                if (mode != MODE_MATCH) EXIT_MODE_ERROR("match-mode", "-t");
                have_modearg = 1;
                printtree = 1;
                context.outmode = OUT_FIELDS;
                context.outputs = TREE_OUTPUTS;
                context.outputc = TREE_OUTPUTS_COUNT;
                break;
            case 'o':
                if (optind == prevind) {
                    fprintf(stderr, "no option allowed after -o\n");
                    goto cleanup;
                }
                have_modearg = 1;
                context.outmode = OUT_FIELDS;
                if (printtree) {
                    aoutputs = calloc(argc - optind + 1, sizeof(char*));
                    malloc_check(aoutputs);
                    aoutputs[0] = ":itree";
                    memcpy(aoutputs + 1, argv + optind, (argc - optind) * sizeof(char*));
                    context.outputs = aoutputs;
                    context.outputc = argc - optind + 1;
                } else {
                    context.outputs = argv + optind;
                    context.outputc = argc - optind;
                }
                goto argparse_finished;
            case 'I':
                context.swaymode = 0;
                break;
            case 'W':
                context.swaymode = 1;
                break;
            case '?':
                goto cleanup;
            default:
                fprintf(stderr, "unhandled option: '%c'\n", c);
                abort();
            }
        } else {
            have_modearg = 1;
            const char *arg = argv[optind];
            if (i3json_parse_matcher(arg, matchers + context.matcherc) == -1) {
                fprintf(stderr, "invalid filter: %s\n", arg);
                goto cleanup;
            }
            ++context.matcherc;
            ++optind;
        }
    }
argparse_finished: {}

    switch (mode) {
    case MODE_MATCH:
        result = match_mode_main(&context);
        break;
    case MODE_SUBSCRIBE:
        result = subscribe_mode_main(&context);
        break;
    default:
        fprintf(stderr, "invalid operation mode\n");
        abort();
    }

cleanup:
    debug_print("%s\n", "cleanup...");
    sb_free(&context.itree);
    sb_free(&context.sb);
    free(aoutputs);
    free(matchers);

    return result;
}
