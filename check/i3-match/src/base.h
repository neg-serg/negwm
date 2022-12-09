#ifndef _BASE_H_
#define _BASE_H_

#ifndef __GNUC__
#  define __attribute__(x) /*nothing*/
#endif

#define __unused __attribute__((unused))

#define JSON_TOKENER_DEPTH 128

#endif
