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
#define UART_SYSSPEC_FCR_RX_TRIG UART_FCR_R_TRIG_14
```

[GUARANTEE]
```c
void uart_hw_init(struct uart_port *port);
```

[SPECIFICATION]
**Pre-Condition**:
- `port` is valid with `port->iobase` configured.

**Post-Condition**:
- FIFO enabled with receive trigger level `UART_SYSSPEC_FCR_RX_TRIG` for better batching.
- Default 115200 8N1 line settings are applied.

**System Algorithm**:
1. Disable interrupts.
2. Enable FIFO with clear bits and `UART_SYSSPEC_FCR_RX_TRIG`.
3. Program divisor for 115200 baud and set 8N1.
