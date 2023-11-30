     ORG 300

DEFMACRO macro1: #a1, #a2, #eti
#eti:LD #a1, #a2
cp 3
DEC A
DEFMACRO macro2: #a3
ld c,#a3
ENDMACRO
ENDMACRO

; Programa:
macro1:x,l,emacro
macro2:b
inicio:
     LD A, (360)                ; Cargar el numero al que se le va a calcular el factorial
     CP 9
     JP P, eti1                  ; Si el numero es mayor a 8 ir a eti1
     CP 0
     JP M, eti1                  ; Si el numero es negativo ir a eti1
     CP 2
     JP M, eti2                  ; si el numero es 0 o 1 ir a eti2
     LD E, A
     LD D, 0
     PUSH DE
     POP HL                      ; Inicializar HL
     DEC A                       ; Se modifca A para que sea el numero por el cual se va a multiplicar el resultado
     LD B, A                     ; Guardar el valor de A
CicloP:
     LD A, B                     ; Actualizar A
     PUSH HL
     POP DE                      ; Guardar en DE el valor que se va a sumar A veces a HL
     CP 2
     JP M, guardar
cicloS:
     ADD HL, DE                  ; Multiplicar
     DEC A                       ; Actualizar el valor de A
     CP 2
     JP P, cicloS
     DEC B                       ; Actualizar el valor de B
     
     JP guardar
eti1:
     LD HL, -1               ; Se coloca -1 para indicar error
     JP guardar
eti2:
     LD HL, 1                    ; El factorial de 0 y 1 es 1
guardar:
     PUSH HL                     ; Guardar en la pila el resultado
     HALT
END