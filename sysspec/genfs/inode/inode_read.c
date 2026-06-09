#include "inode.h"

struct read_ret* inode_read(struct inode* node, unsigned len, unsigned offset) {
    struct read_ret* ret = malloc_readret();
    if (offset >= node->size || len == 0) {
        ret->num = 0;
        ret->buf = NULL;
        return ret;
    }
    
    unsigned actual = (len < node->size - offset) ? len : (node->size - offset);
    char* buf = malloc_buffer(actual);
    file_read(node, offset, actual, buf);
    
    ret->buf = buf;
    ret->num = actual;
    return ret;
}