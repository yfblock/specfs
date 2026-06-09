#include "interface.h"

struct read_ret* atomfs_read(char* path[], unsigned size, unsigned offset) {
    lock(root_inum);
    struct inode* target = locate(root_inum, path);
    if (target == NULL) {
        return NULL;
    }
    if (check_file(target) != 0) {
        return NULL;
    }
    struct read_ret* ret = inode_read(target, size, offset);
    unlock(target);
    return ret;
}