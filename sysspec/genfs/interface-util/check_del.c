#include "interface-util.h"

int check_del(struct inode *cur, char *name) {
    struct inode *target;

    // Pre-condition: lock for cur is held.
    // Check for NULL cur (though pre-condition says valid, but for safety)
    if (cur == NULL) {
        // Cannot unlock NULL; but this case should not happen per spec.
        return 1;
    }

    // Find the entry
    target = inode_find(cur, name);
    if (target == NULL) {
        // Entry does not exist -> failure, release cur lock
        unlock(cur);
        return 1;
    }

    // Check if deletion is permissible: file or empty directory
    if (target->mode != DIR_MODE || target->size == 0) {
        // Permissible: lock the target inode, keep cur lock held
        lock(target);
        return 0;
    } else {
        // Not permissible: directory non-empty, release cur lock
        unlock(cur);
        return 1;
    }
}