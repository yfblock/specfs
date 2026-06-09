#ifndef _VIRTIO_BLK_H
#define _VIRTIO_BLK_H

#include "common.h"
#include "util.h"
#include "virtio_core.h"

int blk_submit(struct virtio_blk_dev *vdev, struct request *rq);
void blk_done(struct virtqueue *vq);
#endif // _VIRTIO_BLK_H