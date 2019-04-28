// Client side C/C++ program to demonstrate Socket programming 
#include <stdio.h> 
#include <sys/socket.h> 
#include <stdlib.h> 
#include <netinet/in.h> 
#include <string.h> 
#define PORT 15555
   
int main(int argc, char const *argv[]) { 
    struct sockaddr_in address; 
    int sock = 0, valread; 
    struct sockaddr_in serv_addr; 

    char *cmd = calloc(1024, 1);
    /* strcat(cmd, "'"); */
    for (int i = 1; i < argc; i++) {
        strcat(cmd, argv[i]);
        strcat(cmd, " ");
    }
    /* strcat(cmd, "'\n"); */
    strcat(cmd, "\n");

    char buffer[1024] = {0}; 
    if ((sock = socket(AF_INET, SOCK_STREAM, 0)) < 0) 
    { 
        printf("\n Socket creation error \n"); 
        return -1; 
    } 
   
    memset(&serv_addr, '0', sizeof(serv_addr)); 
   
    serv_addr.sin_family = AF_INET; 
    serv_addr.sin_port = htons(PORT); 

    // Convert IPv4 and IPv6 addresses from text to binary form 
    if(inet_pton(AF_INET, "127.0.0.1", &serv_addr.sin_addr)<=0)  { 
        printf("\nInvalid address/ Address not supported \n"); 
        return -1; 
    } 

   
    if (connect(sock, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) < 0) { 
        printf("\nConnection Failed \n"); 
        return -1; 
    } 
    
    if (send(sock, cmd, strlen(cmd), 0) <= 0){
        printf("Send failed");
    }

    return 0; 
} 
