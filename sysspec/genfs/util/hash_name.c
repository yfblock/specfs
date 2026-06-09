#include "util.h"

unsigned int hash_name(char* name) {
    unsigned int hash = 0;

    if (name == NULL || *name == '\0') {
        return hash;
    }

    while (*name != '\0') {
        hash = hash * 131 + (unsigned char)(*name);
        name++;
    }

    return hash & 0x1FF;
}