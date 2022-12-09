
#ifndef _I3JSON_H_
#define _I3JSON_H_

#include "base.h"

#include <json-c/json_object.h>
#include <stdio.h>

typedef enum iter_advice {
    ITER_CONT = 0,
    ITER_NODESC = 1,
    ITER_ABORT = 2,
    ITER_ABORT_SUCCESS = 3
} iter_advice;

typedef struct iter_info {
    int level;
    int floating;
    int nodei;
    int nodec;
    int subnodec;
} iter_info;

typedef iter_advice (i3json_iter_nodes_pred)(json_object *node, iter_info *info, void *ptr);

extern iter_advice i3json_iter_nodes(json_object *tree, i3json_iter_nodes_pred pred, void *ptr);

typedef enum matcher_type {
    MT_EQUALS = 0<<0,
    MT_STARTS = 1<<0,
    MT_ENDS = 2<<0,
    MT_CONTAINS = 3<<0,
    MT_NOT = 1<<4,
    MT_MASK_BASE = 0x0f
} matcher_type;

typedef struct i3json_matcher {
    unsigned int type;
    const char *key;
    size_t key_len;
    const char *pattern;
    size_t pattern_len;
} i3json_matcher;

extern int i3json_parse_matcher(const char *strdef, i3json_matcher *out);

extern int i3json_parse_operator(const char *str);

extern void i3json_make_matcher(const char *key, const char *pattern, unsigned int type, i3json_matcher *out);

extern int i3json_matcher_match_value(const char* value, i3json_matcher *matcher);

extern int i3json_matcher_match(json_object *node, i3json_matcher *matchers);

typedef const char *(i3json_value_getter)(const char *key, void *ptr);

extern int i3json_matchers_match_ex(int matcherc, i3json_matcher *matchers, i3json_value_getter *getter, void *ptr);

extern int i3json_matchers_match_node(json_object *node, int matcherc, i3json_matcher *matchers);

extern json_object *i3json_matchers_match_tree(json_object *tree, int matcherc, i3json_matcher *matchers);

extern int i3json_matcher_cmp_key(i3json_matcher *matcher, const char* key);

struct i3json_print_tree_context {
    int prevlevel;
    int scratch;
    int floating;
    int wslevel;
    const char *ws;
    int outputlevel;
    const char *output;
};

#define I3JSON_EMPTY_PRINT_TREE_CONTEXT {.prevlevel = 0, .scratch = 0, .floating = 0}

extern void i3json_tree_accum_data(json_object *node, json_object *scratch_ids, iter_info *info, struct i3json_print_tree_context *context);

#endif /* _I3JSON_H_ */
