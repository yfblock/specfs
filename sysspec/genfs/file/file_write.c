#include "file.h"

void file_write(struct inode *node, unsigned offset, unsigned len, const char *data) {
    if (len == 0) return;

    struct indextb *tb = node->file;
    unsigned remaining = len;
    unsigned curr_offset = offset;

    while (remaining > 0) {
        unsigned page_index = curr_offset / PG_SIZE;
        unsigned page_off = curr_offset % PG_SIZE;
        unsigned copy_len = (PG_SIZE - page_off < remaining) ? (PG_SIZE - page_off) : remaining;

        unsigned char *page = tb->index[page_index];
        if (data == NULL) {
            // Case 1: zero-fill, allocate page if necessary
            if (page == NULL) {
                page = (unsigned char *)malloc(PG_SIZE);
                if (page) {
                    memset(page, 0, PG_SIZE);
                    tb->index[page_index] = page;
                }
            }
            // Zero the specific region within the page
            if (page) {
                memset(page + page_off, 0, copy_len);
            }
        } else {
            // Case 2: copy from data buffer
            if (page) {
                memcpy(page + page_off, data + (curr_offset - offset), copy_len);
            }
        }

        curr_offset += copy_len;
        remaining -= copy_len;
    }
}