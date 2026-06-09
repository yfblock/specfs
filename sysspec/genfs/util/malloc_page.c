#include "util.h"

extern void* malloc(size_t size);
extern void* memset(void* s, int c, size_t n);

unsigned char* malloc_page() {
    void* ptr = malloc(PG_SIZE);
    if (ptr == NULL) {
        return NULL;
    }
    memset(ptr, 0, PG_SIZE);
    return (unsigned char*)ptr;
}