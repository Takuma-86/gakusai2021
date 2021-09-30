//
// Created by ryuzo on 2021/09/29.
//

#ifndef SERVER_ERRORHANDLING_H
#define SERVER_ERRORHANDLING_H

#include <stdarg.h>
#include <stdio.h>
#include <syslog.h>
#include <stdlib.h>

#define MAXLINE 4096

void error_exit(const char *content){
    char buf[MAXLINE + 1];
    snprintf(buf, sizeof(buf), "%s", content);
    perror(buf);
    exit(1);
}
#endif //SERVER_ERRORHANDLING_H
