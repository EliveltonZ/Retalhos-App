from PySide6 import QtCore, QtGui, QtWidgets
from mod_functions import PATH_ICON

class Ui_Config(object):
    def setupUi(self, Config):
        Config.setObjectName("Config")
        Config.resize(526, 298)
        Config.setFixedSize(526, 298)
        icon = QtGui.QIcon.fromTheme(PATH_ICON)
        Config.setWindowIcon(icon)
        Config.setStyleSheet("QWidget{\n"
"    background-color: rgb(68, 114, 196);\n"
"}\n"
"QLabel{\n"
"    color: rgb(255, 255, 255);\n"
"    background-color: rgba(0, 0, 0, 0);\n"
"}\n"
"\n"
"QPushButton{\n"
"    border-radius: 5px;\n"
"    background-color: rgb(255, 170, 0);\n"
"}\n"
"\n"
"QPushButton:hover{\n"
"    border-radius: 5px;\n"
"    background-color: rgba(255, 170, 0, 150);\n"
"}\n"
"\n"
"QLineEdit{\n"
"    border-radius: 5px;\n"
"    background-color: rgba(255, 170, 0, 50);\n"
"    color: rgb(255, 255, 255)\n"
"}\n"
"\n"
"QLineEdit:focus{\n"
"    border-radius: 5px;\n"
"    background-color: rgba(255, 170, 0, 50);\n"
"    color: rgb(255, 255, 255);\n"
"    border: 1px solid rgb(255, 255, 255)\n"
"}")
        self.txt_corte_certo = QtWidgets.QLineEdit(Config)
        self.txt_corte_certo.setGeometry(QtCore.QRect(16, 90, 491, 22))
        self.txt_corte_certo.setCursorPosition(0)
        self.txt_corte_certo.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.txt_corte_certo.setObjectName("txt_corte_certo")
        self.txt_maquina = QtWidgets.QLineEdit(Config)
        self.txt_maquina.setGeometry(QtCore.QRect(16, 160, 131, 22))
        self.txt_maquina.setCursorPosition(0)
        self.txt_maquina.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.txt_maquina.setObjectName("txt_maquina")
        self.txt_maquina.setAlignment(QtCore.Qt.AlignCenter)
        self.lb_configuration = QtWidgets.QLabel(Config)
        self.lb_configuration.setGeometry(QtCore.QRect(161, 20, 201, 41))
        font = QtGui.QFont()
        font.setPointSize(22)
        self.lb_configuration.setFont(font)
        self.lb_configuration.setAlignment(QtCore.Qt.AlignCenter)
        self.lb_configuration.setObjectName("lb_configuration")
        self.lb_path = QtWidgets.QLabel(Config)
        self.lb_path.setGeometry(QtCore.QRect(20, 59, 120, 31))
        self.lb_path.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.lb_path.setObjectName("lb_path")
        self.txt_data_base = QtWidgets.QLineEdit(Config)
        self.txt_data_base.setGeometry(QtCore.QRect(166, 160, 341, 22))
        self.txt_data_base.setCursorPosition(0)
        self.txt_data_base.setAlignment(QtCore.Qt.AlignCenter)
        self.txt_data_base.setObjectName("txt_data_base")
        self.bt_search_path_3 = QtWidgets.QPushButton(Config)
        self.bt_search_path_3.setGeometry(QtCore.QRect(206, 250, 111, 31))
        self.bt_search_path_3.setObjectName("bt_search_path_3")
        self.lb_machine = QtWidgets.QLabel(Config)
        self.lb_machine.setGeometry(QtCore.QRect(20, 121, 131, 31))
        self.lb_machine.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.lb_machine.setObjectName("lb_machine")
        self.lb_path_db = QtWidgets.QLabel(Config)
        self.lb_path_db.setGeometry(QtCore.QRect(170, 119, 151, 31))
        self.lb_path_db.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.lb_path_db.setObjectName("lb_path_db")
        self.lb_testing_cc = QtWidgets.QLabel(Config)
        self.lb_testing_cc.setGeometry(QtCore.QRect(50, 210, 71, 16))
        self.lb_testing_cc.setObjectName("lb_testing_cc")
        self.lb_testing_db = QtWidgets.QLabel(Config)
        self.lb_testing_db.setGeometry(QtCore.QRect(280, 210, 71, 16))
        self.lb_testing_db.setObjectName("lb_testing_db")
        self.lb_testing_cc_2 = QtWidgets.QLabel(Config)
        self.lb_testing_cc_2.setGeometry(QtCore.QRect(120, 210, 91, 16))
        self.lb_testing_cc_2.setObjectName("lb_testing_cc_2")
        self.lb_testing_db_2 = QtWidgets.QLabel(Config)
        self.lb_testing_db_2.setGeometry(QtCore.QRect(350, 210, 91, 16))
        self.lb_testing_db_2.setObjectName("lb_testing_db_2")
        self.retranslateUi(Config)
        QtCore.QMetaObject.connectSlotsByName(Config)
        self.create_functions()

    def create_functions(self):
        ...
    
    def retranslateUi(self, Config):
        _translate = QtCore.QCoreApplication.translate
        Config.setWindowTitle(_translate("Config", "Configurações"))
        self.lb_configuration.setText(_translate("Config", "Configurações"))
        self.lb_path.setText(_translate("Config", "Caminho Corte Certo:"))
        self.bt_search_path_3.setText(_translate("Config", "Salvar"))
        self.lb_machine.setText(_translate("Config", "Maquina/Responsavel:"))
        self.lb_path_db.setText(_translate("Config", "Caminho Banco de Dados:"))
        self.lb_testing_cc.setText(_translate("Config", "Testing CC:"))
        self.lb_testing_db.setText(_translate("Config", "Testing BD:"))
        self.txt_corte_certo.setText(_translate("Config", ""))
        self.txt_data_base.setText(_translate("Config", ""))
        self.txt_maquina.setText(_translate("Config", ""))
        self.lb_testing_cc_2.setText(_translate("Config", "..."))
        self.lb_testing_db_2.setText(_translate("Config", "..."))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Config = QtWidgets.QWidget()
    ui = Ui_Config()
    ui.setupUi(Config)
    Config.show()
    sys.exit(app.exec())
