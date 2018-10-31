section .data
    msg db      "hello, world!"

section .text
    global _start
_start:
    push    rbp
    mov     rbp, rsp
    mov     DWORD[rbp-0x4], 0x0

    loop:
    mov     rax, 1
    mov     rdi, 1
    mov     rsi, msg
    mov     rdx, 13
    syscall
    add     DWORD[rbp-0x4], 1
    cmp     DWORD[rbp-0x4], 10
    jne     loop
    
    pop rbp

    mov    rax, 60
    mov    rdi, 0
    syscall