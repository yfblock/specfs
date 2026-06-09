[PROMPT]
Provide complete `dev_negotiate.c` file that implement `dev_negotiate` operation. You can use information first from [RELY], [GUARANTEE] and [SPECIFICATION] in the first phase, then more information in the refine phase as described below. Your first line MUST be `#include "virtio_core.h"`. Only provide the implementation of that single function. Your output is wrapped in a C code block, and no other unrelavent code should be given.

## First Prompt
[RELY]
```c
typedef struct virtio_blk_dev {
    void __iomem *ioaddr;
    u64 features;
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
```c
// MMIO read 32-bit value at a given offset from ioaddr.
u32 vblk_ioread32(struct virtio_blk_dev *vdev, int off);
```
```c
// MMIO write 32-bit value at a given offset from ioaddr.
void vblk_iowrite32(struct virtio_blk_dev *vdev, int off, u32 val);
```
```c
// VBLK_SUPPORTED_FEATURES is defined in common.h via common.header.
// Do NOT redefine it here. Use it directly in your code.
```

[GUARANTEE]
```c
int dev_negotiate(struct virtio_blk_dev *vdev);
```

[SPECIFICATION]
**Pre-Condition**:
- `vdev` is a valid non-NULL pointer.
- The device has been reset (status = 0).
- `vdev->ioaddr` is valid.

**Post-Condition**:
**Case 1 (Success)**:
- The device status register has `ACKNOWLEDGE` and `DRIVER` bits set.
- The device feature bits (32 low bits) are read from the device.
- The driver features are intersected with `VBLK_SUPPORTED_FEATURES` (defined in common.h).
- The negotiated features are written back to the device.
- `vdev->features` stores the negotiated feature set.
- The `DRIVER_OK` bit is set in the device status.
- Returns 0.

**Case 2 (Failure)**:
- Returns a negative error code.

**System Algorithm**:
1. **Acknowledge**: Set status to `VIRTIO_CONFIG_S_ACKNOWLEDGE | VIRTIO_CONFIG_S_DRIVER`.
2. **Read device features (64-bit)**: Select low features (write 0 to `VIO_REG_DEVICE_FEAT_SEL`), read from `VIO_REG_DEVICE_FEAT`. Select high features (write 1 to `VIO_REG_DEVICE_FEAT_SEL`), read from `VIO_REG_DEVICE_FEAT`. Reset select to 0.
3. **Negotiate**: `vdev->features = ((u64)feat_hi << 32 | feat_lo) & VBLK_SUPPORTED_FEATURES`.
4. **Write driver features (64-bit)**: Select low (write 0 to `VIO_REG_DRIVER_FEAT_SEL`), write low 32 bits to `VIO_REG_DRIVER_FEAT`. Select high (write 1 to `VIO_REG_DRIVER_FEAT_SEL`), write high 32 bits. Reset select to 0.
5. **Barrier**: `hw_wmb()` to ensure feature negotiation is visible before setting DRIVER_OK.
6. **Set DRIVER_OK**: `VIRTIO_CONFIG_S_DRIVER_OK` in status register, then `hw_mb()`.
7. **Return**: Return 0.

## Refine Prompt
[RELY]
```c
// Write memory barrier: ensures all previous stores are visible.
void hw_wmb(void);
```
```c
// Read memory barrier: ensures subsequent loads see latest values.
void hw_rmb(void);
```

[SPECIFICATION of dev_negotiate]
**Pre-Condition**:
No lock is owned.

**Post-Condition**:
No lock is owned.

**Memory Ordering**:
- After writing feature bits and before setting DRIVER_OK, a write memory barrier (`hw_wmb()`) must be issued to ensure feature negotiation is visible to the device before the driver signals readiness.
