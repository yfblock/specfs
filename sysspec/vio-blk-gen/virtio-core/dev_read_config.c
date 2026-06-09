#include "virtio_core.h"

int dev_read_config(struct virtio_blk_dev *vdev)
{
	u32 low, high;

	/* Read 64-bit capacity from offset 0 (low) and 4 (high) */
	low = vblk_ioread32(vdev, 0);
	high = vblk_ioread32(vdev, 4);
	vdev->config.capacity = ((u64)high << 32) | low;

	/* Optional: block size (VIRTIO_BLK_F_BLK_SIZE, bit 6) */
	if (vdev->features & (1UL << 6))
		vdev->config.blk_size = vblk_ioread32(vdev, 20);

	/* Optional: size_max (VIRTIO_BLK_F_SIZE_MAX, bit 1) */
	if (vdev->features & (1UL << 1))
		vdev->config.size_max = vblk_ioread32(vdev, 8);

	/* Optional: seg_max (VIRTIO_BLK_F_SEG_MAX, bit 2) */
	if (vdev->features & (1UL << 2))
		vdev->config.seg_max = vblk_ioread32(vdev, 12);

	/* Optional: geometry (VIRTIO_BLK_F_GEOMETRY, bit 4) */
	if (vdev->features & (1UL << 4)) {
		vdev->config.geometry.cylinders = vblk_ioread16(vdev, 16);
		vdev->config.geometry.heads     = vblk_ioread8(vdev, 18);
		vdev->config.geometry.sectors   = vblk_ioread8(vdev, 19);
	}

	/* Set single queue defaults */
	vdev->num_queues = 1;
	vdev->queue_size = 128;

	return 0;
}