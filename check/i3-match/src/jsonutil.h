
#ifndef _JSONUTIL_H_
#define _JSONUTIL_H_

#include "sb.h"

#include <json-c/json_object.h>
#include <json-c/json_tokener.h>

#include <stdio.h>

extern void jsonutil_print_cb_sb_push(void *ctx, const char *str, size_t len);

extern const char *jsonutil_get_string(json_object *val);

extern json_object *jsonutil_path_get(json_object *obj, const char *path);

extern int jsonutil_object_prop_is_str(json_object *obj, const char *key, const char *str);

extern void jsonutil_print_error(const char *str, enum json_tokener_error error);

#endif /* _JSONUTIL_H_ */
