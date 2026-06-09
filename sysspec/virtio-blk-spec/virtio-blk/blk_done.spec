[PROMPT]
Provide complete `blk_done.c` file that implement `blk_done` operation. You can use information from [RELY], [GUARANTEE] and [SPECIFICATION] as described below. Your first line MUST be `#include "virtio_blk.h"`. Only provide the implementation of that single function. Your output is wrapped in a C code block, and no other unrelavent code should be given.

[RELY]
```c
typedef struct vblk_request {
    u8 status;
} vblk_request;
```
```c
// Kernel virtqueue API: get the next completed buffer from the used ring.
// Returns the opaque data pointer passed to virtqueue_add_sgs, or NULL if no buffers are available.
// len: output parameter set to the used length.
void *virtqueue_get_buf(struct virtqueue *vq, unsigned int *len);
```
```c
// Get the blk-mq private data (vblk_request) from a request.
void *blk_mq_rq_to_pdu(struct request *rq);
```
```c
// End a blk-mq request with the given status.
void blk_mq_end_request(struct request *rq, blk_status_t status);
```
```c
// From linux/virtio_blk.h: VIRTIO_BLK_S_OK=0, VIRTIO_BLK_S_IOERR=1
// From linux/blkdev.h: BLK_STS_OK=0, BLK_STS_IOERR
```

[GUARANTEE]
```c
void blk_done(struct virtqueue *vq);
```

[SPECIFICATION]
**Pre-Condition**:
- `vq` is a valid non-NULL pointer to a kernel `struct virtqueue`.
- This function is registered as a virtqueue callback and runs in interrupt context.
- The device has completed one or more I/O requests.

**Post-Condition**:
- For each completed request obtained from `virtqueue_get_buf`:
  - The request pointer (`struct request *`) is recovered from the opaque data.
  - The `vblk_request` is recovered via `blk_mq_rq_to_pdu(rq)`.
  - If `vbr->status == VIRTIO_BLK_S_OK`, the request is completed via `blk_mq_end_request(rq, BLK_STS_OK)`.
  - Otherwise, the request is completed via `blk_mq_end_request(rq, BLK_STS_IOERR)`.

**System Algorithm**:
1. **Poll loop**: While `virtqueue_get_buf(vq, &len)` returns a non-NULL pointer:
   - Recover `rq` from the returned pointer.
   - Recover `vbr = blk_mq_rq_to_pdu(rq)`.
   - Check `vbr->status`.
   - If `VIRTIO_BLK_S_OK`, call `blk_mq_end_request(rq, BLK_STS_OK)`.
   - Otherwise, call `blk_mq_end_request(rq, BLK_STS_IOERR)`.
2. **Return**.
