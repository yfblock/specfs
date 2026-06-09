#include "interface.h"

int atomfs_ins(char* path[], char* name, int mode, unsigned maj, unsigned min) {
    lock(root_inum);
    struct inode *cur = locate(root_inum, path);
    if (cur == NULL) {
        return -1;
    }
    if (check_ins(cur, name) != 0) {
        return -1;
    }
    struct inode *new_inode = malloc_inode(mode, maj, min);
    inode_insert(cur, new_inode, name);
    unlock(cur);
    return 0;
}