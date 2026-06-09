#include "util.h"

void unlock(struct inode* inum) {
    mcs_node_t *me = inum->hd;
    inum->mutex = 0;
    mcs_mutex_unlock(inum->impl, me);
    free(me);
}