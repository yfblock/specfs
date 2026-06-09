#include "interface.h"

extern struct inode *root_inum;

struct getattr_ret* atomfs_getattr(char* path[]) {
    lock(root_inum);
    struct inode *target = locate(root_inum, path);
    if (target == NULL) {
        return NULL;
    }
    struct getattr_ret *ret = malloc_getattr_ret(target, target->mode, target->size, target->maj, target->min);
    unlock(target);
    return ret;
}