#include "util.h"

void vblk_bitmap_free(unsigned long *bitmap, int index)
{
    clear_bit(index, bitmap);
}