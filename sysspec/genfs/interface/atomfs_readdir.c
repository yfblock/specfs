#include "interface.h"

char **atomfs_readdir(char *path[]) {
    // No lock held initially; lock root_inum for locate traversal.
    lock(root_inum);

    // Traverse path; locate will release root_inum lock and acquire target lock if found,
    // otherwise releases all locks and returns NULL.
    struct inode *target = locate(root_inum, path);
    if (target == NULL) {
        return NULL;
    }

    // Target is locked; verify it is a directory.
    if (check_dir(target) != 0) {
        // check_dir releases the lock on failure.
        return NULL;
    }

    // Target is locked and is a directory.
    // Allocate directory content array (size target->size + 1 entries for NULL terminator).
    char **dircontent = malloc_dir_content(target->size + 1);
    if (dircontent == NULL) {
        unlock(target);
        return NULL;
    }

    // Fill directory entries (fill_dir handles NULL termination).
    fill_dir(target, dircontent);

    // Release target lock before returning.
    unlock(target);
    return dircontent;
}