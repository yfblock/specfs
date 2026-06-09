#include "virtio_core.h"

int dev_reset(struct virtio_blk_dev *vdev)
{
    u8 status;

    /* Check for invalid device or IO address */
    if (!vdev || !vdev->ioaddr)
        return -ENODEV;

    /* Perform reset by writing 0 to status register */
    hw_set_device_status(vdev->ioaddr, 0);

    /* Verify that the device acknowledged the reset */
    status = hw_get_device_status(vdev->ioaddr);
    if (status != 0) {
        pr_warn("virtio_blk: device reset failed, status=0x%x\n", status);
        return -EIO;
    }

    return 0;
}