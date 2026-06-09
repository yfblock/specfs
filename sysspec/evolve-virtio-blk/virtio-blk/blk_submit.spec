[PROMPT]
Provide complete `blk_submit.c` file that implement `blk_submit` operation. This is an OPTIMIZED version. Your first line MUST be `#include "virtio_blk.h"`. Only provide the implementation. Your output is wrapped in a C code block, and no other unrelavent code should be given.

KEY OPTIMIZATION: Do NOT call `virtqueue_kick()` inside this function. The caller (`virtblk_queue_rq`) handles kicking based on `bd->last` to batch doorbell writes.

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
void *blk_mq_rq_to_pdu(struct request *rq);
int rq_data_dir(struct request *rq);
sector_t blk_rq_pos(struct request *rq);
void sg_init_one(struct scatterlist *sg, const void *buf, unsigned int len);
int blk_rq_map_sg(struct request_queue *q, struct request *rq, struct scatterlist *sglist);
int virtqueue_add_sgs(struct virtqueue *vq, struct scatterlist **sgs,
                      unsigned int out_sgs, unsigned int in_sgs,
                      void *data, gfp_t gfp);
u64 cpu_to_virtio64(struct virtio_device *vdev, u64 val);
```

[GUARANTEE]
```c
int blk_submit(struct virtio_blk_dev *vdev, struct request *rq);
```

[SPECIFICATION]
**Pre-Condition**:
- `vdev` is a valid non-NULL pointer.
- `rq` is a valid non-NULL pointer to a `struct request`.
- `vdev->vq` is a valid kernel virtqueue.

**Post-Condition**:
- The request is submitted to the virtqueue via `virtqueue_add_sgs`.
- `virtqueue_kick()` is NOT called — the caller handles kicking.
- Returns 0 on success, error code from `virtqueue_add_sgs` on failure.

**System Algorithm**:
1. Get PDU: `vbr = blk_mq_rq_to_pdu(rq)`.
2. Set header: type based on `rq_data_dir`, sector from `blk_rq_pos`.
3. Init sg_hdr and sg_status with `sg_init_one`.
4. Map data: `num_sg = blk_rq_map_sg(rq->q, rq, vbr->sg_data)`.
5. Assemble sgs array: [0]=sg_hdr, [1..num_sg]=sg_data, [num_sg+1]=sg_status.
6. For READ: num_out=1, num_in=num_sg+1. For WRITE: num_out=1+num_sg, num_in=1.
7. Submit: `ret = virtqueue_add_sgs(vdev->vq, vbr->sgs, num_out, num_in, rq, GFP_ATOMIC)`.
8. Return ret. Do NOT kick.
