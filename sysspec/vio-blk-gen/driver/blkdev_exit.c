#include "driver.h"

void blkdev_exit(struct virtio_blk_dev *vdev)
{
    del_gendisk(vdev->gd);
    kfree(vdev->gd->fops);
    put_disk(vdev->gd);
    blk_mq_free_tag_set(&vdev->tag_set);
}