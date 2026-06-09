# Makefile for SYSSPEC-generated virtio-blk kernel module
# Usage: make                  (build module)
#        make clean            (clean build artifacts)
#        sudo insmod vblk.ko   (load module)
#        sudo rmmod vblk       (unload module)

KDIR ?= /lib/modules/$(shell uname -r)/build
PWD  := $(shell pwd)

obj-m := vblk.o

vblk-objs := \
	vblk_mod.o \
	util/bitmap_alloc.o \
	util/bitmap_free.o \
	virtio-core/dev_reset.o \
	virtio-core/dev_negotiate.o \
	virtio-core/dev_setup_vqs.o \
	virtio-core/dev_read_config.o \
	virtio-blk/blk_submit.o \
	virtio-blk/blk_done.o \
	driver/blkdev_init.o \
	driver/blkdev_exit.o

ccflags-y := -I$(src) -I$(src)/util -I$(src)/virtio-core -I$(src)/virtio-blk -I$(src)/driver

all:
	$(MAKE) -C $(KDIR) M=$(PWD) modules

clean:
	$(MAKE) -C $(KDIR) M=$(PWD) clean

.PHONY: all clean
