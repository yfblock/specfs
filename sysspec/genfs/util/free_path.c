#include "util.h"

void free_path(char** path) {
    if (path == NULL) return;
    for (size_t i = 0; path[i] != NULL; i++) {
        free(path[i]);
    }
    free(path);
}