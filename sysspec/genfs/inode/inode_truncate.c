#include "inode.h"

void inode_truncate(struct inode* node, unsigned size) {
    if (size < node->size) {
        // Truncate: clear the bytes from new size to old size
        file_clear(node, size, node->size - size);
        node->size = size;
    } else if (size > node->size) {
        // Extend: allocate and clear the new space
        file_allocate(node, node->size, size - node->size);
        file_clear(node, node->size, size - node->size);
        node->size = size;
    }
    // If size equals node->size, nothing to do
}