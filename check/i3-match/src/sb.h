#ifndef _SB_H_
#define _SB_H_

#include "base.h"

#include <stdio.h>
#include <stdarg.h>

#define SB_FLAG_EXT_BUF 0x0001

typedef struct {
    char *buf;
    size_t bufsz;
    size_t len;
    int flags;
} string_builder;

#define EMPTY_STRING_BUILDER {NULL, 0, 0, 0}
#define SB_WITH_EXT_BUF(buf, size) {(buf), (size), 0, SB_FLAG_EXT_BUF}

extern void sb_free(string_builder *sb);

extern char *sb_disown(string_builder *sb);

extern void sb_trunc(string_builder *sb, size_t len);

extern void sb_replacen(string_builder *sb, size_t rep_pos, size_t rep_len, const char *ins_str, size_t ins_len);

extern void sb_pushn(string_builder *sb, const char *s, size_t len);

extern void sb_push(string_builder *sb, const char *s);

extern void sb_replacefv(string_builder *sb, size_t rep_pos, size_t rep_len, const char *fmt, va_list ap);

extern void sb_replacef(string_builder *sb, size_t rep_pos, size_t rep_len, const char *fmt, ...)
            __attribute__((format(printf, 4, 5)));

extern void sb_pushfv(string_builder *sb, const char *fmt, va_list ap);

extern void sb_pushf(string_builder *sb, const char *fmt, ...)
            __attribute__((format(printf, 2, 3)));

#endif /* _SB_H_ */
