#include "inode.h"
#include <string.h>

struct inode* inode_delete(struct inode* cur, char* name) {
    unsigned int h = hash_name(name);
    struct entry **pp = &cur->dir->tb[h];
    struct entry *en = *pp;
    while (en != NULL) {
        if (strcmp(en->name, name) == 0) {
            *pp = en->next;
            void *inum = en->inum;
            free_entry(en);
            cur->size -= 1;
            return (struct inode*)inum;
        }
        pp = &en->next;
        en = en->next;
    }
    return NULL;
}