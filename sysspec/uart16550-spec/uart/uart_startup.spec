[PROMPT]
Provide complete `uart_startup.c` file that implement `uart_startup` operation. You can use information from [RELY], [GUARANTEE] and [SPECIFICATION] as described below. Your first line MUST be `#include "uart.h"`. Only provide the implementation of that single function. Your output is wrapped in a C code block, and no other unrelavent code should be given.

[RELY]
```c
void uart_hw_init(struct uart_port *port);
```
```c
static inline unsigned int hw_inb(unsigned long port);
```
```c
static inline void hw_outb(unsigned long port, u8 val);
```

[GUARANTEE]
```c
int uart_startup(struct uart_port *port);
```

[SPECIFICATION]
**Pre-Condition**:
- `port` is valid and `port->lock` is initialized.

**Post-Condition**:
- Hardware has been initialized via `uart_hw_init`.
- Receive and transmit-hold-empty interrupts are enabled.
- Returns 0 on success.

**System Algorithm**:
1. Acquire `port->lock` with `spin_lock_irqsave`.
2. Call `uart_hw_init(port)`.
3. Enable `UART_IER_RDI | UART_IER_THRI` in IER.
4. Release lock and return 0.
