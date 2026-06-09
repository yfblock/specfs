#include "virtio_blk.h"

int blk_submit(struct virtio_blk_dev *vdev, struct request *rq)
{
    struct vblk_request *vbr;
    int num_sg;
    unsigned int num_out, num_in;
    int ret;

    vbr = blk_mq_rq_to_pdu(rq);

    /* Set virtio-blk header */
    if (rq_data_dir(rq) == READ) {
        vbr->hdr.type = VIRTIO_BLK_T_IN;
    } else {
        vbr->hdr.type = VIRTIO_BLK_T_OUT;
    }
    vbr->hdr.sector = cpu_to_virtio64(vdev->vdev, blk_rq_pos(rq));

    /* Initialize scatterlists */
    sg_init_one(&vbr->sg_hdr, &vbr->hdr, sizeof(vbr->hdr));

    sg_init_one(&vbr->sg_status, &vbr->status, sizeof(vbr->status));

    /* Map request data into sg_data */
    num_sg = blk_rq_map_sg(rq->q, rq, vbr->sg_data);
    if (num_sg < 0)
        return -EIO;

    /* Assemble sgs array */
    vbr->sgs[0] = &vbr->sg_hdr;
    for (int i = 0; i < num_sg; i++)
        vbr->sgs[i + 1] = &vbr->sg_data[i];
    vbr->sgs[num_sg + 1] = &vbr->sg_status;

    /* Determine number of out and in segments based on direction */
    if (rq_data_dir(rq) == READ) {
        num_out = 1;          /* header only */
        num_in = num_sg + 1;  /* data + status */
    } else {
        num_out = 1 + num_sg; /* header + data */
        num_in = 1;           /* status only */
    }

    /* Submit to virtqueue */
    ret = virtqueue_add_sgs(vdev->vq, vbr->sgs, num_out, num_in,
                            rq, GFP_ATOMIC);
    if (ret)
        return ret;

    return 0;
}