
#include "sb.h"
#include "debug.h"

#include <stdlib.h>
#include <string.h>
#include <assert.h>
#ifndef DONT_USE_MALLOC_USABLE_SIZE
#include <malloc.h>
#endif

static void sb_ensure_size(string_builder *sb, size_t minsize) {
    if (minsize > sb->bufsz) {
        size_t minlen = minsize;
        size_t newcount = (sb->bufsz >> 1) + sb->bufsz;
        if (newcount < 64) newcount = 64;
        if (minlen > newcount) newcount = minlen;
        char *newbuf;
        if (sb->flags & SB_FLAG_EXT_BUF) {
            debug_print("move to own buffer of size %ld\n", newcount);
            newbuf = malloc(newcount);
            malloc_check(newbuf);
            memcpy(newbuf, sb->buf, sb->len + 1);
            sb->flags &= ~SB_FLAG_EXT_BUF;
        } else {
            debug_print("realloc to size %ld\n", newcount);
            newbuf = realloc(sb->buf, newcount);
            malloc_check(newbuf);
        }
        assert(newbuf);
        sb->buf = newbuf;
        #ifndef DONT_USE_MALLOC_USABLE_SIZE
        newcount = malloc_usable_size(newbuf);
        debug_print("got a %ld byte allocation\n", newcount);
        #endif
        sb->bufsz = newcount;
    }
}

void sb_free(string_builder *sb) {
    if (!(sb->flags & SB_FLAG_EXT_BUF)) {
        debug_print("freeing buffer of size %ld\n", sb->bufsz);
        free(sb->buf);
    } else {
        debug_print("not freeing extern buffer of size %ld\n", sb->bufsz);
    }
    sb->buf = NULL;
    sb->bufsz = 0;
    sb->len = 0;
}

char *sb_disown(string_builder *sb) {
    char *buf = sb->buf;
    sb->buf = NULL;
    sb->bufsz = 0;
    sb->len = 0;
    return buf;
}

void sb_trunc(string_builder *sb, size_t len) {
    debug_print("len=%ld\n", len);
    assert(len <= sb->len);
    // Need to check this because buf may be NULL at length 0.
    if (sb->len > 0) {
        sb->len = len;
        sb->buf[len] = '\0';
    }
}

void sb_replacen(string_builder *sb, size_t rep_pos, size_t rep_len, const char *ins_str, size_t ins_len) {
    size_t len = sb->len;
    debug_print("rep_pos=%ld rep_len=%ld ins_len=%ld\n", rep_pos, rep_len, ins_len);
    assert(rep_pos <= len);
    assert(rep_len + rep_pos <= len);
    size_t szdiff = ins_len - rep_len;
    // move right part
    size_t mvstart = rep_pos + rep_len;
    size_t mvsize = len - mvstart;
    sb_ensure_size(sb, len + szdiff + 1);
    debug_print("mvstart=%ld mvsize=%ld szdiff=%ld\n", mvstart, mvsize, szdiff);
    if (mvsize > 0 && szdiff != 0) {
        memmove(sb->buf + mvstart + szdiff, sb->buf + mvstart, mvsize);
    }
    // insert new part
    if (ins_len > 0) {
        memcpy(sb->buf + rep_pos, ins_str, ins_len);
    }
    len += szdiff;
    assert(len < sb->bufsz);
    sb->buf[len] = '\0';
    sb->len = len;
    debug_print("buf=%s\n", sb->buf);
}

void sb_pushn(string_builder *sb, const char *s, size_t len) {
    sb_ensure_size(sb, sb->len + len + 1);
    memcpy(sb->buf + sb->len, s, len);
    sb->len += len;
    assert(sb->len < sb->bufsz);
    sb->buf[sb->len] = '\0';
}

void sb_push(string_builder *sb, const char *s) {
    sb_pushn(sb, s, strlen(s));
}

void sb_replacefv(string_builder *sb, size_t rep_pos, size_t rep_len, const char *fmt, va_list ap) {
    va_list ap2;
    va_copy(ap2, ap);
    size_t ins_len = vsnprintf(NULL, 0, fmt, ap);
    size_t len = sb->len;
    debug_print("rep_pos=%ld rep_len=%ld ins_len=%ld\n", rep_pos, rep_len, ins_len);
    assert(rep_pos <= len);
    assert(rep_len + rep_pos <= len);
    size_t szdiff = ins_len - rep_len;
    sb_ensure_size(sb, len + szdiff + 1);
    // move right part
    size_t mvstart = rep_pos + rep_len;
    size_t mvsize = len - mvstart;
    debug_print("mvstart=%ld mvsize=%ld szdiff=%ld\n", mvstart, mvsize, szdiff);
    if (mvsize > 0 && szdiff != 0) {
        memmove(sb->buf + mvstart + szdiff, sb->buf + mvstart, mvsize);
    }
    // insert new part
    if (ins_len > 0) {
        char tmpchar = sb->buf[rep_pos + ins_len]; // vsnprintf writes a \0 here
        size_t l = vsnprintf(sb->buf + rep_pos, ins_len + 1, fmt, ap2);
        sb->buf[rep_pos + ins_len] = tmpchar; // restore char
        assert(l == ins_len);
    }
    len += szdiff;
    assert(len < sb->bufsz);
    sb->buf[len] = '\0';
    sb->len = len;
    debug_print("buf=%s\n", sb->buf);
    va_end(ap2);
}

void sb_replacef(string_builder *sb, size_t rep_pos, size_t rep_len, const char *fmt, ...) {
    va_list ap;
    va_start(ap, fmt);
    sb_replacefv(sb, rep_pos, rep_len, fmt, ap);
    va_end(ap);
}

void sb_pushfv(string_builder *sb, const char *fmt, va_list ap) {
    va_list ap2;
    va_copy(ap2, ap);
    size_t ins_len = vsnprintf(NULL, 0, fmt, ap);
    if (ins_len > 0) {
        size_t len = sb->len;
        sb_ensure_size(sb, len + ins_len + 1);
        char tmpchar = sb->buf[len + ins_len]; // vsnprintf writes a \0 here
        size_t l = vsnprintf(sb->buf + len, ins_len + 1, fmt, ap2);
        sb->buf[len + ins_len] = tmpchar; // restore char
        assert(l == ins_len);
        len += ins_len;
        assert(len < sb->bufsz);
        sb->buf[len] = '\0';
        sb->len = len;
    }
    va_end(ap2);
    debug_print("buf=%s\n", sb->buf);
}

void sb_pushf(string_builder *sb, const char *fmt, ...) {
    va_list ap;
    va_start(ap, fmt);
    sb_pushfv(sb, fmt, ap);
    va_end(ap);
}

