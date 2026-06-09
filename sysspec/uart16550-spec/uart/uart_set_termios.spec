[PROMPT]
Provide complete `uart_set_termios.c` file that implement `uart_set_termios` operation. You can use information from [RELY], [GUARANTEE] and [SPECIFICATION] as described below. Your first line MUST be `#include "uart.h"`. Only provide the implementation of that single function. Your output is wrapped in a C code block, and no other unrelavent code should be given.

[RELY]
```c
static inline void hw_outb(unsigned long port, u8 val);
```
```c
unsigned int uart_get_baud_rate(struct uart_port *port, struct ktermios *termios,
				struct ktermios *old, unsigned int min, unsigned int max);
```
```c
unsigned int uart_get_divisor(struct uart_port *port, unsigned int baud);
```

[GUARANTEE]
```c
void uart_set_termios(struct uart_port *port, struct ktermios *termios,
		      const struct ktermios *old);
```

[SPECIFICATION]
**Pre-Condition**:
- `port`, `termios` are valid.

**Post-Condition**:
- Baud divisor registers are updated for the requested baud rate.
- Line control is configured for 8 data bits, no parity, one stop bit.
- `termios` is encoded with the selected baud rate.

**System Algorithm**:
1. Compute baud with `uart_get_baud_rate` and divisor with `uart_get_divisor`.
2. Under `port->lock`, set DLAB, write DLL/DLM, clear DLAB, set 8N1 LCR.
3. Call `tty_termios_encode_baud_rate`.
