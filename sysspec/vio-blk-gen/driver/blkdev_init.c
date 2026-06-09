#include "driver.h"

/*
 * Queue_rq callback: submit request to virtqueue with proper locking.
 * The standard virtio-blk driver uses a per-queue spinlock to serialize
 * virtqueue access between queue_rq (process context) and the completion
 * handler (interrupt context).
 */
static blk_status_t virtblk_queue_rq(struct blk_mq_hw_ctx *hctx,
				      const struct blk_mq_queue_data *bd)
{
	struct virtio_blk_dev *vdev = hctx->queue->queuedata;
	struct request *rq = bd->rq;
	unsigned long flags;
	bool kick;
	int ret;

	blk_mq_start_request(rq);

	spin_lock_irqsave(&vdev->vq_lock, flags);

	ret = blk_submit(vdev, rq);
	if (ret) {
		spin_unlock_irqrestore(&vdev->vq_lock, flags);
		blk_mq_end_request(rq, BLK_STS_IOERR);
		return BLK_STS_IOERR;
	}

	kick = virtqueue_kick_prepare(vdev->vq);
	spin_unlock_irqrestore(&vdev->vq_lock, flags);

	if (kick)
		virtqueue_notify(vdev->vq);
	return BLK_STS_OK;
}

static const struct blk_mq_ops virtblk_mq_ops = {
	.queue_rq = virtblk_queue_rq,
};

int blkdev_init(struct virtio_blk_dev *vdev)
{
	struct block_device_operations *fops;
	struct queue_limits lim = {
		.logical_block_size = vdev->config.blk_size ?: 512,
		.max_segments = 128,
		.max_segment_size = 65536,
	};
	int ret;

	spin_lock_init(&vdev->vq_lock);

	vdev->tag_set.ops = &virtblk_mq_ops;
	vdev->tag_set.nr_hw_queues = 1;
	vdev->tag_set.queue_depth = vdev->queue_size / 3;
	vdev->tag_set.cmd_size = sizeof(struct vblk_request);
	vdev->tag_set.numa_node = NUMA_NO_NODE;
	vdev->tag_set.driver_data = vdev;

	ret = blk_mq_alloc_tag_set(&vdev->tag_set);
	if (ret)
		return ret;

	vdev->gd = blk_mq_alloc_disk(&vdev->tag_set, &lim, vdev);
	if (IS_ERR(vdev->gd)) {
		ret = PTR_ERR(vdev->gd);
		goto fail_tag_set;
	}

	fops = kzalloc(sizeof(*fops), GFP_KERNEL);
	if (!fops) {
		ret = -ENOMEM;
		goto fail_disk;
	}
	fops->owner = NULL;
	vdev->gd->fops = fops;

	snprintf(vdev->gd->disk_name, DISK_NAME_LEN, "vda");
	set_capacity(vdev->gd, vdev->config.capacity);

	vdev->rq = vdev->gd->queue;
	vdev->rq->queuedata = vdev;

	ret = device_add_disk(&vdev->vdev->dev, vdev->gd, NULL);
	if (ret)
		goto fail_fops;

	return 0;

fail_fops:
	kfree(fops);
fail_disk:
	put_disk(vdev->gd);
fail_tag_set:
	blk_mq_free_tag_set(&vdev->tag_set);
	return ret;
}
