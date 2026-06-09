[PROMPT]
Provide complete `blkdev_init.c` file that implement `blkdev_init` and its helper functions. This is an OPTIMIZED version. Your first line MUST be `#include "driver.h"`. Only provide the implementation. Your output is wrapped in a C code block, and no other unrelavent code should be given.

KEY OPTIMIZATIONS over the original:
1. Batch kick: only kick virtqueue when `bd->last` is true (end of batch), not every request
2. Spinlock protection: hold vdev->vq_lock during submission to prevent races
3. Deferred completion: use `blk_mq_complete_request` instead of `blk_mq_end_request`
4. Dynamic queue depth from virtqueue size

IMPORTANT: The `block_device_operations` struct MUST be allocated with `kzalloc` at runtime (NOT declared as a static variable).

[RELY]
```c
typedef struct virtio_blk_dev {
    struct virtio_device *vdev;
    struct virtio_blk_config config;
    u64 features;
    u32 num_queues;
    u16 queue_size;
    struct virtqueue *vq;
    struct gendisk *gd;
    struct request_queue *rq;
    struct blk_mq_tag_set tag_set;
    spinlock_t vq_lock;
} virtio_blk_dev;
```
```c
typedef struct vblk_request {
    struct virtio_blk_outhdr hdr;
    u8 status;
    struct scatterlist sg_hdr;
    struct scatterlist sg_data[VBLK_MAX_SEGMENTS];
    struct scatterlist sg_status;
    struct scatterlist *sgs[VBLK_MAX_SEGMENTS + 2];
} vblk_request;
```
```c
int blk_submit(struct virtio_blk_dev *vdev, struct request *rq);
void blk_done(struct virtqueue *vq);
void virtqueue_enable_cb(struct virtqueue *vq);
void virtqueue_disable_cb(struct virtqueue *vq);
bool virtqueue_kick_prepare(struct virtqueue *vq);
void virtqueue_notify(struct virtqueue *vq);
int virtio_find_vqs(struct virtio_device *vdev, unsigned nvqs,
                    struct virtqueue **vqs, struct virtqueue_info *vq_info,
                    struct irq_affinity *affd);
unsigned int virtqueue_get_vring_size(struct virtqueue *vq);
int blk_mq_alloc_tag_set(struct blk_mq_tag_set *set);
struct gendisk *blk_mq_alloc_disk(struct blk_mq_tag_set *set,
                                   struct queue_limits *lim, void *queuedata);
int device_add_disk(struct device *parent, struct gendisk *disk,
                    const struct attribute_group **groups);
void set_capacity(struct gendisk *disk, sector_t size);
void blk_mq_start_request(struct request *rq);
void blk_mq_end_request(struct request *rq, blk_status_t status);
void blk_mq_complete_request(struct request *rq);
```

[GUARANTEE]
```c
int blkdev_init(struct virtio_blk_dev *vdev);
```

[SPECIFICATION]
**Pre-Condition**:
- `vdev` is a valid non-NULL pointer.
- `vdev->vq` is set by `vblk_mod.c` via `virtio_find_vqs`.
- `vdev->config.capacity` and `vdev->config.blk_size` are set.
- `vdev->vdev` is a pointer to `struct virtio_device`.

**Post-Condition**:
- A `blk_mq_ops` struct is defined with `.queue_rq` callback.
- `.queue_rq` submits requests via `blk_submit`, holds `vq_lock`, and only kicks when `bd->last` is true.
- A `block_device_operations` is allocated with `kzalloc`.
- A `gendisk` is registered via `device_add_disk`.
- Returns 0.

**System Algorithm**:
1. **Init spinlock**: `spin_lock_init(&vdev->vq_lock)`.
2. **Define queue_rq**: Hold `vq_lock`, call `blk_submit`, release lock. If `bd->last`, call `virtqueue_kick_prepare` + `virtqueue_notify`.
3. **Configure tag set**: `nr_hw_queues=1`, `queue_depth` from `virtqueue_get_vring_size(vdev->vq)`.
4. **Allocate fops**: `fops = kzalloc(sizeof(*fops))`, `fops->owner = NULL`.
5. **Register disk**: `device_add_disk(&vdev->vdev->dev, gd, NULL)`.
