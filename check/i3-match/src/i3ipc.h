
#ifndef _I3IPC_H_
#define _I3IPC_H_

#include <i3/ipc.h>

#include <stdio.h>

enum {
    ST_UNKNOWN = -1,
    ST_OK = 0,
    ST_INVALID_HEADER,
    ST_SOCK_ERROR,
    ST_DATA_ERROR,
    ST_INVALID_RESPONSE,
    ST_RECYCLED,
};

typedef struct i3_msg {
    int status;
    unsigned long type;
    char *data;
    size_t len;
    size_t blen;
} i3_msg;
#define EMPTY_I3_MSG {ST_UNKNOWN, -1, NULL, 0, 0}

extern int i3ipc_open_socket(const char *path, int swaymode);

extern int i3ipc_send_message(int sock, unsigned long type, const char *data);

extern int i3ipc_recv_message(int sock, i3_msg *msg);

extern int i3ipc_request(int s, unsigned long type, const char *data, i3_msg *msg);

extern int i3ipc_send_commandf(int sock, char *buf, size_t size, char *fmt, ...);

extern int i3ipc_send_ccommandf(int sock, char *buf, size_t size, char *fmt, ...);

extern int i3ipc_send_ccommand(int sock, const char *data);

extern void i3ipc_print_error(int status);

extern int i3ipc_recv_skip(int sock, i3_msg *msg);

extern void del_i3_msg(i3_msg *msg);
extern void i3ipc_msg_recycle(i3_msg *msg);

#endif /* _I3IPC_H_ */
