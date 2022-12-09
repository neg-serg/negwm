/*
 * vim:ts=4:sw=4:expandtab
 *
 * root_atom_contents.c from i3 window manager (libi3/root_atom_contents.c)
 *
 * i3 - an improved dynamic tiling window manager
 * © 2009 Michael Stapelberg and contributors (see also: LICENSE)
 *
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <string.h>
#include <stdbool.h>
#include <stdlib.h>

#include <xcb/xcb.h>
#include <xcb/xcb_aux.h>

#include "root_atom_contents.h"

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
char *root_atom_contents(const char *atomname, xcb_connection_t *provided_conn, int screen) {
    xcb_intern_atom_cookie_t atom_cookie;
    xcb_intern_atom_reply_t *atom_reply;
    char *content = NULL;
    size_t content_max_words = 256;
    xcb_connection_t *conn = provided_conn;

    if (provided_conn == NULL &&
        ((conn = xcb_connect(NULL, &screen)) == NULL ||
         xcb_connection_has_error(conn))) {
        return NULL;
    }

    atom_cookie = xcb_intern_atom(conn, 0, strlen(atomname), atomname);

    xcb_screen_t *root_screen = xcb_aux_get_screen(conn, screen);
    xcb_window_t root = root_screen->root;

    atom_reply = xcb_intern_atom_reply(conn, atom_cookie, NULL);
    if (atom_reply == NULL) {
        goto out_conn;
    }

    xcb_get_property_cookie_t prop_cookie;
    xcb_get_property_reply_t *prop_reply;
    prop_cookie = xcb_get_property_unchecked(conn, false, root, atom_reply->atom,
                                             XCB_GET_PROPERTY_TYPE_ANY, 0, content_max_words);
    prop_reply = xcb_get_property_reply(conn, prop_cookie, NULL);
    if (prop_reply == NULL) {
        goto out_atom;
    }
    if (xcb_get_property_value_length(prop_reply) > 0 && prop_reply->bytes_after > 0) {
        /* We received an incomplete value. Ask again but with a properly
         * adjusted size. */
        // content_max_words += ceil(prop_reply->bytes_after / 4.0);
        content_max_words += (prop_reply->bytes_after + 3) / 4;
        /* Repeat the request, with adjusted size */
        free(prop_reply);
        prop_cookie = xcb_get_property_unchecked(conn, false, root, atom_reply->atom,
                                                 XCB_GET_PROPERTY_TYPE_ANY, 0, content_max_words);
        prop_reply = xcb_get_property_reply(conn, prop_cookie, NULL);
        if (prop_reply == NULL) {
            goto out_atom;
        }
    }
    if (xcb_get_property_value_length(prop_reply) == 0) {
        goto out;
    }
    if (asprintf(&content, "%.*s", xcb_get_property_value_length(prop_reply),
                (char *)xcb_get_property_value(prop_reply)) == -1) {
        content = NULL;
    }

out:
    free(prop_reply);
out_atom:
    free(atom_reply);
out_conn:
    if (provided_conn == NULL)
        xcb_disconnect(conn);
    return content;
}
