#include "interface-util.h"

int check_ins(struct inode *cur, char *name) {
    // Ensure cur is non-NULL (pre-condition implies lock is held, so it should be valid)
    if (cur == NULL) {
        return 1;
    }

    // Check if cur is a directory
    if (cur->mode != DIR_MODE) {
        unlock(cur);
        return 1;
    }

    // Check if directory is full
    if (cur->size >= MAX_DIR_SIZE) {
        unlock(cur);
        return 1;
    }

    // Check if an entry with the given name already exists
    struct inode *existing = inode_find(cur, name);
    if (existing != NULL) {
        unlock(cur);
        return 1;
    }

    // All conditions satisfied, insertion is possible
    return 0;
}