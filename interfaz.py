#Librerias a utilizar con el interfaz grafico PyQt5--------------------------------------------

import sys
from PyQt5.QtWidgets import QApplication, QLabel, QPushButton, QWidget, QStackedLayout, QGridLayout, QVBoxLayout, QPlainTextEdit, QHBoxLayout
from PyQt5.QtGui import QPixmap, QCursor
from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QDesktopServices
from logica import ensamblar

# Botones que serán utilizados en el menú del compilador------------------------------------------------------------
widgets = {
    "Regresar menu principal": [],
    "Iniciar": [],
    "DIE": [],
}

class pagina2(QWidget):
    def __init__(self, parent):
        super(pagina2, self).__init__()

        # DIE widget________________________________________________________________
        imagen_DIE = QPixmap("DIE.png").scaled(500, 500, QtCore.Qt.KeepAspectRatio)
        DIE = QLabel()
        DIE.setPixmap(imagen_DIE)
        DIE.setAlignment(QtCore.Qt.AlignCenter)
        DIE.setStyleSheet("margin-top: 75px; margin-bottom: 30px;")
        widgets["DIE"].append(DIE)

        # Imagen "Unam"_____________________________________________________________
        image_unam = QPixmap("Unam.png").scaled(300, 200, QtCore.Qt.KeepAspectRatio)
        unam_eti = QLabel()
        unam_eti.setPixmap(image_unam)
        unam_eti.setAlignment(QtCore.Qt.AlignCenter)

        # Botones del código 2_______________________________________________
        boton1 = self.BotonesA('Manual de Usuario', 0, 0, self.B_manual)
        boton2 = self.BotonesA('Programa', 0, 0, self.Ventana_programa)
        boton3 = self.BotonesA('Créditos', 0, 0, self.Ventana_creditos)

        # Coloca los widgets en el diseño
        layout = QVBoxLayout()
        layout.addWidget(widgets["DIE"][-1])
        layout.addWidget(unam_eti)
        layout.addWidget(boton1)
        layout.addWidget(boton2)
        layout.addWidget(boton3)

        self.setLayout(layout)

        parent.setLayout(QGridLayout())
        parent.layout().addWidget(self, 0, 0, 1, 2)

    def BotonesA(self, answer, l_margin, r_margin, callback):
        '''Crea botones idénticos con márgenes izquierdo y derecho personalizados'''
        boton = QPushButton(answer)
        boton.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
        boton.setFixedWidth(200)
        boton.setStyleSheet(
            "*{"
            "background: #6445B0;"  # Cambia el color de fondo del botón (color predeterminado)
            "color: white;"
            "font-family: 'shanti';"
            "font-size: 14px;"
            "border: 4px solid '#8B00FF';"  # Cambia el color del marco a #8B00FF-------------------
            "border-radius: 25px;"
            "padding: 15px 0;"
            "margin-top: 20px;"
            "}"
            "*:hover{"
            "background: '#8B00FF';" #Fondo al mantener el cursor en el boton
            "}"
        )
        boton.clicked.connect(callback)
        return boton

       #ACCION A RREALIZAR al presionar boton "MANUAL"_______________________________________________________________________
    def B_manual(self):
        pdf_file_path = 'prueba1.pdf'  # La ruta del PDF ***********
        QDesktopServices.openUrl(QUrl.fromLocalFile(pdf_file_path))

    def Ventana_programa(self):
        main_menu.Mostar_pag_Programa()

    def Ventana_creditos(self):
        main_menu.Mostar_pag_Creditos()
#______________________________________________________________________________________________________________________________
       #ACCION A RREALIZAR al presionar boton "Creditos"_______________________________________________________________________
class Pagina_Creditos(QWidget):
    def __init__(self):
        super(Pagina_Creditos, self).__init__()

        self.setWindowTitle("Créditos del Proyecto")
        self.setGeometry(100, 100, 800, 600)

        self.layout = QVBoxLayout()
         
        #Nombres de los miembros y tutor
        self.members = [
            {"name": "Romero Pizano Christian Gustavo", "nombre": "Christian.png", "escala": 2.0},
            {"name": "Zarco Romero José Alberto", "nombre": "Zarco.png", "escala": 1.0},
            {"name": "Ing. Alberto Templos Carbajal", "nombre": "profesor.png", "escala": 2.0},
            {"name": "Guillermo Hernández Ruiz de Esparza", "nombre": "Guillermo.png", "escala": 1.0},
            {"name": "Ugalde Santos Atzin", "nombre": "atzin.png", "escala": 1.0},
        ]

        for informacion in self.members:
            self.agregar_miembro(informacion)

        self.setLayout(self.layout)

    def agregar_miembro(self, informacion):
        name_label = QLabel(informacion["name"])
        eti_nombre = QLabel()

        # Obtén la ruta completa del archivo PNG en el mismo directorio que el script
        photo_path = informacion["nombre"]
        escala = QPixmap(photo_path).scaledToWidth(int(100 * informacion["escala"]))
        eti_nombre.setPixmap(escala)

        # Aumenta el tamaño de la letra
        font = eti_nombre.font()
        font.setPointSize(20)  # Ajusta el tamaño de la letra según tus necesidades
        eti_nombre.setFont(font)

        # Color del texto
        name_label.setStyleSheet("color: white;")

        self.layout.addWidget(name_label, alignment=Qt.AlignCenter)
        self.layout.addWidget(eti_nombre, alignment=Qt.AlignCenter)

    def set_escala(self, member_index, escala):
        if 0 <= member_index < len(self.members):
            self.members[member_index]["escala"] = escala
            self.clear_layout()
            for informacion in self.members:
                self.agregar_miembro(informacion)

    def clear_layout(self):
        while self.layout.count():
            item = self.layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        main_menu.Mostar_pag_Creditos()
        

#ACCION A RREALIZAR al presionar boton "Programa"_______________________________________________________________________        
class ensamblador(QWidget):
    def __init__(self):
        super().__init__()
        
        #Apartado grrafico de "PROGRAMA"-------------------------------------------------------
 
        # Configuración de la ventana
        self.setWindowTitle('Ensamblador App')
        self.setGeometry(100, 100, 800, 600)

        # Crear un diseño vertical
        layout = QVBoxLayout()

        # Área de código
        self.code_editor = QPlainTextEdit()
        self.code_editor.setStyleSheet("background-color: #2F3946  ; color: #FFFFFF   ;")
        layout.addWidget(self.code_editor)

        # Botón para ensamblar
        assemble_button = QPushButton("Ensamblar")
        assemble_button.clicked.connect(self.assemble_code)
        layout.addWidget(assemble_button)

        # Etiqueta para mostrar resultados o mensajes
        self.result_label = QLabel("Resultados:")
        layout.addWidget(self.result_label)

        # Establecer el diseño en la ventana
        self.setLayout(layout)
      
      #--------------------------------------------------------------------------------------------
      
      
      #AQUI VIENE EL APARTADO DE LA LOGICA Y PROGRAMACION DEL ENSAMBLADOR________________________________________________________________________________________________________________________________________
      
      
    
      
      
      
    # Método para procesar y ensamblar el código ingresado
    def assemble_code(self):
        code = self.code_editor.toPlainText()
        
        
        
        success = ensamblar(code)  # La lógica que van a implementar en el ensamblado iría aquí





        if success:
            self.result_label.setText("Ensamblado exitoso")
            self.setStyleSheet("background-color: #379974 ;")  # Color azul fuerte
        else:
            self.result_label.setText("Error de ensamblado")
            self.setStyleSheet("background-color: #800000;")  # Color rojo






#__________________________________________________________________________________________________________________________________________________________________________________________________________________




class MainMenu(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Proyecto')
        self.setFixedSize(1200, 1000)
        self.move(400, 100)
        self.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #004DFF, stop:1 #29D2F0);")

        self.stacked_layout = QStackedLayout()

        self.crear_menu()
        self.crear_pagina2()
        self.crear_pagina_creditos()
        self.crear_pagina_programa()

        self.setLayout(self.stacked_layout)

    def crear_menu(self):
        main_menu_widget = QWidget()
        layout = QGridLayout()

        # DIE widget
        imagen_DIE = QPixmap("DIE.png").scaled(1000, 500, QtCore.Qt.KeepAspectRatio)
        DIE = QLabel()
        DIE.setPixmap(imagen_DIE)
        DIE.setAlignment(QtCore.Qt.AlignCenter)
        DIE.setStyleSheet("margin-top: 30px;")
        widgets["DIE"].append(DIE)

        # Botón widget
        boton = self.BotonesA("Iniciar", 200, 200, self.ventana_2)
        widgets["Iniciar"].append(boton)

        # Coloca los widgets globales en la cuadrícula
        layout.addWidget(widgets["DIE"][-1], 0, 0, 1, 2)
        layout.addWidget(widgets["Iniciar"][-1], 1, 0, 1, 2)

        main_menu_widget.setLayout(layout)
        self.stacked_layout.addWidget(main_menu_widget)

    def crear_pagina2(self):
        pagina2_widget = QWidget()
        self.pagina2 = pagina2(pagina2_widget)
        self.stacked_layout.addWidget(pagina2_widget)

    def crear_pagina_creditos(self):
        credits_widget = Pagina_Creditos()
        Boton_Regresar = self.BotonesA('Regresar al Menú', 0, 0, self.show_main_menu)
        credits_widget.layout.addWidget(Boton_Regresar, alignment=Qt.AlignCenter)
        self.stacked_layout.addWidget(credits_widget)

    def crear_pagina_programa(self):
        programa_widget = ensamblador()
        Boton_Regresar = self.BotonesA('Regresar al Menú', 0, 0, self.show_main_menu)
        programa_widget.layout().addWidget(Boton_Regresar, alignment=Qt.AlignCenter)
        self.stacked_layout.addWidget(programa_widget)

    def BotonesA(self, answer, l_margin, r_margin, callback):
        '''Crea botones idénticos con márgenes izquierdo y derecho personalizados'''
        boton = QPushButton(answer)
        boton.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
        boton.setFixedWidth(200)
        boton.setStyleSheet(
            "*{"
            "background: #6445B0;"  # Cambia el color de fondo del botón (color predeterminado)
            "color: white;"
            "font-family: 'shanti';"
            "font-size: 14px;"
            "border: 4px solid '#8B00FF';"  # Cambia el color del marco a #8B00FF
            "border-radius: 25px;"
            "padding: 15px 0;"
            "margin-top: 20px;"
            "}"
            "*:hover{"
            "background: '#8B00FF';"
            "}"
        )
        boton.clicked.connect(callback)
        return boton

    def show_main_menu(self):
        self.stacked_layout.setCurrentIndex(0)

    def ventana_2(self):
        self.stacked_layout.setCurrentIndex(1)

    def Mostar_pag_Creditos(self):
        self.stacked_layout.setCurrentIndex(2)

    def Mostar_pag_Programa(self):
        self.stacked_layout.setCurrentIndex(3)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_menu = MainMenu()
    main_menu.show()
    sys.exit(app.exec_())
