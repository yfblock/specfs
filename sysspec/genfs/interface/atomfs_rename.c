#include "interface.h"

int atomfs_rename(char* srcpath[], char* dstpath[], char* srcname, char* dstname) {
    // Phase 1: Traverse the common path
    char** common = calculate(srcpath, dstpath);
    if (common == NULL) {
        return -1;
    }
    int common_len = getlen(common);
    lock(root_inum);
    struct inode* parent = locate(root_inum, common);
    free_path(common);
    if (parent == NULL) {
        // No lock held
        return -1;
    }

    // Phase 2: Traverse remaining paths
    // Compute remaining path components for src and dst
    int src_len = getlen(srcpath);
    int dst_len = getlen(dstpath);
    // The remaining paths are the components after the common prefix
    char** src_remain = srcpath + common_len;
    char** dst_remain = dstpath + common_len;

    struct inode* srcdir = locate_hold(parent, src_remain);
    if (srcdir == NULL) {
        // Only parent lock remains (locate_hold leaves parent locked on failure)
        unlock(parent);
        return -1;
    }
    // Now parent and srcdir are locked (may be same)
    struct inode* dstdir = locate_hold(parent, dst_remain);
    if (dstdir == NULL) {
        // Release srcdir and parent locks appropriately
        unlock(srcdir);
        check_unlock(parent, srcdir, NULL);
        return -1;
    }
    // Release parent lock if not equal to srcdir or dstdir
    check_unlock(parent, srcdir, dstdir);

    // Phase 3: Checks and operations
    int ret = check_src_exist_dst_delete(srcdir, dstdir, srcname, dstname);
    if (ret != 0) {
        // All locks released by check_src_exist_dst_delete
        return -1;
    }

    // Perform rename
    struct inode* srcinode = inode_delete(srcdir, srcname);
    // srcinode should not be NULL according to precondition
    struct inode* dstinode = inode_delete(dstdir, dstname);
    if (dstinode != NULL) {
        unlock(dstinode);
        dispose_inode(dstinode);
    }
    inode_insert(dstdir, srcinode, dstname);

    unlock2dir(srcdir, dstdir);
    return 0;
}