[PROMPT]
Provide complete `dev_read_config.c` file that implement `dev_read_config` operation. You can use information from [RELY], [GUARANTEE] and [SPECIFICATION] as described below. Your first line MUST be `#include "virtio_core.h"`. Only provide the implementation of that single function. Do NOT redefine any `VIRTIO_BLK_F_*` macros — they are already defined in kernel headers via `uapi/linux/virtio_blk.h`. Use `(1UL << N)` to test feature bits. Your output is wrapped in a C code block, and no other unrelavent code should be given.

[RELY]
```c
typedef struct virtio_blk_dev {
    void __iomem *ioaddr;
    u64 features;
    u32 num_queues;
    u16 queue_size;
    struct virtio_blk_config config;
} virtio_blk_dev;
```
```c
// MMIO read 32-bit value at a given offset from ioaddr.
u32 vblk_ioread32(struct virtio_blk_dev *vdev, int off);
```
```c
// MMIO read 16-bit value at a given offset from ioaddr.
u16 vblk_ioread16(struct virtio_blk_dev *vdev, int off);
```
```c
// MMIO read 8-bit value at a given offset from ioaddr.
u8 vblk_ioread8(struct virtio_blk_dev *vdev, int off);
```

[GUARANTEE]
```c
int dev_read_config(struct virtio_blk_dev *vdev);
```

[SPECIFICATION]
**Pre-Condition**:
- `vdev` is a valid non-NULL pointer.
- `vdev->ioaddr` is valid and mapped.
- Features have been negotiated.

**Post-Condition**:
**Case 1 (Success)**:
- `vdev->config.capacity` is read from the device config space (64-bit, little-endian).
- If `VIRTIO_BLK_F_BLK_SIZE` (bit 6) is negotiated, `vdev->config.blk_size` is read from offset 20.
- If `VIRTIO_BLK_F_SIZE_MAX` (bit 1) is negotiated, `vdev->config.size_max` is read from offset 8.
- If `VIRTIO_BLK_F_SEG_MAX` (bit 2) is negotiated, `vdev->config.seg_max` is read from offset 12.
- If `VIRTIO_BLK_F_GEOMETRY` (bit 4) is negotiated, `vdev->config.geometry.cylinders` (u16) from offset 16, `vdev->config.geometry.heads` (u8) from offset 18, `vdev->config.geometry.sectors` (u8) from offset 19. NOTE: geometry fields are nested inside `struct virtio_blk_geometry` — use `vdev->config.geometry.cylinders`, NOT `vdev->config.cylinders`.
- `vdev->num_queues` is set to 1 (single queue only).
- `vdev->queue_size` defaults to 128.
- Returns 0.

**Case 2 (Failure)**:
- Returns a negative error code.

**System Algorithm**:
1. **Read capacity**: Read 64-bit capacity from `VIO_REG_CONFIG + 0` (low 32 bits) and `VIO_REG_CONFIG + 4` (high 32 bits).
2. **Read optional fields**: Use named constants (`VIRTIO_BLK_F_*`) to test feature bits. Read from `VIO_REG_CONFIG + offset` using `vblk_ioread32/16/8`.
3. **Set defaults**: Set `num_queues = 1`, `queue_size = 128` (single queue only).
4. **Return**: Return 0.
