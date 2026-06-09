#include "virtio_blk.h"
#include "virtio_core.h"

int dev_setup_vqs(struct virtio_blk_dev *vdev)
{
    struct virtqueue_info vq_info = {
        .callback = blk_done,
        .name = "req.0"
    };
    int ret;

    ret = virtio_find_vqs(vdev->vdev, 1, &vdev->vq, &vq_info, NULL);
    if (ret < 0)
        return ret;

    vdev->queue_size = virtqueue_get_vring_size(vdev->vq);

    return 0;
}