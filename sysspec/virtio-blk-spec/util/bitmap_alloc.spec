[PROMPT]
Provide complete `vblk_bitmap_alloc.c` file that implement `vblk_bitmap_alloc` operation. You can use information from [RELY], [GUARANTEE] and [SPECIFICATION] as described below. Your first line MUST be `#include "util.h"`. Only provide the implementation of that single function. Your output is wrapped in a C code block, and no other unrelavent code should be given.

[RELY]

[GUARANTEE]
```c
int vblk_bitmap_alloc(unsigned long *bitmap, int num);
```

[SPECIFICATION]
**Pre-Condition**:
- `bitmap` is a valid non-NULL pointer to a bitmap with at least `num` bits.
- `num` is a positive integer.

**Post-Condition**:
**Case 1 (Success)**:
- A previously clear (free) bit is found and set (allocated).
- Returns the index of the allocated bit (0 to num-1).

**Case 2 (No free bit)**:
- No bit is modified.
- Returns -1.

**System Algorithm**:
1. **Find first zero bit**: Call `find_first_zero_bit(bitmap, num)`.
2. **Check availability**: If the result is >= `num`, return -1.
3. **Set bit**: Call `set_bit(index, bitmap)`.
4. **Return**: Return the index.
