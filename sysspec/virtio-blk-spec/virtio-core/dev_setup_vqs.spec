[PROMPT]
Provide complete `dev_setup_vqs.c` file that implement `dev_setup_vqs` operation. You can use information from [RELY], [GUARANTEE] and [SPECIFICATION] as described below. Your first line MUST be `#include "virtio_blk.h"` (needed for `blk_done` declaration). Your second line should be `#include "virtio_core.h"`. Only provide the implementation of that single function. Your output is wrapped in a C code block, and no other unrelavent code should be given.

[RELY]
```c
typedef struct virtio_blk_dev {
    struct virtio_device *vdev;
    u32 num_queues;
    u16 queue_size;
    struct virtqueue *vq;
} virtio_blk_dev;
```
```c
// Completion handler declared in virtio_blk.h — called as virtqueue callback.
void blk_done(struct virtqueue *vq);
```
```c
// Kernel virtio API: find and initialize virtqueues for a virtio device.
// vdev: the virtio device
// nvqs: number of virtqueues to set up
// vqs: output array of virtqueue pointers
// vq_info: array of virtqueue_info structs (name + callback)
// affd: interrupt affinity descriptor, or NULL
// Returns 0 on success, negative error on failure.
int virtio_find_vqs(struct virtio_device *vdev, unsigned nvqs,
                    struct virtqueue **vqs,
                    struct virtqueue_info *vq_info,
                    struct irq_affinity *affd);
```
```c
// Get the number of descriptors in a virtqueue.
unsigned int virtqueue_get_vring_size(struct virtqueue *vq);
```

[GUARANTEE]
```c
int dev_setup_vqs(struct virtio_blk_dev *vdev);
```

[SPECIFICATION]
**Pre-Condition**:
- `vdev` is a valid non-NULL pointer.
- `vdev->num_queues` has been set (e.g., from config or defaults).
- The device has been reset and features negotiated.
- `vdev->vdev` is a pointer to the `struct virtio_device`.

**Post-Condition**:
**Case 1 (Success)**:
- `vdev->vq` is set to the first virtqueue obtained from `virtio_find_vqs`.
- `vdev->queue_size` is set to the vring size from `virtqueue_get_vring_size`.
- Returns 0.

**Case 2 (Failure)**:
- Returns a negative error code from `virtio_find_vqs`.

**System Algorithm**:
1. **Prepare callback info**: Set up `struct virtqueue_info` with `.callback = blk_done` and `.name = "req.0"`.
2. **Find virtqueues**: Call `virtio_find_vqs(vdev->vdev, 1, &vdev->vq, &vq_info, NULL)`.
3. **Check result**: If ret < 0, return ret.
4. **Get queue size**: `vdev->queue_size = virtqueue_get_vring_size(vdev->vq)`.
5. **Return**: Return 0.
