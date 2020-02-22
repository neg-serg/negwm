#include <stdio.h>
#include <sys/socket.h>
#include <stdlib.h>
#include <netinet/in.h>
#include <string.h>
#include <arpa/inet.h>
#include <bsd/string.h>

#define PORT 15555

int main(int argc, char const *argv[]) {
    struct sockaddr_in serv_addr;

    int sock = 0;

    char *cmd = calloc(1024, 1);
    for (int i = 1; i < argc; i++) {
        strlcat(cmd, argv[i], 128);
        strlcat(cmd, " ", 128);
    }
    strlcat(cmd, "\n", 128);

    if ((sock = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
        puts("\n Socket creation error \n");
        free(cmd);
        return -1;
    }

    memset(&serv_addr, '0', sizeof(serv_addr));

    serv_addr.sin_family = AF_INET;
    serv_addr.sin_port = htons(PORT);

    if(inet_pton(AF_INET, "127.0.0.1", &serv_addr.sin_addr)<=0) {
        printf("\nInvalid address/ Address not supported \n");
        free(cmd);
        return -1;
    }


    if (connect(sock, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) < 0) {
        printf("\nConnection Failed \n");
        free(cmd);
        return -1;
    }

    if (send(sock, cmd, strnlen(cmd, 1024), 0) <= 0) {
        printf("Send failed");
    }

    free(cmd);
    return 0;
}
