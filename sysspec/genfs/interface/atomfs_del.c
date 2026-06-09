#include "interface.h"

int atomfs_del(char* path[], char* name) {
    struct inode *parent;

    // Lock the root inode before traversal
    lock(root_inum);
    parent = locate(root_inum, path);

    // If locate returns NULL, traversal failed (locks already released)
    if (parent == NULL) {
        return -1;
    }

    // parent is locked; check if deletion is allowed
    int del_ok = check_del(parent, name);
    if (del_ok != 0) {
        // check_del released the lock on failure
        return -1;
    }

    // parent is still locked; perform deletion
    struct inode *deleted = inode_delete(parent, name);
    // Release the parent's lock
    unlock(parent);

    if (deleted == NULL) {
        // Deletion failed (should not happen if check_del passed, but handle gracefully)
        return -1;
    }

    // Free the deleted inode's resources
    dispose_inode(deleted);
    return 0;
}