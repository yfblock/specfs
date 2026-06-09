#include "interface.h"

struct inode *atomfs_open(char *path[], unsigned mode) {
    // No locks held initially
    lock(root_inum);
    struct inode *target = locate(root_inum, path);
    if (target == NULL) {
        // No locks held (locate guarantees)
        return NULL;
    }
    // target is locked; check_open will unlock it
    int ret = check_open(target, mode);
    if (ret != 0) {
        // check_open already unlocked target
        return NULL;
    }
    // target is now unlocked; no locks held
    return target;
}