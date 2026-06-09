/*
 * 8250/16550 UART driver skeleton for SYSSPEC-generated port logic.
 *
 * Hand-written: module init, uart_register_driver, IRQ registration,
 *   I/O region request, module parameters for iobase/irq.
 * Generated: uart_startup/shutdown/set_termios/tx/irq handlers.
 */
#include <linux/platform_device.h>
#include <linux/serial.h>

#include "common.h"
#include "uart/uart.h"

#define UART_SYSSPEC_NR_PORTS 1

static struct uart_port uart_sysspec_port;
static struct uart_driver uart_sysspec_driver;
static struct platform_device *uart_sysspec_pdev;

static unsigned long uart_iobase = 0x2f8;
static unsigned int uart_irq = 3;
module_param_named(iobase, uart_iobase, ulong, 0444);
MODULE_PARM_DESC(iobase, "I/O base address for SYSSPEC UART (default COM2 0x2f8)");
module_param_named(irq, uart_irq, uint, 0444);
MODULE_PARM_DESC(irq, "IRQ line for SYSSPEC UART (default COM2 IRQ 3)");

static unsigned int uart_sysspec_tx_empty(struct uart_port *port)
{
	return uart_tx_empty(port);
}

static void uart_sysspec_set_mctrl(struct uart_port *port, unsigned int mctrl)
{
	unsigned int mcr = 0;

	if (mctrl & TIOCM_RTS)
		mcr |= UART_MCR_RTS;
	if (mctrl & TIOCM_DTR)
		mcr |= UART_MCR_DTR;
	if (mctrl & TIOCM_OUT1)
		mcr |= UART_MCR_OUT1;
	if (mctrl & TIOCM_OUT2)
		mcr |= UART_MCR_OUT2;
	hw_outb(UART16550_PORT_REG(port->iobase, UART_SYSSPEC_MCR), mcr);
}

static unsigned int uart_sysspec_get_mctrl(struct uart_port *port)
{
	unsigned int msr = hw_inb(UART16550_PORT_REG(port->iobase, UART_SYSSPEC_MSR));
	unsigned int mctrl = 0;

	if (msr & UART_MSR_CTS)
		mctrl |= TIOCM_CTS;
	if (msr & UART_MSR_DCD)
		mctrl |= TIOCM_CAR;
	if (msr & UART_MSR_RI)
		mctrl |= TIOCM_RI;
	if (msr & UART_MSR_DSR)
		mctrl |= TIOCM_DSR;
	return mctrl;
}

static const char *uart_sysspec_type(struct uart_port *port)
{
	return "16550A-SYSSPEC";
}

static void uart_sysspec_stop_rx(struct uart_port *port)
{
	unsigned long flags;
	unsigned int ier;

	spin_lock_irqsave(&port->lock, flags);
	ier = hw_inb(UART16550_PORT_REG(port->iobase, UART_SYSSPEC_IER));
	hw_outb(UART16550_PORT_REG(port->iobase, UART_SYSSPEC_IER),
		ier & ~UART_IER_RDI);
	spin_unlock_irqrestore(&port->lock, flags);
}

static int uart_sysspec_handle_irq(struct uart_port *port)
{
	return uart_handle_irq(port->irq, port) == IRQ_HANDLED ? 1 : 0;
}

static void uart_sysspec_release_port(struct uart_port *port)
{
	release_region(port->iobase, UART_SYSSPEC_PORT_SIZE);
}

static int uart_sysspec_request_port(struct uart_port *port)
{
	if (!request_region(port->iobase, UART_SYSSPEC_PORT_SIZE, "uart16550-sysspec"))
		return -EBUSY;
	return 0;
}

static void uart_sysspec_config_port(struct uart_port *port, int flags)
{
	if (flags & UART_CONFIG_TYPE)
		port->type = PORT_16550A;
}

static struct uart_ops uart_sysspec_ops = {
	.tx_empty	= uart_sysspec_tx_empty,
	.set_mctrl	= uart_sysspec_set_mctrl,
	.get_mctrl	= uart_sysspec_get_mctrl,
	.stop_tx	= uart_stop_tx,
	.start_tx	= uart_start_tx,
	.stop_rx	= uart_sysspec_stop_rx,
	.enable_ms	= NULL,
	.startup	= uart_startup,
	.shutdown	= uart_shutdown,
	.set_termios	= uart_set_termios,
	.type		= uart_sysspec_type,
	.release_port	= uart_sysspec_release_port,
	.request_port	= uart_sysspec_request_port,
	.config_port	= uart_sysspec_config_port,
};

static int __init uart16550_sysspec_init(void)
{
	int ret;

	pr_info("uart16550-sysspec: loading (iobase=0x%lx irq=%u)\n",
		uart_iobase, uart_irq);

	uart_sysspec_driver.owner		= THIS_MODULE;
	uart_sysspec_driver.driver_name		= "uart16550_sysspec";
	uart_sysspec_driver.dev_name		= "ttySY";
	uart_sysspec_driver.major		= 0;
	uart_sysspec_driver.minor		= 0;
	uart_sysspec_driver.nr			= UART_SYSSPEC_NR_PORTS;

	uart_sysspec_pdev = platform_device_register_simple("uart16550-sysspec", 0,
							    NULL, 0);
	if (IS_ERR(uart_sysspec_pdev))
		return PTR_ERR(uart_sysspec_pdev);

	ret = uart_register_driver(&uart_sysspec_driver);
	if (ret)
		goto err_pdev;

	spin_lock_init(&uart_sysspec_port.lock);
	uart_sysspec_port.dev		= &uart_sysspec_pdev->dev;
	uart_sysspec_port.iobase	= uart_iobase;
	uart_sysspec_port.iotype	= UPIO_PORT;
	uart_sysspec_port.irq		= uart_irq;
	uart_sysspec_port.uartclk	= UART_SYSSPEC_UARTCLK;
	uart_sysspec_port.fifosize	= UART_SYSSPEC_FIFO_SIZE;
	uart_sysspec_port.ops		= &uart_sysspec_ops;
	uart_sysspec_port.flags		= UPF_FIXED_TYPE | UPF_FIXED_PORT | UPF_SHARE_IRQ;
	uart_sysspec_port.line		= 0;
	uart_sysspec_port.type		= PORT_16550A;
	uart_sysspec_port.handle_irq	= uart_sysspec_handle_irq;

	ret = uart_add_one_port(&uart_sysspec_driver, &uart_sysspec_port);
	if (ret)
		goto err_driver;

	pr_info("uart16550-sysspec: registered /dev/ttySY0 at 0x%lx irq %u\n",
		uart_iobase, uart_irq);
	return 0;

err_driver:
	uart_unregister_driver(&uart_sysspec_driver);
err_pdev:
	platform_device_unregister(uart_sysspec_pdev);
	return ret;
}

static void __exit uart16550_sysspec_exit(void)
{
	uart_remove_one_port(&uart_sysspec_driver, &uart_sysspec_port);
	uart_unregister_driver(&uart_sysspec_driver);
	platform_device_unregister(uart_sysspec_pdev);
	pr_info("uart16550-sysspec: unloaded\n");
}

module_init(uart16550_sysspec_init);
module_exit(uart16550_sysspec_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("SYSSPEC Generated");
MODULE_DESCRIPTION("8250/16550 UART driver generated by SYSSPEC");
