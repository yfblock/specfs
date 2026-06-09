#include "path.h"

struct inode* locate(struct inode* cur, char* path[]) {
    struct inode *current = cur;
    
    for (int i = 0; path[i] != NULL; i++) {
        struct inode *next = inode_find(current, path[i]);
        if (next == NULL) {
            unlock(current);
            return NULL;
        }
        lock(next);
        unlock(current);
        current = next;
    }
    
    return current;
}