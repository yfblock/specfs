#ifndef _COMMON_H
#define _COMMON_H

#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/pci.h>
#include <linux/virtio.h>
#include <linux/virtio_ring.h>
#include <uapi/linux/virtio_blk.h>
#include <linux/blkdev.h>
#include <linux/blk-mq.h>
#include <linux/bio.h>
#include <linux/spinlock.h>
#include <linux/interrupt.h>
#include <linux/workqueue.h>
#include <linux/dma-mapping.h>
#include <linux/slab.h>
#include <linux/string.h>
#include <linux/errno.h>
#include <linux/types.h>
#include "hw_ops.h"


#define VBLK_SUPPORTED_FEATURES ((1ULL << VIRTIO_BLK_F_SIZE_MAX) | (1ULL << VIRTIO_BLK_F_SEG_MAX) | (1ULL << VIRTIO_BLK_F_GEOMETRY) | (1ULL << VIRTIO_BLK_F_RO) | (1ULL << VIRTIO_BLK_F_BLK_SIZE) | (1ULL << VIRTIO_BLK_F_FLUSH) | (1ULL << VIRTIO_BLK_F_TOPOLOGY) | (1ULL << VIRTIO_BLK_F_CONFIG_WCE))

#define VBLK_MAX_SEGMENTS        128
#define VBLK_MAX_SIZE_MAX        65536
#define VBLK_NUM_REQUESTS        128

/* Note: u64, u32, u16, u8 are already defined by linux/types.h */

typedef struct vblk_request {
    struct virtio_blk_outhdr hdr;
    u8 status;
    struct scatterlist sg_hdr;
    struct scatterlist sg_data[VBLK_MAX_SEGMENTS];
    struct scatterlist sg_status;
    struct scatterlist *sgs[VBLK_MAX_SEGMENTS + 2];
} vblk_request;

typedef struct virtio_blk_dev {
    struct pci_dev *pdev;
    struct virtio_device *vdev;
    void __iomem *ioaddr;
    resource_size_t ioaddr_len;
    struct virtio_blk_config config;
    u64 features;
    u32 num_queues;
    u16 queue_size;
    struct virtqueue *vq;
    spinlock_t vq_lock;
    struct gendisk *gd;
    struct request_queue *rq;
    struct blk_mq_tag_set tag_set;
    int irq;
    struct work_struct config_work;
} virtio_blk_dev;
#endif // _COMMON_H