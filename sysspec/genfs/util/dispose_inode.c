#include "util.h"

void dispose_inode(struct inode* inum) {
    if (!inum) return;

    if (inum->mode == DIR_MODE) {
        struct dirtb *dir = inum->dir;
        if (dir) {
            for (int i = 0; i < DIRTB_NUM; i++) {
                struct entry *entry = dir->tb[i];
                while (entry) {
                    struct entry *next = entry->next;
                    if (entry->name) free(entry->name);
                    free(entry);
                    entry = next;
                }
            }
            free(dir);
        }
    } else if (inum->mode == FILE_MODE) {
        struct indextb *file = inum->file;
        if (file) {
            for (int i = 0; i < INDEXTB_NUM; i++) {
                if (file->index[i]) {
                    free(file->index[i]);
                }
            }
            free(file);
        }
    }

    if (inum->impl) {
        mcs_mutex_destroy(inum->impl);
    }
    free(inum);
}