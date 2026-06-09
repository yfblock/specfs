#ifndef _DRIVER_H
#define _DRIVER_H

#include "common.h"
#include "util.h"
#include "virtio_core.h"
#include "virtio_blk.h"

int blkdev_init(struct virtio_blk_dev *vdev);
void blkdev_exit(struct virtio_blk_dev *vdev);
#endif // _DRIVER_H