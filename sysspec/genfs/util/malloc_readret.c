#include "util.h"

struct read_ret* malloc_readret() {
    struct read_ret *ret = (struct read_ret*)malloc(sizeof(struct read_ret));
    if (ret == NULL) {
        return NULL;
    }
    ret->buf = NULL;
    ret->num = 0;
    return ret;
}