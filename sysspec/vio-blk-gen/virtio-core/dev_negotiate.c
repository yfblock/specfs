#include "virtio_core.h"

int dev_negotiate(struct virtio_blk_dev *vdev)
{
    u32 feat_lo, feat_hi;
    u8 status;

    /* Step 1: Acknowledge and set DRIVER status */
    hw_set_device_status(vdev->ioaddr, VIRTIO_CONFIG_S_ACKNOWLEDGE | VIRTIO_CONFIG_S_DRIVER);

    /* Verify that the status bits were set correctly */
    status = hw_get_device_status(vdev->ioaddr);
    if (!(status & VIRTIO_CONFIG_S_ACKNOWLEDGE) || !(status & VIRTIO_CONFIG_S_DRIVER))
        return -EIO;   /* Device did not acknowledge */

    /* Step 2: Read device features (64-bit) */
    vblk_iowrite32(vdev, VIO_REG_DEVICE_FEAT_SEL, 0);
    feat_lo = vblk_ioread32(vdev, VIO_REG_DEVICE_FEAT);

    vblk_iowrite32(vdev, VIO_REG_DEVICE_FEAT_SEL, 1);
    feat_hi = vblk_ioread32(vdev, VIO_REG_DEVICE_FEAT);

    /* Reset device feature select to 0 */
    vblk_iowrite32(vdev, VIO_REG_DEVICE_FEAT_SEL, 0);

    /* Sanity check: device should offer at least some features */
    if (feat_lo == 0 && feat_hi == 0)
        return -ENODEV;

    /* Step 3: Negotiate features */
    vdev->features = ((u64)feat_hi << 32 | feat_lo) & VBLK_SUPPORTED_FEATURES;

    /* Step 4: Write driver features (64-bit) */
    vblk_iowrite32(vdev, VIO_REG_DRIVER_FEAT_SEL, 0);
    vblk_iowrite32(vdev, VIO_REG_DRIVER_FEAT, (u32)(vdev->features));

    vblk_iowrite32(vdev, VIO_REG_DRIVER_FEAT_SEL, 1);
    vblk_iowrite32(vdev, VIO_REG_DRIVER_FEAT, (u32)(vdev->features >> 32));

    /* Reset driver feature select to 0 */
    vblk_iowrite32(vdev, VIO_REG_DRIVER_FEAT_SEL, 0);

    /* Step 5: Write memory barrier */
    hw_wmb();

    /* Step 6: Set DRIVER_OK */
    status = hw_get_device_status(vdev->ioaddr);
    hw_set_device_status(vdev->ioaddr, status | VIRTIO_CONFIG_S_DRIVER_OK);

    /* Verify that DRIVER_OK was set */
    status = hw_get_device_status(vdev->ioaddr);
    if (!(status & VIRTIO_CONFIG_S_DRIVER_OK))
        return -EIO;

    hw_mb();   /* Full memory barrier after setting DRIVER_OK */

    /* Step 7: Return success */
    return 0;
}