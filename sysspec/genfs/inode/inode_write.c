#include "inode.h"

unsigned inode_write(struct inode* node, const char* buffer, unsigned len, unsigned offset) {
    // If offset is beyond the maximum file size, nothing can be written.
    if (offset >= MAX_FILE_SIZE) {
        return 0;
    }

    // Compute the actual number of bytes to write, bounded by the maximum file size.
    unsigned write_len = len;
    if (offset + write_len > MAX_FILE_SIZE) {
        write_len = MAX_FILE_SIZE - offset;
    }

    unsigned new_size = offset + write_len;

    // Grow the file if necessary.
    if (new_size > node->size) {
        unsigned grow_len = new_size - node->size;
        file_allocate(node, node->size, grow_len);
        file_clear(node, node->size, grow_len);
        node->size = new_size;
    }

    // Write the data.
    file_write(node, offset, write_len, buffer);

    return write_len;
}