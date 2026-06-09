#include "util.h"
#include <string.h>
#include <stdlib.h>

void split_dirs_file(const char *path, char *dirname[], char *filename) {
    // Duplicate the path string so we can modify it
    char *path_copy = malloc_string(path);
    if (!path_copy) return;  // Should not happen given pre‑conditions

    char *token, *saveptr;
    int count = 0;

    // Tokenize the path using '/' as delimiter
    token = strtok_r(path_copy, "/", &saveptr);
    while (token != NULL) {
        // Store each directory component (including the final one for now)
        if (count < MAX_PATH_LEN) {
            dirname[count] = malloc_string(token);
        }
        count++;
        token = strtok_r(NULL, "/", &saveptr);
    }

    // If we found any tokens, the last one is the filename
    if (count > 0) {
        int last = count - 1;
        // Copy the filename into the provided buffer
        strcpy(filename, dirname[last]);
        // Free the allocated string and set the pointer to NULL
        free(dirname[last]);
        dirname[last] = NULL;
    }
    // (If no tokens were found, dirname and filename remain unchanged)

    // Free the temporary copy of the path
    free(path_copy);
}