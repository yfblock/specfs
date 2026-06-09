#include "util.h"

char** calculate(char* srcpath[], char* dstpath[]) {
    unsigned i = 0;
    /* Find length of longest common prefix */
    while (srcpath[i] != NULL && dstpath[i] != NULL) {
        const char *s = srcpath[i];
        const char *d = dstpath[i];
        /* Compare strings character by character */
        while (*s && *d && *s == *d) {
            ++s;
            ++d;
        }
        if (*s != *d) {
            break;               /* mismatch found */
        }
        ++i;                     /* component matches */
    }
    unsigned count = i;

    /* Allocate array for count components plus NULL terminator */
    char **compath = malloc_path(count + 1);
    if (compath == NULL) {
        return NULL;             /* allocation failure (should not happen per guarantee) */
    }

    /* Copy each common component */
    for (unsigned j = 0; j < count; ++j) {
        compath[j] = malloc_string(srcpath[j]);
        /* malloc_string is guaranteed to succeed */
    }
    compath[count] = NULL;       /* terminate the array */

    return compath;
}