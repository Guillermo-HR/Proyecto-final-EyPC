ORG 100
DEFMACRO m1: #par1, #par2, #eti
#eti: LD A, #par1
ADD #par2
LD A, C
ENDMACRO

inicio:
LD A, (10)
LD B, A
LD C, 10
m1: b, c, eti1
eti2: LD A, B
END