[PROMPT]
Provide complete `blkdev_exit.c` file that implement `blkdev_exit` operation. You can use information from [RELY], [GUARANTEE] and [SPECIFICATION] as described below. Your first line MUST be `#include "driver.h"`. Only provide the implementation of that single function. Your output is wrapped in a C code block, and no other unrelavent code should be given.

[RELY]
```c
typedef struct virtio_blk_dev {
    struct gendisk *gd;
    struct blk_mq_tag_set tag_set;
} virtio_blk_dev;
```
```c
// Delete a gendisk from the system (removes from block layer).
void del_gendisk(struct gendisk *disk);
```
```c
// Free a blk-mq tag set.
void blk_mq_free_tag_set(struct blk_mq_tag_set *set);
```
```c
// Release a gendisk reference.
void put_disk(struct gendisk *disk);
```
```c
// Free kernel memory allocated with kzalloc/kmalloc.
void kfree(const void *ptr);
```

[GUARANTEE]
```c
void blkdev_exit(struct virtio_blk_dev *vdev);
```

[SPECIFICATION]
**Pre-Condition**:
- `vdev` is a valid non-NULL pointer.
- The block device has been initialized via `blkdev_init`.
- `vdev->gd->fops` was allocated with `kzalloc` in `blkdev_init`.

**Post-Condition**:
- The gendisk is deleted from the system via `del_gendisk(vdev->gd)`.
- The dynamically allocated `fops` struct is freed via `kfree(vdev->gd->fops)`.
- The gendisk reference is released via `put_disk(vdev->gd)`.
- The blk-mq tag set is freed via `blk_mq_free_tag_set(&vdev->tag_set)`.

**System Algorithm**:
1. **Remove disk**: `del_gendisk(vdev->gd)`.
2. **Free fops**: `kfree(vdev->gd->fops)` — this was allocated with `kzalloc` in `blkdev_init`.
3. **Release gendisk**: `put_disk(vdev->gd)`.
4. **Free tag set**: `blk_mq_free_tag_set(&vdev->tag_set)`.

**IMPORTANT**: Do NOT call `unregister_blkdev` — the major number is auto-assigned by `device_add_disk` and does not need manual unregistration. The teardown order MUST be: `del_gendisk` -> `kfree(fops)` -> `put_disk` -> `blk_mq_free_tag_set`.
