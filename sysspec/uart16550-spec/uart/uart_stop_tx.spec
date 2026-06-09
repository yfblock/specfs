[PROMPT]
Provide complete `uart_stop_tx.c` file that implement `uart_stop_tx` operation. You can use information from [RELY], [GUARANTEE] and [SPECIFICATION] as described below. Your first line MUST be `#include "uart.h"`. Only provide the implementation of that single function. Your output is wrapped in a C code block, and no other unrelavent code should be given.

[RELY]
```c
static inline unsigned int hw_inb(unsigned long port);
```
```c
static inline void hw_outb(unsigned long port, u8 val);
```

[GUARANTEE]
```c
void uart_stop_tx(struct uart_port *port);
```

[SPECIFICATION]
**Pre-Condition**:
- `port` is valid.

**Post-Condition**:
- Transmit-hold-empty interrupt (THRI) is disabled in IER.

**System Algorithm**:
1. Acquire `port->lock`.
2. Read IER, clear UART_IER_THRI bit, write back.
3. Release lock.
