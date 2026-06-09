# Makefile for SYSSPEC-generated 8250/16550 UART kernel module
# Usage: make                  (build module)
#        make clean            (clean build artifacts)
#        sudo insmod uart16550.ko iobase=0x2f8 irq=3

KDIR ?= /lib/modules/$(shell uname -r)/build
PWD  := $(shell pwd)

obj-m := uart16550.o

uart16550-objs := \
	uart16550_mod.o \
	uart/uart_hw_init.o \
	uart/uart_startup.o \
	uart/uart_shutdown.o \
	uart/uart_set_termios.o \
	uart/uart_start_tx.o \
	uart/uart_stop_tx.o \
	uart/uart_tx_empty.o \
	uart/uart_handle_irq.o

ccflags-y := -I$(src) -I$(src)/uart

all:
	$(MAKE) -C $(KDIR) M=$(PWD) modules

clean:
	$(MAKE) -C $(KDIR) M=$(PWD) clean

.PHONY: all clean
