
#ifndef _F__DEBUG_H_
#define _F__DEBUG_H_

#ifndef DEBUG
#define DEBUG 0
#endif

#define debug_print(fmt, ...) \
    do { if (DEBUG) fprintf(stderr, "%s:%d:%s(): " fmt, __FILE__, __LINE__, __func__, ##__VA_ARGS__); } while (0)

#define malloc_check(p) \
    do { if (!p) abort_malloc_fail(); } while (0)
#define abort_malloc_fail() \
    do { fprintf(stderr, "%s:%d:%s(): malloc failed\n", __FILE__, __LINE__, __func__); abort(); } while (0)

#endif /* _f__DEBUG_H_ */
