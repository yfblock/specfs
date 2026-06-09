#include "interface-util.h"

int check_src_exist_dst_delete(struct inode *srcdir, struct inode *dstdir, char *srcname, char *dstname) {
    struct inode *srcinode = NULL;
    struct inode *dstinode = NULL;
    int src_locked = 0;
    int dst_locked = 0;

    // Step 1: Check source existence
    srcinode = inode_find(srcdir, srcname);
    if (srcinode == NULL) {
        unlock2dir(srcdir, dstdir);
        return 1;
    }

    // Step 2: Check destination directory validity
    if (dstdir->mode != DIR_MODE || dstdir->size >= MAX_DIR_SIZE) {
        unlock2dir(srcdir, dstdir);
        return 1;
    }

    // Step 3: Check destination entry
    dstinode = inode_find(dstdir, dstname);
    if (dstinode != NULL) {
        // Lock srcinode and dstinode
        lock(srcinode);
        src_locked = 1;
        if (srcinode != dstinode) {
            lock(dstinode);
            dst_locked = 1;
        } else {
            // Same inode: treat the lock as dstinode lock as well
            dst_locked = 1; // but no second lock needed
        }

        // Check compatibility
        if (srcinode != dstinode) {
            // Types must be compatible: both directories or both non-directories
            int src_is_dir = (srcinode->mode == DIR_MODE);
            int dst_is_dir = (dstinode->mode == DIR_MODE);
            if (src_is_dir != dst_is_dir) {
                // Incompatible types -> failure
                goto failure;
            }
            // If dstinode is a directory, it must be empty
            if (dst_is_dir && dstinode->size != 0) {
                goto failure;
            }
        }
        // If same inode, validity is automatically held, no extra checks.

        // Release srcinode lock (if different from dstinode)
        if (srcinode != dstinode) {
            unlock(srcinode);
            src_locked = 0;
        } else {
            // If same, we keep the lock (it will remain as dstinode lock)
            src_locked = 0; // Not held separately
        }

        // Success: keep locks on srcdir, dstdir, and dstinode (if existed)
        return 0;
    }

    // Destination does not exist, success with only srcdir and dstdir locks held
    return 0;

failure:
    // Release any held locks
    if (src_locked) {
        unlock(srcinode);
    }
    if (dst_locked) {
        // If srcinode == dstinode and we held that lock, it will be released here.
        // But we already set src_locked = 0 for same case, so dst_locked still true.
        unlock(dstinode);
    }
    unlock2dir(srcdir, dstdir);
    return 1;
}