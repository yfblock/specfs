[PROMPT]
Provide complete `blkdev_init.c` file that implement `blkdev_init` and its helper functions. You can use information from [RELY], [GUARANTEE] and [SPECIFICATION] as described below. Your first line MUST be `#include "driver.h"`. Only provide the implementation. Your output is wrapped in a C code block, and no other unrelavent code should be given.

IMPORTANT: The `block_device_operations` struct MUST be allocated with `kzalloc` at runtime (NOT declared as a static variable). Static struct initialization with `THIS_MODULE` fails due to compiler relocation issues in kernel modules.

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
// Submit a request to the virtio-blk device. Returns 0 on success.
int blk_submit(struct virtio_blk_dev *vdev, struct request *rq);
```
```c
// Completion handler for virtqueue callbacks.
void blk_done(struct virtqueue *vq);
```
```c
// Enable virtqueue callback for completion notification.
void virtqueue_enable_cb(struct virtqueue *vq);
```
```c
// Allocate a blk-mq tag set. Returns 0 on success.
int blk_mq_alloc_tag_set(struct blk_mq_tag_set *set);
```
```c
// Allocate a gendisk with blk-mq backing. Returns gendisk pointer or ERR_PTR.
struct gendisk *blk_mq_alloc_disk(struct blk_mq_tag_set *set,
                                   struct queue_limits *lim, void *queuedata);
```
```c
// Add a gendisk to the system with a parent device. Returns 0 on success.
int device_add_disk(struct device *parent, struct gendisk *disk,
                    const struct attribute_group **groups);
```
```c
// Set the capacity of a gendisk in sectors.
void set_capacity(struct gendisk *disk, sector_t size);
```
```c
// Start a blk-mq request (marks it as active).
void blk_mq_start_request(struct request *rq);
```
```c
// End a blk-mq request with the given status.
void blk_mq_end_request(struct request *rq, blk_status_t status);
```

[GUARANTEE]
```c
int blkdev_init(struct virtio_blk_dev *vdev);
```

[SPECIFICATION]
**Pre-Condition**:
- `vdev` is a valid non-NULL pointer.
- The device has been initialized: features negotiated, virtqueues set up, config read.
- `vdev->config.capacity` contains the device capacity in sectors.
- `vdev->config.blk_size` contains the sector size.
- `vdev->vq` is a valid kernel virtqueue with `blk_done` as its callback.
- `vdev->vdev` is a pointer to `struct virtio_device`.

**Post-Condition**:
**Case 1 (Success)**:
- A `blk_mq_ops` struct with `.queue_rq` callback is defined.
- The `.queue_rq` callback submits requests via `blk_submit` and enables completion via `virtqueue_enable_cb`.
- A `block_device_operations` struct is allocated with `kzalloc` (NOT static).
- A `blk_mq_tag_set` is configured and allocated.
- A `gendisk` is allocated via `blk_mq_alloc_disk`.
- `disk_name` is set to "vda".
- Capacity is set from `vdev->config.capacity`.
- The disk is registered via `device_add_disk(&vdev->vdev->dev, vdev->gd, NULL)`.
- Returns 0.

**Case 2 (Failure)**:
- Returns a negative error code. Resources are cleaned up on failure.

**System Algorithm**:
1. **Define queue_rq callback**: `virtblk_queue_rq(hctx, bd)` that calls `blk_mq_start_request`, `blk_submit`, `virtqueue_enable_cb`, and returns `BLK_STS_OK` or `BLK_STS_IOERR`.
2. **Define blk_mq_ops**: Static struct with `.queue_rq = virtblk_queue_rq`.
3. **Configure tag set**: Set `tag_set.ops`, `tag_set.nr_hw_queues = 1`, `tag_set.queue_depth = vdev->queue_size / 3` (each request uses 3 descriptors: header + data + status), `tag_set.cmd_size = sizeof(struct vblk_request)`, `tag_set.numa_node = NUMA_NO_NODE`, `tag_set.driver_data = vdev`.
4. **Allocate tag set**: `ret = blk_mq_alloc_tag_set(&vdev->tag_set)`. If fail, return ret.
5. **Set queue limits**: `struct queue_limits` with `logical_block_size = vdev->config.blk_size ?: 512`, `max_segments = 128`, `max_segment_size = 65536`.
6. **Allocate gendisk**: `vdev->gd = blk_mq_alloc_disk(&vdev->tag_set, &lim, vdev)`. If fail, clean up.
7. **Allocate fops**: `fops = kzalloc(sizeof(*fops), GFP_KERNEL)`. Set `fops->owner = NULL`. Set `vdev->gd->fops = fops`. NOTE: Do NOT use a static `block_device_operations` — the compiler's `THIS_MODULE` relocation fails in kernel modules.
8. **Configure gendisk**: Set `disk_name = "vda"`, call `set_capacity(vdev->gd, vdev->config.capacity)`.
9. **Set up queue**: `vdev->rq = vdev->gd->queue`, `vdev->rq->queuedata = vdev`.
10. **Add disk**: `ret = device_add_disk(&vdev->vdev->dev, vdev->gd, NULL)`. If fail, free fops and clean up.
11. **Return**: Return 0.
