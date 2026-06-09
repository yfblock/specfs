[PROMPT]
Provide complete `blk_submit.c` file that implement `blk_submit` operation. You can use information from [RELY], [GUARANTEE] and [SPECIFICATION] as described below. Your first line MUST be `#include "virtio_blk.h"`. Only provide the implementation of that single function. Your output is wrapped in a C code block, and no other unrelavent code should be given.

[RELY]
```c
typedef struct virtio_blk_dev {
    struct virtio_device *vdev;
    struct virtqueue *vq;
    u64 features;
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
// Get the blk-mq private data (vblk_request) from a request.
void *blk_mq_rq_to_pdu(struct request *rq);
```
```c
// Get the data direction of a request (READ or WRITE).
int rq_data_dir(struct request *rq);
```
```c
// Get the sector number of a request.
sector_t blk_rq_pos(struct request *rq);
```
```c
// Initialize a single-entry scatterlist.
void sg_init_one(struct scatterlist *sg, const void *buf, unsigned int len);
```
```c
// Map request data to scatterlist. Returns number of segments.
int blk_rq_map_sg(struct request_queue *q, struct request *rq, struct scatterlist *sglist);
```
```c
// Kernel virtqueue API: add scatter-gather buffers to the virtqueue.
int virtqueue_add_sgs(struct virtqueue *vq, struct scatterlist **sgs,
                      unsigned int out_sgs, unsigned int in_sgs,
                      void *data, gfp_t gfp);
```
```c
// Kernel virtqueue API: notify the device that buffers are available.
void virtqueue_kick(struct virtqueue *vq);
```
```c
// End-of-endian conversion for virtio. vdev is a pointer to struct virtio_device.
u32 cpu_to_virtio32(struct virtio_device *vdev, u32 val);
u64 cpu_to_virtio64(struct virtio_device *vdev, u64 val);
```
```c
// From uapi/linux/virtio_blk.h: VIRTIO_BLK_T_IN=0 (read), VIRTIO_BLK_T_OUT=1 (write)
```

[GUARANTEE]
```c
int blk_submit(struct virtio_blk_dev *vdev, struct request *rq);
```

[SPECIFICATION]
**Pre-Condition**:
- `vdev` is a valid non-NULL pointer.
- `rq` is a valid non-NULL pointer to a `struct request` from blk-mq.
- `vdev->vq` is a valid kernel virtqueue.
- `vdev->vdev` is a pointer to `struct virtio_device` (NOT a copy).

**Post-Condition**:
**Case 1 (Success)**:
- The request's scatterlist is populated: `sg_hdr` for the virtio-blk header, `sg_data[]` for data segments, `sg_status` for the status byte.
- The `hdr.type` is `VIRTIO_BLK_T_IN` for reads or `VIRTIO_BLK_T_OUT` for writes.
- The `hdr.sector` is set from `blk_rq_pos(rq)`.
- The `sgs[]` array is assembled: `[0]=sg_hdr`, `[1..num_sg]=sg_data[]`, `[1+num_sg]=sg_status`.
- `virtqueue_add_sgs(vdev->vq, sgs, num_out, num_in, rq, GFP_ATOMIC)` is called.
- `virtqueue_kick(vdev->vq)` is called to notify the device.
- Returns 0.

**Case 2 (Failure)**:
- Returns the error code from `virtqueue_add_sgs`.

**System Algorithm**:
1. **Get PDU**: `vbr = blk_mq_rq_to_pdu(rq)`.
2. **Set header**: `vbr->hdr.type = (rq_data_dir(rq) == READ) ? VIRTIO_BLK_T_IN : VIRTIO_BLK_T_OUT`. `vbr->hdr.sector = cpu_to_virtio64(vdev->vdev, blk_rq_pos(rq))`. Note: `vdev->vdev` is already a pointer, do NOT use `&vdev->vdev`.
3. **Init sg_hdr**: `sg_init_one(&vbr->sg_hdr, &vbr->hdr, sizeof(vbr->hdr))`.
4. **Init sg_status**: `sg_init_one(&vbr->sg_status, &vbr->status, sizeof(vbr->status))`.
5. **Map data**: `num_sg = blk_rq_map_sg(rq->q, rq, vbr->sg_data)`. If `num_sg < 0`, return `-EIO`.
6. **Assemble sgs**: Set `vbr->sgs[0] = &vbr->sg_hdr`, then `vbr->sgs[1..num_sg] = &vbr->sg_data[0..num_sg-1]`, then `vbr->sgs[num_sg+1] = &vbr->sg_status`.
   - For READ: `num_out = 1` (header), `num_in = num_sg + 1` (data + status).
   - For WRITE: `num_out = 1 + num_sg` (header + data), `num_in = 1` (status).
7. **Submit**: `ret = virtqueue_add_sgs(vdev->vq, vbr->sgs, num_out, num_in, rq, GFP_ATOMIC)`.
8. **Kick**: `virtqueue_kick(vdev->vq)`.
9. **Return**: Return ret (0 on success, negative error code from `virtqueue_add_sgs` or `-EIO` from data mapping failure).
