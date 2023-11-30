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
    if re.fullmatch(r'[a-zA-Z0-9 ,#:\(\)-]*', codigo) == None:
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
    #LD dd, nn
    if re.fullmatch('[l,L][d,D] [BC,DE,HL,SP,bc,de,hl,sp] -?[0-9]{1,4}', linea) != None:
        if pasada1:
            cl +=3
        nn = int(linea[7:])
        nn_ = bin(abs(nn))[2:].zfill(16)
        if nn < 0:
            nn_ = nn_.replace('0', '2').replace('1', '0').replace('2', '1')
            nn_ = bin(int(nn_, 2) + 1)[2:].zfill(16)
        return hex(int(f'00{tablaPares[linea[3:5]]}0001{nn_}', 2))[2:].upper().zfill(6)
    
    #LD IX,nn
    if re.fullmatch('[l,L][d,D] [i,I][X,x], -?[0-9]{1,4}', linea) != None:
        if pasada1:
            cl +=4
        nn = int(linea[7:])
        nn_ = bin(abs(nn))[2:].zfill(16) 
        if nn < 0:
            nn_ = nn_.replace('0', '2').replace('1', '0').replace('2', '1')
            nn_ = bin(int(nn_, 2) + 1)[2:].zfill(16)
        return hex(int(f'1101110100100001{nn_}', 2))[2:].upper().zfill(8)
  
  #LD IY, nn
    if re.fullmatch('[l,L][d,D] [i,I][Y,y], -?[0-9]{1,4}', linea) != None:
        if pasada1:
            cl +=4
        nn = int(linea[7:])
        nn_ = bin(abs(nn))[2:].zfill(16) 
        if nn < 0:
            nn_ = nn_.replace('0', '2').replace('1', '0').replace('2', '1')
            nn_ = bin(int(nn_, 2) + 1)[2:].zfill(16)
        return hex(int(f'1111110100100001{nn_}', 2))[2:].upper().zfill(8)
    
    # LD HL, nn
    if re.fullmatch('[l,L][d,D] [h,H][l,L], -?[0-9]{1,4}', linea) != None:
        if pasada1:
            cl +=3
        nn = int(linea[7:])
        nn_ = bin(abs(nn))[2:].zfill(16) 
        if nn < 0:
            nn_ = nn_.replace('0', '2').replace('1', '0').replace('2', '1')
            nn_ = bin(int(nn_, 2) + 1)[2:].zfill(16)
        return hex(int(f'00101010{nn_}', 2))[2:].upper().zfill(6)
  #LD HL, (nn)
    if re.fullmatch('[l,L][d,D] [h,H][l,L], \(-?[0-9]{2}\)', linea) != None:
        if pasada1:
            cl +=3
        nn = linea[8:-1].zfill(4)
        nn = nn[2:] + nn[:2]
        return hex(int(f'00101010{nn}', 2))[2:].upper().zfill(6)

  #LD dd, (nn)
    if re.fullmatch('[l,L][d,D] [BC,DE,HL,SP,bc,de,hl,sp]{2}, \(-?[0-9]{2}\)', linea) != None:
        if pasada1:
            cl +=4
        nn = linea[8:-1].zfill(4)
        nn = nn[2:] + nn[:2]
        return hex(int(f'1110110101{tablaPares[linea[3:5]]}1011{nn}', 2))[2:].upper().zfill(8)
  
  #LD IX, (nn)
    if re.fullmatch('[l,L][d,D] [i,I][x,X], \(-?[0-9]{2}\)', linea) != None:
        if pasada1:
            cl +=4
        nn = linea[8:-1].zfill(4)
        nn = nn[2:] + nn[:2]
        return hex(int(f'1101110100101010{nn}', 2))[2:].upper().zfill(8)
  
  #LD IY, (nn)
    if re.fullmatch('[l,L][d,D] [h,H][l,L], \(-?[0-9]{2}\)', linea) != None:
        if pasada1:
            cl +=4
        nn = linea[8:-1].zfill(4)
        nn = nn[2:] + nn[:2]
        return hex(int(f'1111110100101010{nn}', 2))[2:].upper().zfill(8)
  
  #LD (nn), HL
    if re.fullmatch(r'[l,L][d,D] \([0-9]{1,4}\), [h,H][l,L]', linea) != None:
        if pasada1:
            cl += 3
        nn = linea[4:linea.index(')')].zfill(4)
        nn = nn[2:]+nn[:2]
        return hex(int(f'00100010{nn}', 2))[2:].upper().zfill(6)
  
  #LD (nn), dd
    if re.fullmatch(r'[l,L][d,D] \([0-9]{1,4}\), [BC,DE,HL,SP,bc,de,hl,sp]{2}', linea) != None:
        if pasada1:
            cl += 4
        nn = linea[4:linea.index(')')].zfill(4)
        nn = nn[2:]+nn[:2]
        return hex(int(f'1110110101{tablaPares[linea[6:8]]}0011{nn}', 2))[2:].upper().zfill(8) #checa la posicion de tablaPares
  
  #LD (nn), IX
    if re.fullmatch(r'[l,L][d,D] \([0-9]{1,4}\), [i,I][x,X]', linea) != None:
        if pasada1:
            cl += 4
        nn = linea[4:linea.index(')')].zfill(4)
        nn = nn[2:]+nn[:2]
        return hex(int(f'1101110100100010{nn}', 2))[2:].upper().zfill(8)
    
  #LD (nn), IY
    if re.fullmatch(r'[l,L][d,D] \([0-9]{1,4}\), [i,I][y,Y]', linea) != None:
        if pasada1:
            cl += 4
        nn = linea[4:linea.index(')')].zfill(4)
        nn = nn[2:]+nn[:2]
        return hex(int(f'1111110100100010{nn}', 2))[2:].upper().zfill(8)
    
  #LD SP, HL
    if re.fullmatch(r'[l,L][d,D] [s,S][p,P], [h,H][l,L]', linea) != None:
        if pasada1:
            cl += 1
        return hex(int(f'11111001', 2))[2:].upper().zfill(2)
    
  #LD SP, IX
    if re.fullmatch(r'[l,L][d,D] [s,S][p,P], [i,I][x,X]', linea) != None:
        if pasada1:
            cl += 2
        return hex(int(f'1101110111111001', 2))[2:].upper().zfill(4)
  
  #LD SP, IY
    if re.fullmatch(r'[l,L][d,D] [s,S][p,P], [i,I][y,Y]', linea) != None:
        if pasada1:
            cl += 2
        return hex(int(f'1111110111111001', 2))[2:].upper().zfill(4)
  
  #PUSH qq
    if re.fullmatch(r'[p,P][u,U][s,S][h,H] [BC,DE,HL,AF,bc,de,hl,af]{2}', linea) != None:
        if pasada1:
            cl += 1
        return hex(int(f'11{tablaPares[linea[5:7]]}0101', 2))[2:].upper().zfill(2)
  
  #POP qq
    if re.fullmatch(r'[p,P][o,O][p,P] [BC,DE,HL,AF,bc,de,hl,af]{2}', linea) != None:
        if pasada1:
            cl += 1
        return hex(int(f'11{tablaPares[linea[4:6]]}0001', 2))[2:].upper().zfill(2)

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
    
    #POP IX
    if re.fullmatch(r'[p,P][o,O][p,P] [i,I][x,X]', linea) != None:
        if pasada1:
            cl += 2
        return hex(int(f'1101110111100001', 2))[2:].upper().zfill(4)   
    
    #POP IY
    if re.fullmatch(r'[p,P][o,O][p,P] [i,I][y,Y]', linea) != None:
        if pasada1:
            cl += 2
        return hex(int(f'1111110111100001', 2))[2:].upper().zfill(4)
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

    # CPDR
    if re.fullmatch(r'[c,C][p,P][d,D][r,R]', linea) != None:
        if pasada1:
            cl += 4 
        return 
    
    # Tabla 4 - Grupo aritmético y lógico de 8 bits
    # ADD r
    if re.fullmatch(r'[a,A][d,D][d,D] [A,B,C,D,E,H,L,a,b,c,d,e,h,l]', linea) != None:
        if pasada1:
            cl += 1     
        return hex(int(f'10000{tablaRegistros[linea[-1].upper()]}', 2))[2:].upper().zfill(2)
    
    #ADD n
    if re.fullmatch(r'[a,A][d,D]{2} -?[0-9]{1,3}', linea) != None:
        if pasada1:
         cl += 2
        n = int(linea[4:]) 
        n_ = bin(abs(n))[2:].zfill(8) 
        if n < 0: 
            n_ = n_.replace('0', '2').replace('1', '0').replace('2', '1') 
            n_ = bin(int(n_, 2) + 1)[2:].zfill(4) 
        return hex(int(f'11{n_}110', 2))[2:].upper().zfill(2) 
  
    #ADD (HL)
    if re.fullmatch(r'[a,A][d,D]{2} \([h,H][l,L]\)', linea) != None:
        if pasada1:
            cl += 1
        return hex(int(f'10{tablaPares[linea[5].upper()]}110', 2))[2:].upper().zfill(2)
    
    #ADD (IX+d)
    if re.fullmatch(r'[a,A][d,D]{2} (IX[+,-][0-9]{1,3})', linea) != None: 
        if pasada1:
            cl += 3
        d = int(linea[10:-1])
        if linea[9] == '-':
            d = -d
        d_ = bin(abs(d))[2:].zfill(8)
        if d < 0: 
            d_ = d_.replace('0', '2').replace('1', '0').replace('2', '1') 
            d_ = bin(int(d_, 2) + 1)[2:].zfill(8) 
        return hex(int(f'11011101{tablaPares[linea[3].upper()]}10{d_}101', 2))[2:].upper().zfill(6)
  
    #ADD (IY+d)
    if re.fullmatch(r'[a,A][d,D]{2} (IY[+,-][0-9]{1,3})', linea) != None: 
        if pasada1:
            cl += 3
        d = int(linea[10:-1])
        if linea[9] == '-':
            d = -d
        d_ = bin(abs(d))[2:].zfill(8)
        if d < 0: 
            d_ = d_.replace('0', '2').replace('1', '0').replace('2', '1') 
            d_ = bin(int(d_, 2) + 1)[2:].zfill(8) 
        return hex(int(f'11111101{tablaPares[linea[3].upper()]}10{d_}110', 2))[2:].upper().zfill(6)
  
    #ADC s
    if re.fullmatch(r'[a,A][d,D][c,C] [A,B,C,D,E,H,L,a,b,c,d,e,h,l]', linea) != None:
        if pasada1:
            cl += 1
        return hex(int(f'10001{tablaRegistros[linea[4].upper()]}', 2))[2:].upper().zfill(2)
      
  #SUB s
    if re.fullmatch(r'[d,D][e,E][c,C] [A,B,C,D,E,H,L,a,b,c,d,e,h,l]', linea) != None:
        if pasada1:
            cl += 1
        return hex(int(f'10010{tablaRegistros[linea[4].upper()]}', 2))[2:].upper().zfill(2)
  
  #SBC s
    if re.fullmatch(r'[d,D][e,E][c,C] [A,B,C,D,E,H,L,a,b,c,d,e,h,l]', linea) != None:
        if pasada1:
            cl += 1
        return hex(int(f'10011{tablaRegistros[linea[4].upper()]}', 2))[2:].upper().zfill(2)
    
  #AND s 
    if re.fullmatch(r'[d,D][e,E][c,C] [A,B,C,D,E,H,L,a,b,c,d,e,h,l]', linea) != None:
        if pasada1:
            cl += 1
        return hex(int(f'10100{tablaRegistros[linea[4].upper()]}', 2))[2:].upper().zfill(2)
    
  #OR s
    if re.fullmatch(r'[o,D][r,R] [A,B,C,D,E,H,L,a,b,c,d,e,h,l]', linea) != None:
        if pasada1:
            cl += 1
        return hex(int(f'10110{tablaRegistros[linea[3].upper()]}', 2))[2:].upper().zfill(2)
    
  #XOR s
    if re.fullmatch(r'[x,X][o,O][r,R] [A,B,C,D,E,H,L,a,b,c,d,e,h,l]', linea) != None:
        if pasada1:
            cl += 1
        return hex(int(f'10101{tablaRegistros[linea[4].upper()]}', 2))[2:].upper().zfill(2) #Registro
 
  #CP s 
    if re.fullmatch(r'[c,C][p,P] [A,B,C,D,E,H,L,a,b,c,d,e,h,l]', linea) != None:
        if pasada1:
            cl += 1
        return hex(int(f'10111{tablaRegistros[linea[4].upper()]}', 2))[2:].upper().zfill(2)
    
    if re.fullmatch(r'[c,C][p,P] -?[0-9]{1,3}', linea) != None:
        if pasada1:
            cl += 2
        n = int(linea[3:]) 
        n_ = bin(abs(n))[2:].zfill(8) 
        if n < 0: 
            n_ = n_.replace('0', '2').replace('1', '0').replace('2', '1') 
            n_ = bin(int(n_, 2) + 1)[2:].zfill(8) 
        return hex(int(f'11111110{n_}', 2))[2:].upper().zfill(4) 
    
    if re.fullmatch(r'[c,C][p,P] \([h,H][l,L]\)', linea) != None:
            if pasada1:
                cl += 1
            return hex(int(f'10111110', 2))[2:].upper().zfill(2)
    
    if re.fullmatch(r'[c,C][p,P] (IX[+,-][0-9]{1,3})', linea) != None: 
        if pasada1:
            cl += 3
        d = int(linea[10:-1])
        if linea[9] == '-':
            d = -d
        d_ = bin(abs(d))[2:].zfill(8)
        if d < 0: 
            d_ = d_.replace('0', '2').replace('1', '0').replace('2', '1') 
            d_ = bin(int(d_, 2) + 1)[2:].zfill(8) 
        return hex(int(f'11111101{tablaPares[linea[5].upper()]}10{d_}110', 2))[2:].upper().zfill(6)
    
  #INC r
    if re.fullmatch(r'[i,I][n,N][c,C] [A,B,C,D,E,H,L,a,b,c,d,e,h,l]', linea) != None:
        if pasada1:
            cl += 1
        return hex(int(f'00{tablaRegistros[linea[4].upper()]}100', 2))[2:].upper().zfill(2)
    
  #INC (HL)
    if re.fullmatch(r'[i,I][n,N][c,C] \([h,H][l,L]\)', linea) != None:
        if pasada1:
            cl += 1
        return hex(int(f'00110100', 2))[2:].upper().zfill(2)
    
  #INC (IX+d)
    if re.fullmatch(r'[i,I][n,N][c,C] (IX[+,-][0-9]{1,3})', linea) != None: 
        if pasada1:
            cl += 3
        d = int(linea[10:-1])
        if linea[9] == '-':
            d = -d
        d_ = bin(abs(d))[2:].zfill(8)
        if d < 0: 
            d_ = d_.replace('0', '2').replace('1', '0').replace('2', '1') 
            d_ = bin(int(d_, 2) + 1)[2:].zfill(8) 
        return hex(int(f'11011101{tablaPares[linea[5].upper()]}00110{d_}', 2))[2:].upper().zfill(6)
    
  #DEC d
    if re.fullmatch(r'[d,D][e,E][c,C] [A,B,C,D,E,H,L,a,b,c,d,e,h,l]', linea) != None:
        if pasada1:
            cl += 1
        return hex(int(f'00{tablaRegistros[linea[4].upper()]}101', 2))[2:].upper().zfill(2)
    
    if re.fullmatch(r'[d,D][e,E][c,C] \([h,H][l,L]\)', linea) != None:
        if pasada1:
            cl += 1
        return hex(int(f'00110101', 2))[2:].upper().zfill(2)

    if re.fullmatch(r'[d,D][e,E][c,C] (IX[+,-][0-9]{1,3})', linea) != None: 
        if pasada1:
            cl += 3
        d = int(linea[10:-1])
        if linea[9] == '-':
            d = -d
        d_ = bin(abs(d))[2:].zfill(8)
        if d < 0: 
            d_ = d_.replace('0', '2').replace('1', '0').replace('2', '1') 
            d_ = bin(int(d_, 2) + 1)[2:].zfill(8) 
        return hex(int(f'11011101{tablaPares[linea[5].upper()]}00{d_}101', 2))[2:].upper().zfill(6)
    
    if re.fullmatch(r'[d,D][e,E][c,C] (IY[+,-][0-9]{1,3})', linea) != None: 
        if pasada1:
            cl += 3
        d = int(linea[10:-1])
        if linea[9] == '-':
            d = -d
        d_ = bin(abs(d))[2:].zfill(8)
        if d < 0: 
            d_ = d_.replace('0', '2').replace('1', '0').replace('2', '1') 
            d_ = bin(int(d_, 2) + 1)[2:].zfill(8) 
        return hex(int(f'11111101{tablaPares[linea[5].upper()]}00110101', 2))[2:].upper().zfill(6)
    
    # Tabla 5  - Grupo aritmetico y de control de la CPU
  #HALT
    if re.fullmatch('[H,h][a,A][L,l][t,T]', linea) != None:
        if pasada1:
            cl += 1
        return hex(int(f'01110110', 2))[2:].upper().zfill(2)
    
    # Tabla 6 - Grupo aritmetico de 16 bits
  #ADD HL, ss
    if re.fullmatch('[a,A][d,D][d,D] [h,H][l,L], [BC,DE,HL,SP,bc,de,hl,sp]{2}', linea) != None:
        if pasada1:
            cl += 1
        return hex(int(f'00{tablaPares[linea[8:10]]}1001', 2))[2:].upper().zfill(2)

#ADC HL, ss
    if re.fullmatch('[a,A][d,D][c,C] [h,H][l,L], [BC,DE,HL,SP,bc,de,hl,sp]{2}', linea) != None:
        if pasada1:
            cl += 2
        return hex(int(f'1110110101{tablaPares[linea[8:10]]}1010', 2))[2:].upper().zfill(4)

#SBC HL, ss
    if re.fullmatch('[s,S][b,B][c,C] [h,H][l,L], [BC,DE,HL,SP,bc,de,hl,sp]{2}', linea) != None:
        if pasada1:
            cl += 2
        return hex(int(f'1110110101{tablaPares[linea[8:10]]}0010', 2))[2:].upper().zfill(4)

#ADD IX, po
    if re.fullmatch('[a,A][d,D][d,D] [i,I][i,X], [BC,DE,IX,SP,bc,de,ix,sp]{2}', linea) != None:
        if pasada1:
            cl += 2
        return hex(int(f'1101110100{tablaPares[linea[8:10]]}1001', 2))[2:].upper().zfill(4)

#ADD IY, rr
    if re.fullmatch('[a,A][d,D][d,D] [i,I][i,X], [BC,DE,IY,SP,bc,de,iy,sp]{2}', linea) != None:
        if pasada1:
            cl += 2
        return hex(int(f'1111110100{tablaPares[linea[8:10]]}1001', 2))[2:].upper().zfill(4)

#INC ss
    if re.fullmatch('[i,I][n,N][c,C] [BC,DE,HL,SP,bc,de,hl,sp]{2}', linea) != None:
        if pasada1:
            cl += 1
        return hex(int(f'00{tablaPares[linea[4:6]]}0011', 2))[2:].upper().zfill(2)

#INC IX
    if re.fullmatch('[i,I][n,N][c,C] [i,I][x,X]', linea) != None:
        if pasada1:
            cl += 2
        return hex(int(f'1101110100100011', 2))[2:].upper().zfill(4)

#INC IY
    if re.fullmatch('[i,I][n,N][c,C] [i,I][y,Y]', linea) != None:
        if pasada1:
            cl += 2
        return hex(int(f'1111110100100011', 2))[2:].upper().zfill(4)

#DEC ss
    if re.fullmatch('[d,D][e,E][c,C] [BC,DE,HL,SP,bc,de,hl,sp]{2}', linea) != None:
        if pasada1:
            cl += 1
        return hex(int(f'00{tablaPares[linea[4:6]]}1011', 2))[2:].upper().zfill(2)

#DEC IX
    if re.fullmatch('[d,D][e,E][c,C] [i,I][x,X]', linea) != None:
        if pasada1:
            cl += 2
        return hex(int(f'1101110100101011', 2))[2:].upper().zfill(4)

#DEC IY
    if re.fullmatch('[d,D][e,E][c,C] [i,I][y,Y]', linea) != None:
        if pasada1:
            cl += 2
        return hex(int(f'1111110100101011', 2))[2:].upper().zfill(4)

#Tabla 7 la de rotaciones
  #RLCA
    if re.fullmatch(r'[R,r][L,l][c,C][A,a]', linea) != None:
        if pasada1:
            cl += 1
        return hex(int(f'00000111', 2))[2:].upper().zfill(2)
  #RLA
    if re.fullmatch(r'[R,r][L,l][A,a]', linea) != None:
        if pasada1:
            cl += 1
        return hex(int(f'00010111', 2))[2:].upper().zfill(2)
  #RRCA
    if re.fullmatch(r'[R,r]{2}[c,C][A,a]', linea) != None:
        if pasada1:
            cl += 1
        return hex(int(f'00001111', 2))[2:].upper().zfill(2)
  #RLRA
    if re.fullmatch(r'[R,r]{2}}[A,a]', linea) != None:
        if pasada1:
            cl += 1
        return hex(int(f'00011111', 2))[2:].upper().zfill(2)
  #RLC r
    if re.fullmatch(r'[R,r][L,l][c,C] [A,B,C,D,E,H,L,a,b,c,d,e,h,l]', linea) != None:
        if pasada1:
            cl += 2
        return hex(int(f'11001011 00000{tablaPares[linea[4].upper()]}', 2))[2:].upper().zfill(4)
  #RLC (HL)
    if re.fullmatch(r'[R,r][L,l][c,C] \([h,H][l,L]\)', linea) != None:
        if pasada1:
            cl += 2
        return hex(int(f'11001011 00000110', 2))[2:].upper().zfill(4)
  #RLC (IX+d)
    if re.fullmatch(r'[R,r][L,l][c,C] (IX[+,-][0-9]{1,3})', linea) != None: 
        if pasada1:
            cl += 4
        d = int(linea[10:-1])
        if linea[9] == '-':
            d = -d
        d_ = bin(abs(d))[2:].zfill(8)
        if d < 0: 
            d_ = d_.replace('0', '2').replace('1', '0').replace('2', '1') 
            d_ = bin(int(d_, 2) + 1)[2:].zfill(8) 
        return hex(int(f'11001011 11011101 00{d_}110', 2))[2:].upper().zfill(8)
    #RLC (IY+d)
    if re.fullmatch(r'[R,r][L,l][c,C] (IY[+,-][0-9]{1,3})', linea) != None:
        if pasada1:
            cl += 4
        d = int(linea[10:-1])
        if linea[9] == '-':
            d = -d
        d_ = bin(abs(d))[2:].zfill(8)
        if d < 0: 
            d_ = d_.replace('0', '2').replace('1', '0').replace('2', '1') 
            d_ = bin(int(d_, 2) + 1)[2:].zfill(8) 
        return hex(int(f'11111101 11001011 00{d_}110', 2))[2:].upper().zfill(8)

  #RL S
    if re.fullmatch(r'[R,r][L,l][c,C] [A,B,C,D,E,H,L,a,b,c,d,e,h,l]', linea) != None:
        if pasada1:
            cl += 2
        return hex(int(f'11001011 00010{tablaRegistros[linea[3].upper()]}', 2))[2:].upper().zfill(4)
  
  #RRC S
    if re.fullmatch(r'[R,r]{2}[c,C] [A,B,C,D,E,H,L,a,b,c,d,e,h,l]', linea) != None:
        if pasada1:
            cl += 2
        return hex(int(f'11001011 00001{tablaRegistros[linea[4].upper()]}', 2))[2:].upper().zfill(4)
  
  #RR S
    if re.fullmatch(r'[R,r]{2} [A,B,C,D,E,H,L,a,b,c,d,e,h,l]', linea) != None:
        if pasada1:
            cl += 2
        return hex(int(f'11001011 00011{tablaRegistros[linea[4].upper()]}', 2))[2:].upper().zfill(4)
  
  #SLA S
    if re.fullmatch(r'[S,s][L,l][A,a] [A,B,C,D,E,H,L,a,b,c,d,e,h,l]', linea) != None:
        if pasada1:
            cl += 2
        return hex(int(f'11001011 00100{tablaRegistros[linea[4].upper()]}', 2))[2:].upper().zfill(4)
  
  #SRA S
    if re.fullmatch(r'[S,s][R,r][A,a] [A,B,C,D,E,H,L,a,b,c,d,e,h,l]', linea) != None:
        if pasada1:
            cl += 2
        return hex(int(f'11001011 00101{tablaRegistros[linea[4].upper()]}', 2))[2:].upper().zfill(4)
  
  #SRL S
    if re.fullmatch(r'[R,r][L,l][c,C] [A,B,C,D,E,H,L,a,b,c,d,e,h,l]', linea) != None:
        if pasada1:
            cl += 2
        return hex(int(f'11001011 00111{tablaRegistros[linea[4].upper()]}', 2))[2:].upper().zfill(4)
    #RLD 
    if re.fullmatch(r'[R,r][L,l][D,d]', linea) != None:
        if pasada1:
            cl += 2
        return hex(int(f'11101101 01101111', 2))[2:].upper().zfill(4)
  
  #RRD 
    if re.fullmatch(r'[R,r]{2}}[D,d]', linea) != None:
        if pasada1:
            cl += 2
        return hex(int(f'11101101 01100111', 2))[2:].upper().zfill(4)
    
    # Tabla 8 - grupo BIT
  #BIT b,r
    if re.fullmatch(r'[b,B][I,i][T,t] [0-9], [A,B,C,D,E,H,L,a,b,c,d,e,h,l]', linea) != None:
        if pasada1:
            cl += 2
        return hex(int(f'01{tablaBits[linea[4].upper()]}{tablaRegistros[linea[5].upper()]}', 2))[2:].upper().zfill(4)

  #BIT b,(HL)
    if re.fullmatch(r'[b,B][I,i][T,t] [0-9], \([h,H][l,L]\)', linea) != None:
        if pasada1:
            cl += 2
        return hex(int(f'01{tablaBits[linea[4].upper()]}110', 2))[2:].upper().zfill(4)

  #BIT b, (IX+d)
    if re.fullmatch(r'[b,B][I,i][T,t] [0-9], (IX[+,-][0-9]{1,3})', linea) != None:
        d = int(linea[11:-1])
        if linea[10] == '-':
            d = -d
        d_ = bin(abs(d))[2:].zfill(8)
        if d < 0: 
            d_ = d_.replace('0', '2').replace('1', '0').replace('2', '1') 
            d_ = bin(int(d_, 2) + 1)[2:].zfill(8) 
        return hex(int(f'11011101 01{tablaBits[linea[4].upper()]}110', 2))[2:].upper().zfill(8)
  
  #BIT b, (IY+d) 
    if re.fullmatch(r'[b,B][I,i][T,t] [0-9], (IY[+,-][0-9]{1,3})', linea) != None:
        d = int(linea[11:-1])
        if linea[10] == '-':
            d = -d
        d_ = bin(abs(d))[2:].zfill(8)
        if d < 0: 
            d_ = d_.replace('0', '2').replace('1', '0').replace('2', '1') 
            d_ = bin(int(d_, 2) + 1)[2:].zfill(8) 
        return hex(int(f'11111101 01{tablaBits[linea[4].upper()]}110', 2))[2:].upper().zfill(8)

  #SET b, r
    if re.fullmatch(r'[s,S][E,e][T,t] [0-9], [A,B,C,D,E,H,L,a,b,c,d,e,h,l]', linea) != None:
        if pasada1:
            cl += 2
        return hex(int(f'11{tablaBits[linea[4].upper()]}{tablaRegistros[linea[7].upper()]}',2))[2:].upper().zfill(4)
  #SET b,(HL)
    if re.fullmatch(r'[s,S][E,e][T,t] [0-9], \([h,H][l,L]\)', linea) != None:
        if pasada1:
            cl += 2
        return hex(int(f'11{tablaBits[linea[4].upper()]}110', 2))[2:].upper().zfill(4)

  #SET b, (IX+d)
    if re.fullmatch(r'[s,S][E,e][T,t] [0-9], (IX[+,-][0-9]{1,3})', linea) != None:
        d = int(linea[11:-1])
        if linea[10] == '-':
            d = -d
        d_ = bin(abs(d))[2:].zfill(8)
        if d < 0: 
            d_ = d_.replace('0', '2').replace('1', '0').replace('2', '1') 
            d_ = bin(int(d_, 2) + 1)[2:].zfill(8) 
        return hex(int(f'11011101 11{tablaBits[linea[4].upper()]}110', 2))[2:].upper().zfill(8)
    #SET b, (IY+d)
    if re.fullmatch(r'[s,S][E,e][T,t] [0-9], (IY[+,-][0-9]{1,3})', linea) != None:
        d = int(linea[11:-1])
        if linea[10] == '-':
            d = -d
        d_ = bin(abs(d))[2:].zfill(8)
        if d < 0: 
            d_ = d_.replace('0', '2').replace('1', '0').replace('2', '1') 
            d_ = bin(int(d_, 2) + 1)[2:].zfill(8) 
        return hex(int(f'11111101 11{tablaBits[linea[4].upper()]}110', 2))[2:].upper().zfill(8)
    
      # Tabla 10 - Grupo CALL y RETURN
  #CALL nn
    if re.fullmatch(r'[c,C][a,A][l,L][l,L] -?[0-9]{1,3} -?[0-9]{1,3}', linea) != None:
        if pasada1:
            cl +=  3
        n1 = int(linea[5:6]) 
        n1_ = bin(abs(n))[2:].zfill(8)
        if n1 < 0: 
            n1_ = n_.replace('0', '2').replace('1', '0').replace('2', '1')
            n1_ = bin(int(n_, 2) + 1)[2:].zfill(8)
        n2 = int(linea[7:]) 
        n2_ = bin(abs(n))[2:].zfill(8)
        if n2 < 0: 
            n2_ = n_.replace('0', '2').replace('1', '0').replace('2', '1')
            n2_ = bin(int(n_, 2) + 1)[2:].zfill(8)
        return hex(int(f'11001101{n1_}{n2_}', 2))[2:].upper()

  #CALL cc, nn
    """if re.fullmatch(r'[c,C][a,A][l,L][l,C] [nz,NZ,z,Z,nc,NC,c,C,po,PO,pe,PE,p,P,m,M], -?[0-9]{1,3} -?[0-9]{1,3})') != None:
        if pasada1:
            cl +=  3
        n1 = int(linea[5:6]) 
        n1_ = bin(abs(n))[2:].zfill(8)
        if n1 < 0: 
            n1_ = n_.replace('0', '2').replace('1', '0').replace('2', '1')
            n1_ = bin(int(n_, 2) + 1)[2:].zfill(8)
            n2 = int(linea[7:]) 
            n2_ = bin(abs(n))[2:].zfill(8)
        if n2 < 0: 
            n2_ = n_.replace('0', '2').replace('1', '0').replace('2', '1')
            n2_ = bin(int(n_, 2) + 1)[2:].zfill(8)
        return hex(int(f'11001101{n1_}{n2_}', 2))[2:].upper()
    """
    # Tabla 9 - Grupo de saltos
    #JP nn
    if re.fullmatch(r'[j,J][p,P] [0-9a-zA-Z]{1,}',linea) != None:
        if pasada1:
            cl += 3
        etiqueta = linea[3:]
        dir = buscarEtiqueta(etiqueta)
        if dir == None:
            return ''
        dir = dir[2:]+dir[:2] 
        return f"{hex(int(f'11000011', 2))[2:]}{dir}".upper().zfill(6)
    # jp cc, nn
    if re.fullmatch(r'[j,J][p,P] [nz,NZ,z,Z,nc,NC,c,C,po,PO,pe,PE,p,P,m,M], [0-9a-zA-Z]{1,}',linea) != None:
        if pasada1:
            cl += 3
        cond = linea[3:linea.find(',')]
        etiqueta = linea[linea.find(',')+2:]
        dir = buscarEtiqueta(etiqueta)
        if dir == None:
            return ''
        dir = dir[2:]+dir[:2]
        return f"{hex(int(f'11{tablaCondiciones[cond]}010', 2))[2:]}{dir}".upper().zfill(6)
    # JP (HL)
    if re.fullmatch(r'[j,J][p,P] \([h,H][l,L]\)',linea) != None:
        if pasada1:
            cl += 1
        return hex(int(f'11101001', 2))[2:].upper().zfill(2)
    # JP (IX)
    if re.fullmatch(r'[j,J][p,P] \([i,I][x,X]\)',linea) != None:
        if pasada1:
            cl += 2
        return hex(int(f'1101110111101001', 2))[2:].upper().zfill(4)
    # JP (IY)
    if re.fullmatch(r'[j,J][p,P] \([i,I][y,Y]\)',linea) != None:
        if pasada1:
            cl += 2
        return hex(int(f'1111110111101001', 2))[2:].upper().zfill(4)
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
        hex(cl)[2:].zfill(4).upper()
        validarMnemonico(linea[0])
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
                pass
                #linea[2] = re.sub(simbolo, buscarEtiqueta(simbolo), linea[2])
            linea[1] = validarMnemonico(linea[2], False)
        nuevaTraduccion.append(linea)
    traduccion = nuevaTraduccion.copy()

def agregarTS():
    global traduccion
    traduccion.append('TABLA DE SIMBOLOS')
    for simbolo, dir in tablaSimbolos.items():
        traduccion.append(f'{dir} {simbolo}')

def ensamblar(codigo):
    try:
        macroEnsamble(codigo)
        pasada1()
        pasada2()
        agregarTS()
        crearLST('programa')
    except Exception as e: 
        return e
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