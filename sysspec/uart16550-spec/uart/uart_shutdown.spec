[PROMPT]
Provide complete `uart_shutdown.c` file that implement `uart_shutdown` operation. You can use information from [RELY], [GUARANTEE] and [SPECIFICATION] as described below. Your first line MUST be `#include "uart.h"`. Only provide the implementation of that single function. Your output is wrapped in a C code block, and no other unrelavent code should be given.

[RELY]
```c
static inline void hw_outb(unsigned long port, u8 val);
```

[GUARANTEE]
```c
void uart_shutdown(struct uart_port *port);
```

[SPECIFICATION]
**Pre-Condition**:
- `port` is valid.

**Post-Condition**:
- All UART interrupts are disabled by writing 0 to IER.

**System Algorithm**:
1. Acquire `port->lock` with `spin_lock_irqsave`.
2. Write 0 to IER.
3. Release lock.
