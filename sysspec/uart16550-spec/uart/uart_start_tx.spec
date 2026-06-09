[PROMPT]
Provide complete `uart_start_tx.c` file that implement `uart_start_tx` operation. You can use information from [RELY], [GUARANTEE] and [SPECIFICATION] as described below. Your first line MUST be `#include "uart.h"`. Only provide the implementation of that single function. Your output is wrapped in a C code block, and no other unrelavent code should be given.

[RELY]
```c
static inline unsigned int hw_inb(unsigned long port);
```
```c
static inline void hw_outb(unsigned long port, u8 val);
```

[GUARANTEE]
```c
void uart_start_tx(struct uart_port *port);
```

[SPECIFICATION]
**Pre-Condition**:
- `port->state` and `port->state->port.xmit_fifo` are valid.

**Post-Condition**:
- As many pending transmit characters as possible are written to THR while LSR.THRE is set.
- `port->icount.tx` is incremented for each transmitted byte.
- THRI is enabled in IER if characters remain in the xmit fifo.

**System Algorithm**:
1. Acquire `port->lock`.
2. Drain `xmit_fifo` with `kfifo_get` into THR while THRE is available.
3. If fifo is non-empty, enable THRI in IER.
4. Release lock.
