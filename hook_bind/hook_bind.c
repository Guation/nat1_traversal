#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <dlfcn.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <syslog.h>
#include <string.h>
#include <time.h>
#include <stdbool.h>

typedef int (*orig_bind_type)(int, const struct sockaddr *, socklen_t);

int bind(int sockfd, const struct sockaddr *addr, socklen_t addrlen) {
    static orig_bind_type orig_bind = NULL;
    int opt = 1;
    bool set_opt = false;
    if (!orig_bind) {
        orig_bind = (orig_bind_type)dlsym(RTLD_NEXT, "bind");
        if (!orig_bind) {
            syslog(LOG_ERR, "Failed to find original bind function");
            return -1;
        }
    }
    
    if (addr->sa_family == AF_INET) {
        struct sockaddr_in *addr_in = (struct sockaddr_in *)addr;
        char ip_str[INET_ADDRSTRLEN];
        uint16_t port = ntohs(addr_in->sin_port);
        inet_ntop(AF_INET, &(addr_in->sin_addr), ip_str, INET_ADDRSTRLEN);
        
        syslog(LOG_INFO, "Hooked bind: PID=%d, FD=%d, IP=%s, Port=%d", 
               getpid(), sockfd, ip_str, port);
        
        printf("Hooked bind: PID=%d, FD=%d, IP=%s, Port=%d\n", 
               getpid(), sockfd, ip_str, port);
        if (port != 0) {
            set_opt = true;
        }
    } else if (addr->sa_family == AF_INET6) {
        struct sockaddr_in6 *addr_in6 = (struct sockaddr_in6 *)addr;
        char ip_str[INET6_ADDRSTRLEN];
        uint16_t port = ntohs(addr_in6->sin6_port);
        inet_ntop(AF_INET6, &(addr_in6->sin6_addr), ip_str, INET6_ADDRSTRLEN);
        
        syslog(LOG_INFO, "Hooked bind: PID=%d, FD=%d, IP=%s, Port=%d", 
               getpid(), sockfd, ip_str, port);
        
        printf("Hooked bind: PID=%d, FD=%d, IP=%s, Port=%d\n", 
               getpid(), sockfd, ip_str, port);
        if (port != 0) {
            set_opt = true;
        }
    } else {
        syslog(LOG_INFO, "Hooked bind: PID=%d, FD=%d, Family=%d (unsupported)", 
               getpid(), sockfd, addr->sa_family);
        
        printf("Hooked bind: PID=%d, FD=%d, Family=%d (unsupported)\n", 
               getpid(), sockfd, addr->sa_family);
    }
    if (set_opt) {
        if (setsockopt(sockfd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt))) {
            perror("setsockopt failed");
            return -1;
        }
        if (setsockopt(sockfd, SOL_SOCKET, SO_REUSEPORT, &opt, sizeof(opt))) {
            perror("setsockopt failed");
            return -1;
        } else {
            syslog(LOG_INFO, "Hooked bind: PID=%d, FD=%d, setsockopt SO_REUSEPORT", 
                getpid(), sockfd);
         
            printf("Hooked bind: PID=%d, FD=%d, setsockopt SO_REUSEPORT\n", 
                getpid(), sockfd);
        }
    }
    return orig_bind(sockfd, addr, addrlen);
}
