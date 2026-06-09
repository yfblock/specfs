#include "interface.h"

int atomfs_truncate(char* path[], unsigned offset) {
    if (offset > MAX_FILE_SIZE) {
        return -1;
    }

    lock(root_inum);
    struct inode *target = locate(root_inum, path);
    if (target == NULL) {
        // locate released the lock of root_inum, no locks held
        return -1;
    }

    // target is now locked
    if (check_file(target) != 0) {
        // check_file released the lock on failure
        return -1;
    }

    // target is still locked
    inode_truncate(target, offset);
    unlock(target);

    return 0;
}