#include "util.h"

struct inode* malloc_inode(int mode, unsigned maj, unsigned min) {
    // Allocate and zero-initialize the inode structure
    struct inode *in = malloc(sizeof(struct inode));
    if (!in) {
        return NULL;
    }
    memset(in, 0, sizeof(struct inode));

    // Set the common fields
    in->mode = mode;
    in->maj = maj;
    in->min = min;
    in->impl = mcs_mutex_create();  // guaranteed non-NULL

    // Initialize either the file index or directory table
    if (mode != DIR_MODE) {
        // Regular file case
        in->file = malloc(sizeof(struct indextb));
        if (!in->file) {
            // Free the already allocated mutex and inode on failure
            // Note: no mutex destroy function provided, but we assume
            // mcs_mutex_create never fails; cleanup for completeness.
            free(in);
            return NULL;
        }
        memset(in->file, 0, sizeof(struct indextb));
        in->dir = NULL;
    } else {
        // Directory case
        in->dir = malloc(sizeof(struct dirtb));
        if (!in->dir) {
            free(in);
            return NULL;
        }
        memset(in->dir, 0, sizeof(struct dirtb));
        in->file = NULL;
    }

    return in;
}