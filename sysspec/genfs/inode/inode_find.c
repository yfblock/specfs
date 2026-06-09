#include "inode.h"
#include <string.h>  // for strcmp

struct inode *inode_find(struct inode *node, char *name) {
    unsigned int bucket = hash_name(name);
    struct entry *e = node->dir->tb[bucket];
    while (e != NULL) {
        if (strcmp(e->name, name) == 0) {
            return (struct inode *)e->inum;
        }
        e = e->next;
    }
    return NULL;
}