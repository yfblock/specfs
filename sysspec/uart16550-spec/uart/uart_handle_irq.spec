[PROMPT]
Provide complete `uart_handle_irq.c` file that implement `uart_handle_irq` operation. You can use information from [RELY], [GUARANTEE] and [SPECIFICATION] as described below. Your first line MUST be `#include "uart.h"`. Only provide the implementation of that single function. Your output is wrapped in a C code block, and no other unrelavent code should be given.

[RELY]
```c
static inline unsigned int hw_inb(unsigned long port);
```
```c
void uart_insert_char(struct uart_port *port, unsigned int status, unsigned int overrun,
		      unsigned int ch, unsigned int flag);
```
```c
void uart_write_wakeup(struct uart_port *port);
```

[GUARANTEE]
```c
irqreturn_t uart_handle_irq(int irq, void *dev_id);
```

[SPECIFICATION]
**Pre-Condition**:
- `dev_id` points to the `struct uart_port` registered for this IRQ.

**Post-Condition**:
**Case 1 (No interrupt pending)**:
- Returns `IRQ_NONE`.

**Case 2 (Interrupt handled)**:
- Received bytes are inserted into the TTY flip buffer.
- Transmit wakeup is invoked when THRE is set.
- Flip buffer is pushed to the line discipline.
- Returns `IRQ_HANDLED`.

**System Algorithm**:
1. Cast `dev_id` to `struct uart_port *` and acquire `port->lock`.
2. Read IIR; if `UART_IIR_NO_INT`, release lock and return `IRQ_NONE`.
3. Loop while interrupts pending: on LSR.DR read RBR and `uart_insert_char`; on LSR.THRE call `uart_write_wakeup`.
4. Push flip buffer, release lock, return `IRQ_HANDLED`.
