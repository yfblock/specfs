[PROMPT]
Provide complete `blkdev_exit.c` file that implement `blkdev_exit` operation. Your first line MUST be `#include "driver.h"`. Only provide the implementation. Your output is wrapped in a C code block, and no other unrelavent code should be given.

[RELY]
```c
typedef struct virtio_blk_dev {
    struct virtio_device *vdev;
    struct virtqueue *vq;
    struct gendisk *gd;
    struct blk_mq_tag_set tag_set;
} virtio_blk_dev;
```
```c
void del_gendisk(struct gendisk *disk);
void blk_mq_free_tag_set(struct blk_mq_tag_set *set);
void put_disk(struct gendisk *disk);
void kfree(const void *ptr);
```

[GUARANTEE]
```c
void blkdev_exit(struct virtio_blk_dev *vdev);
```

[SPECIFICATION]
**System Algorithm**:
1. `del_gendisk(vdev->gd)`.
2. `kfree(vdev->gd->fops)`.
3. `put_disk(vdev->gd)`.
4. `blk_mq_free_tag_set(&vdev->tag_set)`.

Do NOT call `unregister_blkdev`.
