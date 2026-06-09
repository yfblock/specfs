[PROMPT]
Provide complete `uart_tx_empty.c` file that implement `uart_tx_empty` operation. You can use information from [RELY], [GUARANTEE] and [SPECIFICATION] as described below. Your first line MUST be `#include "uart.h"`. Only provide the implementation of that single function. Your output is wrapped in a C code block, and no other unrelavent code should be given.

[RELY]
```c
static inline unsigned int hw_inb(unsigned long port);
```

[GUARANTEE]
```c
unsigned int uart_tx_empty(struct uart_port *port);
```

[SPECIFICATION]
**Pre-Condition**:
- `port` is valid.

**Post-Condition**:
- Returns `TIOCSER_TEMT` if LSR.TEMT and LSR.THRE are both set.
- Returns 0 otherwise.

**System Algorithm**:
1. Read LSR from `port->iobase + UART_LSR`.
2. If both TEMT and THRE bits are set, return `TIOCSER_TEMT`, else return 0.
