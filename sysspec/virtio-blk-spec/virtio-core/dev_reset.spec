[PROMPT]
Provide complete `dev_reset.c` file that implement `dev_reset` operation. You can use information from [RELY], [GUARANTEE] and [SPECIFICATION] as described below. Your first line MUST be `#include "virtio_core.h"`. Only provide the implementation of that single function. Your output is wrapped in a C code block, and no other unrelavent code should be given.

[RELY]
```c
typedef struct virtio_blk_dev {
    void __iomem *ioaddr;
} virtio_blk_dev;
```
```c
// Read the device status register (8-bit).
u8 hw_get_device_status(void __iomem *ioaddr);
```
```c
// Write the device status register (8-bit).
void hw_set_device_status(void __iomem *ioaddr, u8 status);
```

[GUARANTEE]
```c
int dev_reset(struct virtio_blk_dev *vdev);
```

[SPECIFICATION]
**Pre-Condition**:
- `vdev` is a valid non-NULL pointer to a `virtio_blk_dev`.
- `vdev->ioaddr` is a valid mapped MMIO address.

**Post-Condition**:
**Case 1 (Success)**:
- The device status register is written with 0 (reset).
- The device is in a clean initial state.
- Returns 0.

**Case 2 (Failure)**:
- If `vdev->ioaddr` is NULL, returns -ENODEV.

**System Algorithm**:
1. **Check IO address**: If `vdev` is NULL or `vdev->ioaddr` is NULL, return -ENODEV.
2. **Reset**: Call `hw_set_device_status(vdev->ioaddr, 0)` (writes to `VIO_REG_STATUS`).
3. **Verify**: Read back status with `hw_get_device_status(vdev->ioaddr)`. If not 0, log a warning and return -EIO.
4. **Return**: Return 0.
