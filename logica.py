import os
import sys
import re
# ---- Variables globales ----
     # Tablas de comentarios
global tablaRegistros, tablaPares, tablaBits, tablaCondiciones, palabrasReservadas
tablaRegistros = {'A':'111', 'B':'000', 'C':'001', 'D':'010', 'E':'011', 'H':'100', 'L':'101'}
tablaPares = {'BC':'00', 'DE':'01', 'HL':'10', 'SP':'11', 'AF':'11', 'IX':'10', 'IY':'10'}
tablaBits = {'0':'000', '1':'001', '2':'010', '3':'011', '4':'100', '5':'101', '6':'110', '7':'111'}
tablaCondiciones = {'NZ':'000', 'Z':'001', 'NC':'010', 'C':'011', 'PO':'100', 'PE':'101', 'P':'110', 'M':'111'}
palabrasReservadas = ['DEFMACRO', 'ENDMACRO', 'ORG']
      # Variables para traduccion
global tablaSimbolos, tablaMacros, traduccion, cl
tablaSimbolos = {}
tablaMacros = {} # {'nombre':{parametros:[], lineas:[]}
traduccion = []
cl = 0

def validarArchivo(archivo):
    if not os.path.exists(archivo):
        raise Exception("Archivo no encontrado")
    if not archivo.endswith('.asm'):
        raise Exception("Archivo no es asm")

def leerArchivo(archivo):
    validarArchivo(archivo)
    with open(archivo, 'r') as f:
        return f.read()

def formatoLinea(linea):
    indice = linea.find(';')
    codigo = linea[:indice] if indice != -1 else linea
    if len(codigo) == 0:
        return ['', linea[indice:] if indice != -1 else '']
    codigo = re.sub(r'\t+', ' ', codigo) # Eliminar tabulaciones
    codigo = re.sub(r' *, *', ', ', codigo) # Eliminar espacios entre comas
    codigo = re.sub(r' +', ' ', codigo) # Eliminar espacios multiples
    codigo = codigo.strip() # Eliminar espacios al inicio y al final
    if len(codigo) == 0:
        return ['', linea[indice:] if indice != -1 else '']
    if re.fullmatch(r'[a-zA-Z0-9 ,#:\(\)]*', codigo) == None:
        raise Exception("Error de syntaxis en la linea: " + linea)
    if codigo.count(':') > 1:
        raise Exception("Error de syntaxis en la linea: " + linea)
    return [codigo,f'{linea[indice:]}' if indice != -1 else '']

def crearLST(nombre):
    global traduccion
    lst = ''
    while True:
        if len(traduccion[0]) == 4:
            linea = traduccion.pop(0)
            lst += f'{linea[0]} {linea[1]}\t\t\t{linea[2]}\t\t\t{linea[3]}\n'
        else:
            break
    lst += f'\n{traduccion.pop(0)}\n'
    contador = 0
    while len(traduccion) != 0:
        if contador == 4:
            lst += '\n'
            contador = 0
        linea = traduccion.pop(0)
        lst += f'{linea}\t\t\t\t'
    
    with open(f'{nombre}.lst', 'w') as f:
        f.write(lst)

def agregarSimbolo(simbolo):
    global tablaSimbolos
    if simbolo in palabrasReservadas:
        raise Exception(f'Nombre de simbolo no puede ser palabra reservada: {simbolo}')
    if re.fullmatch(r'[a-zA-Z][a-zA-Z0-9]{0,10}', simbolo) == None:
        raise Exception(f'Nombre de simbolo invalido: {simbolo}')
    if simbolo in tablaSimbolos.keys():
        raise Exception(f'Declaracion duplicada del simbolo: {simbolo}')
    tablaSimbolos[simbolo] = hex(cl)[2:].zfill(4).upper()

def buscarEtiqueta(simbolo):
    global tablaSimbolos
    if simbolo not in tablaSimbolos.keys():
        return None
    return tablaSimbolos[simbolo]

def macroEnsamble(archivo):
    global tablaMacros, traduccion, cl
    macrosActivas = []
    archivoNuevo = []
    for linea in archivo.split('\n'): # Pasada 1
        linea = formatoLinea(linea)
        if re.fullmatch(r'ORG [0-9]{1,5}', linea[0]) != None:
            n = int(linea[0].split(' ')[1])
            if n > 65535:
                raise Exception(f'Numero de direccion fuera de rango: {n}')
            cl = int(f'{n}', 16)
            archivoNuevo.append(['', linea[0]])
            continue
        if re.fullmatch(r'END', linea[0]) != None:
            archivoNuevo.append(['', linea[0]])
            break
        if re.fullmatch(r'DEFMACRO [a-zA-Z][a-zA-Z0-9]{0,10} ?:(( ?#[a-zA-Z][a-zA-Z0-9]{0,12},)* ?#[a-zA-Z][a-zA-Z0-9]{0,12})?', linea[0]) != None:
            nombre = linea[0].split(':')[0].split(' ')[1].strip()
            if nombre in palabrasReservadas:
                raise Exception(f'Nombre de macro no puede ser palabra reservada: {nombre}')
            if nombre in tablaMacros.keys():
                raise Exception(f'Definicio duplicada de macro: {nombre}')
            parametros = linea[0].split(':')[1].strip().split(',')
            parametros = [parametro.strip() for parametro in parametros]
            macrosActivas.append(nombre)
            tablaMacros[nombre] = {'parametros':parametros, 'lineas':[]}
            continue
        if re.fullmatch(r'ENDMACRO', linea[0]) != None:
            try:
                macrosActivas.pop()
            except:
                raise Exception(f'Se intento cerrar una macro sin haberla abierto: {linea}')
            continue
        if len(macrosActivas) != 0:
            for i in macrosActivas:
                tablaMacros[i]['lineas'].append(linea)
            continue
        archivoNuevo.append(linea)
    if len(macrosActivas) != 0:
        raise Exception(f'No se cerraon la(s) macro(s): {macrosActivas}')
    archivo = archivoNuevo.copy()
    # Pasada intermedia para reemplazar macros dentro de macros
    for macro in tablaMacros.keys():
        macroModificada = []
        for linea in tablaMacros[macro]['lineas']:
            if linea[0].count(':') == 1:
                nombreMacro = linea[0].split(':')[0].strip()
                if nombreMacro in tablaMacros.keys():
                    parametros = linea[0].split(':')[1].strip().split(',')
                    parametros = [parametro.strip() for parametro in parametros]
                    if len(parametros) != len(tablaMacros[nombreMacro]['parametros']):
                        raise Exception(f'Numero de parametros incorrecto en la llamada a la macro: {nombreMacro} se esperaban {len(tablaMacros[nombreMacro]["parametros"])}')
                    for lineaMacro in tablaMacros[nombreMacro]['lineas']:
                        nuevaLinea = lineaMacro.copy()
                        # validar que el numero de parametros sea el correcto
                        for i in range(len(parametros)):
                            nuevaLinea[0] = re.sub(f'{tablaMacros[nombreMacro]["parametros"][i]}', parametros[i], nuevaLinea[0])
                        macroModificada.append(nuevaLinea)
                else:
                    macroModificada.append(linea)
            else:
                macroModificada.append(linea)
        tablaMacros[macro]['lineas'] = macroModificada.copy()
    archivoNuevo = []
    for linea in archivo: # Pasada 2
        if len(linea[0]) == 0:
            archivoNuevo.append(linea)
            continue
        if linea[0].count(':') == 1:
            nombreMacro = linea[0].split(':')[0].strip()
            if nombreMacro in tablaMacros.keys():
                parametros = linea[0].split(':')[1].strip().split(',')
                parametros = [parametro.strip() for parametro in parametros]
                if len(parametros) != len(tablaMacros[nombreMacro]['parametros']):
                    raise Exception(f'Numero de parametros incorrecto en la llamada a la macro: {nombreMacro} se esperaban {len(tablaMacros[nombreMacro]["parametros"])}')
                for lineaMacro in tablaMacros[nombreMacro]['lineas']:
                    nuevaLinea = lineaMacro.copy()
                    # validar que el numero de parametros sea el correcto
                    for i in range(len(parametros)):
                        nuevaLinea[0] = re.sub(f'{tablaMacros[nombreMacro]["parametros"][i]}', parametros[i], nuevaLinea[0])
                    archivoNuevo.append(nuevaLinea)
            else:
                archivoNuevo.append(linea)
        else:
            archivoNuevo.append(linea)
    traduccion = archivoNuevo.copy()

def validarMnemonico(linea, pasada1 = True):
    global cl
    # TABLA 1 - Grupo de carga de 8 bits
    # LD r, r'
    if re.fullmatch(r'[l,L][d,D] [A,B,C,D,E,H,L,a,b,c,d,e,h,l], [A,B,C,D,E,H,L,a,b,c,d,e,h,l]', linea) != None:
        if pasada1:
            cl += 1
        return hex(int(f'01{tablaRegistros[linea[3].upper()]}{tablaRegistros[linea[6].upper()]}', 2))[2:].upper().zfill(2)
    
    #LD r,n
    if re.fullmatch(r'[l,L][d,D] [A,B,C,D,E,H,L,a,b,c,d,e,h,l], -?[0-9]{1,3}', linea) != None:
        if pasada1:
            cl += 2
        n = int(linea[6:]) #agarra a n de la cadena, no?
        n_ = bin(abs(n))[2:].zfill(8) #convierte n a binario y lo pone en 8 bits
        if n < 0: #si n es negativo
            n_ = n_.replace('0', '2').replace('1', '0').replace('2', '1') #lo cambia a binario complemento a 2
            n_ = bin(int(n_, 2) + 1)[2:].zfill(8) #lo convierte a binario y lo pone en 8 bits
        return hex(int(f'00{tablaRegistros[linea[3].upper()]}110{n_}', 2))[2:].upper().zfill(4) #retorna el hexadecimal en 8 bits

    #LD r,(HL)
    if re.fullmatch(r'[l,L][d,D] [A,B,C,D,E,H,L,a,b,c,d,e,h,l], ([h,H][l,L])', linea) != None: 
        if pasada1:
            cl += 1
        return hex(int(f'01{tablaRegistros[linea[3].upper()]}110', 2))[2:].upper().zfill(2)
    
    #LD r, (IX+d)
    if re.fullmatch(r'[l,L][d,D] [A,B,C,D,E,H,L,a,b,c,d,e,h,l], (IX[+,-][0-9]{1,3})', linea) != None: 
        if pasada1:
            cl += 3
        d = int(linea[10:-1])
        if linea[9] == '-':
            d = -d
        d_ = bin(abs(d))[2:].zfill(8) #convierte n a binario y lo pone en 8 bits
        if d < 0: #si n es negativo
            d_ = d_.replace('0', '2').replace('1', '0').replace('2', '1') #lo cambia a binario complemento a 2
            d_ = bin(int(d_, 2) + 1)[2:].zfill(8) #lo convierte a binario y lo pone en 8 bits
        return hex(int(f'1101110101{tablaRegistros[linea[3].upper()]}110{d_}', 2))[2:].upper().zfill(6)
    
    #LD r, (IY+d)
    if re.fullmatch(r'[l,L][d,D] [A,B,C,D,E,H,L,a,b,c,d,e,h,l], IY+ -?[0-9]{1,3}', linea) != None: 
        if pasada1:
            cl += 3
        d = int(linea[10:-1])
        if linea[9] == '-':
            d = -d
        d_ = bin(abs(d))[2:].zfill(8) #convierte n a binario y lo pone en 8 bits
        if d < 0: #si n es negativo
            d_ = d_.replace('0', '2').replace('1', '0').replace('2', '1') #lo cambia a binario complemento a 2
            d_ = bin(int(d_, 2) + 1)[2:].zfill(8) #lo convierte a binario y lo pone en 8 bits
        return hex(int(f'1111110101{tablaRegistros[linea[3].upper()]}110{d_}', 2))[2:].upper().zfill(6)
        
    #LD (HL), r
    if re.fullmatch(r'[l,L][d,D] \([h,H][l,L]\), [A,B,C,D,E,H,L,a,b,c,d,e,h,l]', linea) != None:
        if pasada1:
            cl += 1
        return hex(int(f'01110{tablaRegistros[linea[9].upper()]}', 2))[2:].upper().zfill(2)
        
    #LD (IX+d), r
    if re.fullmatch(r'[l,L][d,D] \([i,I][x,X][+,-][0-9]{1,3}\), [A,B,C,D,E,H,L,a,b,c,d,e,h,l]', linea) != None:
        if pasada1:
            cl += 3
        d = int(linea[7:linea.index(')')])
        if linea[6] == '-':
            d = -d
        d_ = bin(abs(d))[2:].zfill(8) #convierte n a binario y lo pone en 8 bits
        if d < 0: #si n es negativo
            d_ = d_.replace('0', '2').replace('1', '0').replace('2', '1') #lo cambia a binario complemento a 2
            d_ = bin(int(d_, 2) + 1)[2:].zfill(8) #lo convierte a binario y lo pone en 8 bits
        return hex(int(f'1101110101110{tablaRegistros[linea[-1].upper()]}{d_}', 2))[2:].upper().zfill(6)
    
    #LD (IY+d),r
    if re.fullmatch(r'[l,L][d,D] \([i,I][y,Y][+,-][0-9]{1,3}\), [A,B,C,D,E,H,L,a,b,c,d,e,h,l]', linea) != None:
        if pasada1:
            cl += 3
        d = int(linea[7:linea.index(')')])
        if linea[6] == '-':
            d = -d
        d_ = bin(abs(d))[2:].zfill(8) #convierte n a binario y lo pone en 8 bits
        if d < 0: #si n es negativo
            d_ = d_.replace('0', '2').replace('1', '0').replace('2', '1') #lo cambia a binario complemento a 2
            d_ = bin(int(d_, 2) + 1)[2:].zfill(8) #lo convierte a binario y lo pone en 8 bits
        return hex(int(f'1111110101110{tablaRegistros[linea[-1].upper()]}{d_}', 2))[2:].upper().zfill(6)

    #LD (HL), n
    if re.fullmatch(r'[l,L][d,D] \([h,H][l,L]\), -?[0-9]{1,3}', linea) != None: 
        if pasada1:
            cl += 2
        n = int(linea[9:]) #agarra a n de la cadena, no?
        n_ = bin(abs(n))[2:].zfill(8) #convierte n a binario y lo pone en 8 bits
        if n < 0: #si n es negativo
            n_ = n_.replace('0', '2').replace('1', '0').replace('2', '1') #lo cambia a binario complemento a 2
            n_ = bin(int(n_, 2) + 1)[2:].zfill(8) #lo convierte a binario y lo pone en 8 bits
        return hex(int(f'00110110{n_}', 2))[2:].upper().zfill(4) #retorna el hexadecimal en 8 bits
    
    #LD (IX+d), n
    if re.fullmatch(r'[l,L][d,D] \([i,I][x,X][+,-][0-9]{1,3}\), -?[0-9]{1,3}', linea) != None:
        if pasada1:
            cl += 4
        d = int(linea[7:linea.index(')')])
        if linea[6] == '-':
            d = -d
        d_ = bin(abs(d))[2:].zfill(8) #convierte n a binario y lo pone en 8 bits
        if d < 0: #si n es negativo
            d_ = d_.replace('0', '2').replace('1', '0').replace('2', '1') #lo cambia a binario complemento a 2
            d_ = bin(int(d_, 2) + 1)[2:].zfill(8) #lo convierte a binario y lo pone en 8 bits

        n = int(linea[linea.index(',')+1:])
        n_ = bin(abs(n))[2:].zfill(8) #convierte n a binario y lo pone en 8 bits
        if n < 0: #si n es negativo
            n_ = n_.replace('0', '2').replace('1', '0').replace('2', '1') #lo cambia a binario complemento a 2
            n_ = bin(int(n_, 2) + 1)[2:].zfill(8) #lo convierte a binario y lo pone en 8 bits
        return hex(int(f'1101110100110110{d_}{n_}', 2))[2:].upper().zfill(8)
        
    #LD (IY+d), n
    if re.fullmatch(r'[l,L][d,D] \([i,I][y,Y][+,-][0-9]{1,3}\), -?[0-9]{1,3}', linea) != None:
        if pasada1:
            cl += 4
        d = int(linea[7:linea.index(')')])
        if linea[6] == '-':
            d = -d
        d_ = bin(abs(d))[2:].zfill(8)
        if d < 0: 
            d_ = d_.replace('0', '2').replace('1', '0').replace('2', '1') 
            d_ = bin(int(d_, 2) + 1)[2:].zfill(8) 

        n = int(linea[linea.index(',')+1:])
        n_ = bin(abs(n))[2:].zfill(8) 
        if n < 0: 
            n_ = n_.replace('0', '2').replace('1', '0').replace('2', '1') 
            n_ = bin(int(n_, 2) + 1)[2:].zfill(8) 
        return hex(int(f'1111110100110110{d_}{n_}', 2))[2:].upper().zfill(8)

    #LD A, (BC) y LD A, (DE)
    if re.fullmatch(r'[l,L][d,D] [A,a], [[[b,B][c,C]],[[d,D][e,E]]]', linea) != None:
        if pasada1:
            cl += 1
        return hex(int(f'00{tablaPares[linea[6:8]]}1010', 2))[2:].upper().zfill(2)
        
    #LD A, (nn)
    if re.fullmatch(r'[l,L][d,D] [a,A], \([0-9]{1,4}\)', linea) != None:
        if pasada1:
            cl += 3
        nn = linea[7:-1].zfill(4)
        nn = nn[2:] + nn[:2]
        return f"{hex(int(f'00111010', 2))[2:]}{nn}".upper().zfill(6)
        
    # LD (BC), A y LD (DE), A
    if re.fullmatch(r'[l,L][d,D] \([[[b,B][c,C]],[[d,D][e,E]]]\), [A,a]', linea) != None:
        if pasada1:
            cl += 1
        return hex(int(f'00{tablaPares[linea[4:6]]}0010', 2))[2:].upper().zfill(2)
    
    # LD (nn), A
    if re.fullmatch(r'[l,L][d,D] \([0-9]{1,4}\), [A,a]', linea) != None:
        if pasada1:
            cl += 3
        nn = linea[4:linea.index(')')].zfill(4)
        nn = nn[2:]+nn[:2]
        return f"{hex(int(f'00110010', 2))[2:]}{nn}".upper().zfill(6)
    
    # LD A, I
    if re.fullmatch(r'[l,L][d,D] [A,a], [I,i]', linea) != None:
        if pasada1:
            cl += 2  
        return hex(int(f'1110110101010111', 2))[2:].upper().zfill(4)
        
    # LD A, R
    if re.fullmatch(r'[l,L][d,D] [A,a], [R,r]', linea) != None:
        if pasada1:
            cl += 2  
        return hex(int(f'1110110101011111', 2))[2:].upper().zfill(4)

    # LD I, A
    if re.fullmatch(r'[l,L][d,D] [I,i], [A,a]', linea) != None:
        if pasada1:
            cl += 2  
        return hex(int(f'1110110101000111', 2))[2:].upper().zfill(4)

    # LD R, A
    if re.fullmatch(r'[l,L][d,D] [R,r], [A,a]', linea) != None:
        if pasada1:
            cl += 2
        return hex(int(f'1110110101001111', 2))[2:].upper().zfill(4)
    
    # Tabla 2 - Grupo de carga de 16 bits
    # PUSH IX
    if re.fullmatch(r'[p,P][u,U][s,S][h,H] [i,I][x,X]', linea) != None:
        if pasada1:
            cl += 2  
        return hex(int(f'1101110111100101', 2))[2:].upper().zfill(4)

    # PUSH IY
    if re.fullmatch(r'[p,P][u,U][s,S][h,H] [i,I][y,Y]', linea) != None:
        if pasada1:
            cl += 2  
        return hex(int(f'1111110111100101', 2))[2:].upper().zfill(4)
    
    # Tabla 3 Grupo de intercambio y transferencia de búsqueda de bloques
    # LDIR
    if re.fullmatch(r'[l,L][d,D][i,I][r,R]', linea) != None:
        if pasada1:
            cl += 2 
        return hex(int(f'1110110110110000', 2))[2:].upper().zfill(4)

    # LDD
    if re.fullmatch(r'[l,L][d,D]{2}', linea) != None:
        if pasada1:
            cl += 2  
        return hex(int(f'1110110110101000', 2))[2:].upper().zfill(4)

    # LDDR
    if re.fullmatch(r'[l,L][d,D]{2}[r,R]', linea) != None:
        if pasada1:
            cl += 2 
        return hex(int(f'1110110110111000', 2))[2:].upper().zfill(4)
    
    # CPI
    if re.fullmatch(r'[c,C][p,P][i,I]', linea) != None:
        if pasada1:
            cl += 2
        return hex(int(f'1110110110100001', 2))[2:].upper().zfill(4)

    # CPIR
    if re.fullmatch(r'[c,C][p,P][i,I][r,R]', linea) != None:
        if pasada1:
            cl += 2
        return hex(int(f'1110110110110001', 2))[2:].upper().zfill(4)
    
    # CPD
    if re.fullmatch(r'[c,C][p,P][d,D]', linea) != None:
        if pasada1:
            cl += 2  
        return hex(int(f'1110110110101001', 2))[2:].upper().zfill(4)

    # Tabla 4 - Grupo aritmético y lógico de 8 bits
    # ADD r
    if re.fullmatch(r'[a,A][d,D][d,D] [A,B,C,D,E,H,L,a,b,c,d,e,h,l]', linea) != None:
        if pasada1:
            cl += 1     
        return hex(int(f'10000{tablaRegistros[linea[-1].upper()]}', 2))[2:].upper().zfill(2)
    
    # Mnemonicos faltantes
    raise Exception("Mnemonico no reconocido: " + linea)

def pasada1():
    global traduccion
    nuevaTraduccion = []
    for linea in traduccion:
        if len(linea[0]) == 0:
            nuevaTraduccion.append(['','', '',linea[1]])
            continue
        if linea[0].count(':') == 1:
            nombre = linea[0].split(':')[0].strip()
            agregarSimbolo(nombre)
            if len(linea[0].split(':')[1].strip()) == 0:
                nuevaTraduccion.append([hex(cl)[2:].zfill(4).upper(), '', linea[0], linea[1]])
                continue
            nuevaTraduccion.append([hex(cl)[2:].zfill(4).upper(), validarMnemonico(linea[0].split(':')[1].strip()), linea[0], linea[1]])
            continue
        nuevaTraduccion.append([hex(cl)[2:].zfill(4).upper(), validarMnemonico(linea[0]), linea[0], linea[1]])
    traduccion = nuevaTraduccion.copy()

def pasada2():
    global traduccion
    nuevaTraduccion = []
    for linea in traduccion:
        if len(linea[2]) == 0:
            nuevaTraduccion.append(linea)
            continue
        if len(linea[1]) == 0:
            if linea[2].count(':') == 1:
                nuevaTraduccion.append(linea)
                continue
            for simbolo in tablaSimbolos.keys():
                linea[2] = re.sub(simbolo, buscarEtiqueta(simbolo), linea[2])
            linea[1] = validarMnemonico(linea[2], False)
        nuevaTraduccion.append(linea)
    traduccion = nuevaTraduccion.copy()

def agregarTS():
    global traduccion
    traduccion.append('TABLA DE SIMBOLOS')
    for simbolo, dir in tablaSimbolos.items():
        traduccion.append(f'{dir} {simbolo}')

def ensamblar(codigo):
    macroEnsamble(codigo)
    try:
        pasada1()
        pasada2()
    except:
        return False
    agregarTS()
    crearLST('programa')
    return True

if __name__ == "__main__":
    #nombre = "prueba.asm"
    #archivo = leerArchivo(nombre)
    #macroEnsamble(archivo)
    #pasada1()
    #pasada2()
    #agregarTS()
    #crearLST(nombre.split('.')[0])
    pass