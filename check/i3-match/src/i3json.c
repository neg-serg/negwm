#include "i3json.h"
#include "jsonutil.h"
#include "util.h"
#include "debug.h"

#include <stdlib.h>
#include <string.h>

struct operator {
    const char *str;
    const size_t len;
    const int type;
};

static const struct operator OPERATORS[] = {
    {"^=", 2, MT_STARTS},
    {"$=", 2, MT_ENDS},
    {"*=", 2, MT_CONTAINS},
    {"=", 1, MT_EQUALS},
    {"!^=", 3, MT_STARTS | MT_NOT},
    {"!$=", 3, MT_ENDS | MT_NOT},
    {"!*=", 3, MT_CONTAINS | MT_NOT},
    {"!=", 2, MT_EQUALS | MT_NOT},
};

extern int i3json_parse_matcher(const char *strdef, i3json_matcher *out) {
    int i;
    int numops = sizeof(OPERATORS) / sizeof(struct operator);
    const struct operator *best = NULL;
    int bestpos = -1;
    for (i = 0; i < numops; i++) {
        const char *p = strstr(strdef, OPERATORS[i].str);
        if (p) {
            int pos = p - strdef;
            if (!best || pos < bestpos) {
                best = OPERATORS + i;
                bestpos = pos;
            }
        }
    }
    if (best) {
        out->type = best->type;
        out->key = strdef;
        out->key_len = bestpos;
        out->pattern = strdef + bestpos + best->len;
        out->pattern_len = strlen(strdef) - bestpos - best->len;
        return 0;
    } else {
        return -1;
    }
}

extern int i3json_parse_operator(const char *str) {
    int numops = sizeof(OPERATORS) / sizeof(struct operator);
    int i;
    for (i = 0; i < numops; i++) {
        const struct operator *op = OPERATORS + i;
        if (strcmp(str, op->str) == 0) {
            return op->type;
        }
    }
    return -1;
}

#define PRINT_MATCHER_FMT "key=%*.*s pattern=%*.*s type=%d"
#define PRINT_MATCHER_ARGS(matcher) \
        (int) matcher->key_len, (int) matcher->key_len, matcher->key, \
        (int) matcher->pattern_len, (int) matcher->pattern_len, matcher->pattern, \
        matcher->type

extern void i3json_make_matcher(const char *key, const char *pattern, unsigned int type, i3json_matcher *out) {
    out->key = key;
    out->key_len = strlen(key);
    out->pattern = pattern;
    out->pattern_len = strlen(pattern);
    out->type = type;
    debug_print("matcher={" PRINT_MATCHER_FMT "}\n", PRINT_MATCHER_ARGS(out));
}

extern int i3json_matcher_match_value(const char* value, i3json_matcher *matcher) {
    if (!value) {
        // Treat missing value as empty string.
        value = "";
    }
    size_t patlen = matcher->pattern_len;
    debug_print("pattern=%*.*s type=0x%x value=%s\n",
                (int) patlen, (int) patlen, matcher->pattern, matcher->type, value);
    int result;
    int basetype = matcher->type & MT_MASK_BASE;
    switch (basetype) {
    case MT_EQUALS:
        result = strncmp(value, matcher->pattern, patlen) == 0
                 && value[patlen] == '\0';
        break;
    case MT_STARTS:
        result = strncmp(value, matcher->pattern, patlen) == 0;
        break;
    case MT_ENDS: {
        size_t l = strlen(value);
        result = l >= patlen
                 && strncmp(value + l - patlen, matcher->pattern, patlen) == 0;
        break;
    }
    case MT_CONTAINS: {
        STACK_SUBSTR(pattern, matcher->pattern, patlen);
        result = strstr(value, pattern) != NULL;
        break;
    }
    default:
        fprintf(stderr, "basetype=%x\n", basetype);
        abort();
    }
    if (matcher->type & MT_NOT) {
        result = !result;
    }
    return result;
}

extern int i3json_matcher_match(json_object *node, i3json_matcher *matcher) {
    size_t keylen = matcher->key_len;
    STACK_SUBSTR(key, matcher->key, keylen);
    json_object *jobj = jsonutil_path_get(node, key);
    const char *value = jsonutil_get_string(jobj);
    return i3json_matcher_match_value(value, matcher);
}

extern int i3json_matchers_match_ex(int matcherc, i3json_matcher *matchers, i3json_value_getter *getter, void *ptr) {
    int i;
    for (i = 0; i < matcherc; i++) {
        i3json_matcher *matcher = matchers + i;
        size_t keylen = matcher->key_len;
        STACK_SUBSTR(key, matcher->key, keylen);
        const char *value = getter(key, ptr);
        if (!i3json_matcher_match_value(value, matcher)) {
            return 0;
        }
    }
    return 1;
}

extern int i3json_matchers_match_node(json_object *node, int matcherc, i3json_matcher *matchers) {
    int i;
    for (i = 0; i < matcherc; i++) {
        if (!i3json_matcher_match(node, matchers + i)) {
            return 0;
        }
    }
    return 1;
}

typedef struct {
    int matcherc;
    i3json_matcher *matchers;
    json_object *result;
} matcher_pred_args;

static iter_advice matcher_pred(json_object *node, __unused iter_info *info, void *ptr) {
    matcher_pred_args *args = ptr;
    if (i3json_matchers_match_node(node, args->matcherc, args->matchers)) {
        args->result = node;
        return ITER_ABORT_SUCCESS;
    } else {
        return ITER_CONT;
    }
}

extern json_object *i3json_matchers_match_tree(json_object *tree, int matcherc, i3json_matcher *matchers) {
    matcher_pred_args args = { .matcherc = matcherc, .matchers = matchers };
    if (i3json_iter_nodes(tree, &matcher_pred, &args) == ITER_ABORT_SUCCESS) {
        return args.result;
    } else {
        return NULL;
    }
}

extern int i3json_matcher_cmp_key(i3json_matcher *matcher, const char* key) {
    size_t keylen = matcher->key_len;
    int r;
    if ((r = strncmp(matcher->key, key, keylen)) == 0) {
        if (strlen(key) > keylen) {
            r = -1;
        }
    }
    return r;
}

static int i3json_is_scratch(json_object *node, json_object *scratch_ids) {
    json_object *obj;
    if (json_object_object_get_ex(node, "scratchpad_state", &obj)
        && json_object_is_type(obj, json_type_string)) {
        const char *state = json_object_get_string(obj);
        if (state && state[0] && strcmp(state, "none") != 0) {
            return 1;
        }
    }
    if (json_object_is_type(scratch_ids, json_type_array)) {
        int length = json_object_array_length(scratch_ids);
        json_object *node_id_obj;
        if (length
            && json_object_object_get_ex(node, "id", &node_id_obj)
            && json_object_is_type(node_id_obj, json_type_int)) {
            int64_t node_id = json_object_get_int64(node_id_obj);
            int index;
            for (index = 0; index < length; index++) {
                json_object *id_obj = json_object_array_get_idx(scratch_ids, index);
                if (!json_object_is_type(id_obj, json_type_int)) continue;
                int64_t scratch_id = json_object_get_int64(id_obj);
                if (scratch_id == node_id) {
                    return 1;
                }
            }
        }
    }
    return 0;
}

static int is_type(json_object *node, const char *type) {
    json_object *obj;
    if (!json_object_object_get_ex(node, "type", &obj)
         || !json_object_is_type(obj, json_type_string)) {
        return 0;
    }
    const char *ntype = json_object_get_string(obj);
    return ntype && strcmp(ntype, type) == 0;
}

#define ACCUM_DATA(levelvar, cond, level, prevlevel, assign, reset) \
do {                                                                \
    int __val = levelvar;                                           \
    if (__val) {                                                    \
        __val += level - prevlevel;                                 \
        if (__val <= 1) { __val = 0; { reset }; }                   \
        levelvar = __val;                                           \
    }                                                               \
    if (!__val && (cond)) {                                         \
        levelvar = 1;                                               \
        { assign };                                                 \
    }                                                               \
} while (0)

#define ACCUM_LEVEL(field, cond, level, prevlevel) \
    ACCUM_DATA(field, cond, level, prevlevel, {}, {})

void i3json_tree_accum_data(json_object *node, json_object *scratch_ids, iter_info *info, struct i3json_print_tree_context *context) {
    ACCUM_LEVEL(context->scratch, i3json_is_scratch(node, scratch_ids), info->level, context->prevlevel);
    ACCUM_LEVEL(context->floating, info->floating, info->level, context->prevlevel);
    ACCUM_DATA(context->wslevel, is_type(node, "workspace"), info->level, context->prevlevel, {
        json_object *tmp;
        if (json_object_object_get_ex(node, "name", &tmp)
            && json_object_is_type(tmp, json_type_string)) {
            context->ws = json_object_get_string(tmp);
        } else {
            context->ws = "";
        }
    }, {
        context->ws = NULL;
    });
    ACCUM_DATA(context->outputlevel, is_type(node, "output"), info->level, context->prevlevel, {
        json_object *tmp;
        if (json_object_object_get_ex(node, "name", &tmp)
            && json_object_is_type(tmp, json_type_string)) {
            context->output = json_object_get_string(tmp);
        } else {
            context->output = "";
        }
    }, {
        context->output = NULL;
    });
    context->prevlevel = info->level;
}

static iter_advice i3json_iter_nodes_recurse(json_object *tree, iter_info *info, i3json_iter_nodes_pred pred, void *ptr) {
    static const char *keys[] = {"nodes", "floating_nodes"};
    int ki;
    int subnodec = 0;
    for (ki = 0; ki < 2; ki++) {
        json_object *tmp;
        if (json_object_object_get_ex(tree, keys[ki], &tmp)
            && json_object_is_type(tmp, json_type_array)) {
            subnodec += json_object_array_length(tmp);
        }
    }
    info->subnodec = subnodec;
    iter_advice adv = pred(tree, info, ptr);
    switch (adv) {
    case ITER_CONT:
        // Descend to children.
        break;
    case ITER_NODESC:
        return ITER_CONT;
    case ITER_ABORT:
    case ITER_ABORT_SUCCESS:
        return adv;
    }
    int nodei = 0;
    for (ki = 0; ki < 2; ki++) {
        json_object *nodes;
        if (json_object_object_get_ex(tree, keys[ki], &nodes)
            && json_object_is_type(nodes, json_type_array)) {
            int nodes_length = json_object_array_length(nodes);
            int i;
            for (i = 0; i < nodes_length; i++) {
                json_object *node = json_object_array_get_idx(nodes, i);
                iter_info subinfo = { .level = info->level + 1, .floating = ki == 1, .nodei = nodei, .nodec = subnodec};
                iter_advice subadv = i3json_iter_nodes_recurse(node, &subinfo, pred, ptr);
                switch (subadv) {
                case ITER_CONT:
                    // Continue iteration.
                    break;
                case ITER_NODESC:
                    // ITER_NODESC is never returned.
                    abort();
                case ITER_ABORT:
                case ITER_ABORT_SUCCESS:
                    return subadv;
                }
                nodei++;
            }
        }
    }
    return ITER_CONT;
}

iter_advice i3json_iter_nodes(json_object *tree, i3json_iter_nodes_pred pred, void *ptr) {
    iter_info info = { .level = 0, .floating = 0, .nodei = 0, .nodec = 1 };
    return i3json_iter_nodes_recurse(tree, &info, pred, ptr);
}
