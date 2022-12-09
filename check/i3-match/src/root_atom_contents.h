#ifndef _ROOT_ATOM_CONTENTS_H_
#define _ROOT_ATOM_CONTENTS_H_

/*
 * vim:ts=4:sw=4:expandtab
 *
 * i3 - an improved dynamic tiling window manager
 * © 2009 Michael Stapelberg and contributors (see also: LICENSE)
 *
 */
#include <xcb/xcb.h>

/*
 * Try to get the contents of the given atom (for example I3_SOCKET_PATH) from
 * the X11 root window and return NULL if it doesn’t work.
 *
 * If the provided XCB connection is NULL, a new connection will be
 * established.
 *
 * The memory for the contents is dynamically allocated and has to be
 * free()d by the caller.
 *
 */
extern char *root_atom_contents(const char *atomname, xcb_connection_t *provided_conn, int screen);

#endif /* _ROOT_ATOM_CONTENTS_H_ */
