#include "inode.h"

int inode_insert(struct inode* cur, struct inode* inum, char* name) {
    // Compute bucket index
    unsigned int n = hash_name(name) % DIRTB_NUM;

    // Allocate copy of the name
    char *name_copy = malloc_string(name);
    if (!name_copy) {
        return 1;
    }

    // Allocate new entry
    struct entry *new_entry = malloc_entry();
    if (!new_entry) {
        free(name_copy);
        return 1;
    }

    // Initialize the new entry
    new_entry->name = name_copy;
    new_entry->inum = inum;
    // Insert at head of the bucket
    new_entry->next = cur->dir->tb[n];
    cur->dir->tb[n] = new_entry;

    // Increase directory size
    cur->size++;

    return 0;
}