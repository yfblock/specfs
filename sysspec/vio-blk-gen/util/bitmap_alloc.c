#include "util.h"

int vblk_bitmap_alloc(unsigned long *bitmap, int num)
{
    int index = find_first_zero_bit(bitmap, num);
    if (index >= num)
        return -1;
    set_bit(index, bitmap);
    return index;
}