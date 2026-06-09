#ifndef _VIRTIO_CORE_H
#define _VIRTIO_CORE_H

#include "common.h"
#include "util.h"

int dev_reset(struct virtio_blk_dev *vdev);
int dev_negotiate(struct virtio_blk_dev *vdev);
int dev_setup_vqs(struct virtio_blk_dev *vdev);
int dev_read_config(struct virtio_blk_dev *vdev);
#endif // _VIRTIO_CORE_H