#include "jsonutil.h"
#include "util.h"
#include "debug.h"
#include "base.h"

#include <string.h>
#include <stdlib.h>

extern const char *jsonutil_get_string(json_object *val) {
    if (!val) {
        return "";
    }
    json_type type = json_object_get_type(val);
    switch (type) {
    case json_type_null:
        return "";
    case json_type_boolean:
        return json_object_get_boolean(val) ? "true" : "false";
    case json_type_double:
    case json_type_int:
    case json_type_string:
        return json_object_get_string(val);
    case json_type_object:
        return NULL;
    case json_type_array:
        return NULL;
    default:
        fprintf(stderr, "unexpectedly got type %d\n", (int) type);
        abort();
    }
}

extern json_object *jsonutil_path_get(json_object *obj, const char *path) {
    for (;;) {
        char *p = strchr(path, '/');
        const char *keyend = p ? p : path + strlen(path);
        int keylen = keyend - path;
        if (json_object_is_type(obj, json_type_array)) {
            debug_print("array key=%.*s\n", keylen, path);
            char *end = NULL;
            int index = strtol(path, &end, 10);
            debug_print("used array key=%.*s\n", (int) (end - path), path);
            if (end != keyend || end == path) {
                return NULL;
            }
            if (index < 0) {
                index += json_object_array_length(obj);
            }
            if (index < 0 || (size_t) index >= json_object_array_length(obj)) {
                return NULL;
            } else {
                obj = json_object_array_get_idx(obj, index);
            }
        } else {
            STACK_SUBSTR(key, path, keylen);
            debug_print("key=%s\n", key);
            if (!json_object_object_get_ex(obj, key, &obj)) {
                return NULL;
            }
        }
        if (!p) {
            return obj;
        } else if (!obj) {
            return NULL;
        } else {
            path = p + 1;
        }
    }
}

extern int jsonutil_object_prop_is_str(json_object *obj, const char *key, const char *str) {
    json_object *str_obj;
    if (!json_object_object_get_ex(obj, key, &str_obj)
        || !json_object_is_type(str_obj, json_type_string)) {
        return 0;
    }
    const char *s = json_object_get_string(str_obj);
    return s && strcmp(s, str) == 0;
}

extern void jsonutil_print_error(const char *str, enum json_tokener_error error) {
    const char *error_str = json_tokener_error_desc(error);
    if (!str) error_str = "unknown error";
    fprintf(stderr, "%s: %s\n", str, error_str);
}
