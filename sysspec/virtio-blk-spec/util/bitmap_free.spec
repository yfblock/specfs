[PROMPT]
Provide complete `vblk_bitmap_free.c` file that implement `vblk_bitmap_free` operation. You can use information from [RELY], [GUARANTEE] and [SPECIFICATION] as described below. Your first line MUST be `#include "util.h"`. Only provide the implementation of that single function. Your output is wrapped in a C code block, and no other unrelavent code should be given.

[RELY]

[GUARANTEE]
```c
void vblk_bitmap_free(unsigned long *bitmap, int index);
```

[SPECIFICATION]
**Pre-Condition**:
- `bitmap` is a valid non-NULL pointer to a bitmap.
- `index` is a non-negative integer representing a previously allocated bit.

**Post-Condition**:
- The bit at position `index` is cleared (set to 0), marking it as free.

**System Algorithm**:
1. **Clear bit**: Call `clear_bit(index, bitmap)`.
