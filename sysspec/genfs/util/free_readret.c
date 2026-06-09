#include "util.h"

void free_readret(struct read_ret *p) {
    if (p) {
        free(p->buf);
        free(p);
    }
}