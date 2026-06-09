#include "virtio_blk.h"

void blk_done(struct virtqueue *vq)
{
	struct virtio_blk_dev *vdev = vq->vdev->priv;
	struct vblk_request *vbr;
	struct request *rq;
	unsigned long flags;
	unsigned int len;
	void *opaque;

	spin_lock_irqsave(&vdev->vq_lock, flags);

	while ((opaque = virtqueue_get_buf(vq, &len)) != NULL) {
		rq = (struct request *)opaque;
		vbr = blk_mq_rq_to_pdu(rq);
		if (vbr->status == VIRTIO_BLK_S_OK)
			blk_mq_end_request(rq, BLK_STS_OK);
		else
			blk_mq_end_request(rq, BLK_STS_IOERR);
	}

	spin_unlock_irqrestore(&vdev->vq_lock, flags);
}
