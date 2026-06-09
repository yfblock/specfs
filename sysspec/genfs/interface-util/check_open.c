#include "interface-util.h"

int check_open(struct inode *inum, unsigned mode) {
    if (inum == NULL) {
        return 1;
    }

    int result;
    if (inum->mode == DIR_MODE && mode == DIR_MODE) {
        result = 0;
    } else if (inum->mode != DIR_MODE && mode != DIR_MODE) {
        result = 0;
    } else {
        result = 1;
    }

    unlock(inum);
    return result;
}