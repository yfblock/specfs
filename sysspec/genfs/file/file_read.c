#include "file.h"

void file_read(struct inode *node, unsigned offset, unsigned len, char *data) {
    if (len == 0) return;

    unsigned start_block = offset >> 12;          /* block index (4096 bytes per block) */
    unsigned end_block   = (offset + len - 1) >> 12;
    unsigned block_off   = offset & 0xFFF;        /* offset within first block (0..4095) */
    unsigned remaining   = len;

    for (unsigned b = start_block; b <= end_block; ++b) {
        unsigned char *block = node->file->index[b];
        unsigned copy_start = (b == start_block) ? block_off : 0;
        unsigned copy_end   = (b == end_block) ? ((offset + len - 1) & 0xFFF) + 1 : 4096;
        unsigned chunk = copy_end - copy_start;

        /* Copy chunk bytes from block[copy_start] to data buffer */
        unsigned char *src = block + copy_start;
        unsigned char *dst = (unsigned char *)data;
        for (unsigned i = 0; i < chunk; ++i)
            dst[i] = src[i];

        data      += chunk;
        remaining -= chunk;
    }
}