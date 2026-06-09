[PROMPT]
Provide complete `uart_hw_init.c` file that implement `uart_hw_init` operation. You can use information from [RELY], [GUARANTEE] and [SPECIFICATION] as described below. Your first line MUST be `#include "uart.h"`. Only provide the implementation of that single function. Your output is wrapped in a C code block, and no other unrelavent code should be given.

[RELY]
```c
static inline unsigned int hw_inb(unsigned long port);
```
```c
static inline void hw_outb(unsigned long port, u8 val);
```
```c
#define UART_SYSSPEC_IER         1
#define UART_SYSSPEC_FCR         2
#define UART_SYSSPEC_LCR         3
#define UART_SYSSPEC_DLL         0
#define UART_SYSSPEC_DLM         1
#define UART_SYSSPEC_UARTCLK     1843200
```

[GUARANTEE]
```c
void uart_hw_init(struct uart_port *port);
```

[SPECIFICATION]
**Pre-Condition**:
- `port` is a valid non-NULL pointer with `port->iobase` set to the UART I/O base address.

**Post-Condition**:
- UART interrupts are disabled during configuration.
- 16550 FIFO is enabled and receive/transmit FIFOs are cleared.
- Default line format is 8 data bits, no parity, one stop bit.
- Default baud rate is 115200 using `port->uartclk` as the reference clock.

**System Algorithm**:
1. Disable interrupts by writing 0 to IER.
2. Enable and reset FIFO via FCR.
3. Set LCR DLAB bit, program DLL/DLM for 115200 baud.
4. Clear DLAB and set 8N1 in LCR.
