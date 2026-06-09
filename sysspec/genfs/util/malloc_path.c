#include "util.h"

char** malloc_path(unsigned len) {
    char** path = (char**)malloc(len * sizeof(char*));
    if (path == NULL) {
        return NULL;
    }
    for (unsigned i = 0; i < len; i++) {
        path[i] = NULL;
    }
    return path;
}