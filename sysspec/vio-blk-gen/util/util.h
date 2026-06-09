#ifndef _UTIL_H
#define _UTIL_H

#include "common.h"
#include "hw_ops.h"

int vblk_bitmap_alloc(unsigned long *bitmap, int num);
void vblk_bitmap_free(unsigned long *bitmap, int index);
#endif // _UTIL_H