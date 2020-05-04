#include <stdio.h>
#include <string.h>
#include <stdlib.h>

#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>

#define PORT 15555

size_t strlcat(char *dst, const char *src, size_t size) {
    size_t srclen;
    size_t dstlen;
    dstlen = strlen(dst);
    size -= dstlen + 1;
    if (!size) {
        return (dstlen);
    }
    srclen = strlen(src);
    if (srclen > size) {
        srclen = size;
    }
    memcpy(dst + dstlen, src, srclen);
    dst[dstlen + srclen] = '\0';
    return (dstlen + srclen);
}

int main(int argc, char const *argv[]) {
    struct sockaddr_in serv_addr;
    int sock = 0;
    char cmd[1024] = {0};

    for (int i = 1; i < argc; i++) {
        strlcat(cmd, argv[i], 128);
        strlcat(cmd, " ", 128);
    }
    strlcat(cmd, "\n", 128);

    if ((sock = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
        puts("\n Socket creation error \n");
        return -1;
    }

    memset(&serv_addr, '\0', sizeof(serv_addr));

    serv_addr.sin_family = AF_INET;
    serv_addr.sin_port = htons(PORT);

    if(inet_pton(AF_INET, "127.0.0.1", &serv_addr.sin_addr)<=0) {
        printf("\nInvalid address/ Address not supported \n");
        return -1;
    }


    if (connect(sock, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) < 0) {
        printf("\nConnection Failed \n");
        return -1;
    }

    if (send(sock, cmd, strnlen(cmd, 1024), 0) <= 0) {
        printf("Send failed");
    }
    return 0;
}
