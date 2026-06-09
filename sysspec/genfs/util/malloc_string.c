#include "util.h"

char* malloc_string(const char* name) {
    size_t len = strlen(name);
    char* copy = malloc(len + 1);
    strcpy(copy, name);
    return copy;
}