#include "util.h"
#include <string.h>
#include <stdlib.h>
#include <assert.h>

void split_dirs(const char *path, char *dirname[])
{
    // 1. Create a temporary, modifiable copy of the input path.
    size_t len = strlen(path);
    char *temp = (char *)malloc(len + 1);
    if (temp == NULL) {
        return;  // Allocation failure – nothing we can do
    }
    strcpy(temp, path);

    // 2. Tokenize by '/'
    char *saveptr;
    char *token = strtok_r(temp, "/", &saveptr);
    int count = 0;

    while (token != NULL) {
        // 3a. Assert that the number of tokens does not exceed MAX_PATH_LEN.
        assert(count < MAX_PATH_LEN);
        // 3b. Assert that the token length does not exceed MAX_FILE_LEN.
        assert(strlen(token) <= MAX_FILE_LEN);
        // 3c. Create a dynamically allocated copy using malloc_string.
        dirname[count] = malloc_string(token);
        // 3d. Store the pointer and advance.
        count++;
        token = strtok_r(NULL, "/", &saveptr);
    }

    // 4. Free the temporary copy.
    free(temp);
}