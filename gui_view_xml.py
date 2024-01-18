from PySide6 import QtCore, QtGui, QtWidgets
from mod_functions import PATH_ICON

class View_Xml(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(611, 470)
        Form.setFixedSize(611, 470)
        icon = QtGui.QIcon.fromTheme(PATH_ICON)
        Form.setWindowIcon(icon)
        Form.setStyleSheet("QWidget#Form{\n"
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
"}\n"
"\n"
"QProgressBar{\n"
"	color: rgb(0, 0, 0);\n"
"}")
        self.layoutWidget = QtWidgets.QWidget(Form)
        self.layoutWidget.setGeometry(QtCore.QRect(25, 90, 561, 26))
        self.layoutWidget.setObjectName("layoutWidget")
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout(self.layoutWidget)
        self.horizontalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.lb_caminho = QtWidgets.QLabel(self.layoutWidget)
        self.lb_caminho.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.lb_caminho.setObjectName("lb_caminho")
        self.horizontalLayout_5.addWidget(self.lb_caminho)
        spacerItem = QtWidgets.QSpacerItem(10, 10, QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_5.addItem(spacerItem)
        self.txt_caminho = QtWidgets.QLineEdit(self.layoutWidget)
        self.txt_caminho.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.txt_caminho.setText("")
        self.txt_caminho.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.txt_caminho.setObjectName("txt_caminho")
        self.horizontalLayout_5.addWidget(self.txt_caminho)
        spacerItem1 = QtWidgets.QSpacerItem(10, 10, QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_5.addItem(spacerItem1)
        self.bt_buscar = QtWidgets.QPushButton(self.layoutWidget)
        self.bt_buscar.setMinimumSize(QtCore.QSize(100, 0))
        self.bt_buscar.setObjectName("bt_buscar")
        self.horizontalLayout_5.addWidget(self.bt_buscar)
        self.lb_novo_retalho = QtWidgets.QLabel(Form)
        self.lb_novo_retalho.setGeometry(QtCore.QRect(160, 16, 281, 41))
        font = QtGui.QFont()
        font.setPointSize(22)
        self.lb_novo_retalho.setFont(font)
        self.lb_novo_retalho.setAlignment(QtCore.Qt.AlignCenter)
        self.lb_novo_retalho.setObjectName("lb_novo_retalho")
        self.bt_lancar_retalhos = QtWidgets.QPushButton(Form)
        self.bt_lancar_retalhos.setEnabled(False)
        self.bt_lancar_retalhos.setGeometry(QtCore.QRect(320, 430, 121, 21))
        self.bt_lancar_retalhos.setMinimumSize(QtCore.QSize(100, 0))
        self.bt_lancar_retalhos.setObjectName("bt_lancar_retalhos")
        self.bt_exibir_retalhos = QtWidgets.QPushButton(Form)
        self.bt_exibir_retalhos.setGeometry(QtCore.QRect(170, 430, 121, 21))
        self.bt_exibir_retalhos.setMinimumSize(QtCore.QSize(100, 0))
        self.bt_exibir_retalhos.setObjectName("bt_exibir_retalhos")
        self.lb_sobra = QtWidgets.QLabel(Form)
        self.lb_sobra.setGeometry(QtCore.QRect(437, 60, 71, 20))
        self.lb_sobra.setObjectName("lb_sobra")
        self.txt_sobra = QtWidgets.QLineEdit(Form)
        self.txt_sobra.setGeometry(QtCore.QRect(513, 59, 71, 22))
        self.txt_sobra.setAlignment(QtCore.Qt.AlignCenter)
        self.txt_sobra.setObjectName("txt_sobra")
        self.tableWidget = QtWidgets.QTableWidget(Form)
        self.tableWidget.setGeometry(QtCore.QRect(20, 130, 571, 281))
        self.tableWidget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.tableWidget.setColumnCount(7)
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(2, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(3, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(4, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(5, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(6, item)
        self.tableWidget.verticalHeader().setVisible(True)
        self.progressBar = QtWidgets.QProgressBar(Form)
        self.progressBar.setGeometry(QtCore.QRect(180, 255, 251, 23))
        self.progressBar.setProperty("value", 0)
        self.progressBar.setAlignment(QtCore.Qt.AlignCenter)
        self.progressBar.setTextVisible(True)
        self.progressBar.setObjectName("progressBar")
        self.progressBar.setVisible(False)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)
        self.create_functions()

    def create_functions(self):
        pass

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Leitor XML"))
        self.lb_caminho.setText(_translate("Form", "Caminho XML"))
        self.bt_buscar.setText(_translate("Form", "Buscar"))
        self.lb_novo_retalho.setText(_translate("Form", "RETALHOS XML"))
        self.bt_lancar_retalhos.setText(_translate("Form", "Lançar Retalhos"))
        self.bt_exibir_retalhos.setText(_translate("Form", "Visualizar XML"))
        self.lb_sobra.setText(_translate("Form", "Reservado p/"))
        item = self.tableWidget.horizontalHeaderItem(0)
        item.setText(_translate("Form", "+"))
        item = self.tableWidget.horizontalHeaderItem(1)
        item.setText(_translate("Form", "Cod"))
        item = self.tableWidget.horizontalHeaderItem(2)
        item.setText(_translate("Form", "MM"))
        item = self.tableWidget.horizontalHeaderItem(3)
        item.setText(_translate("Form", "Descrição"))
        item = self.tableWidget.horizontalHeaderItem(4)
        item.setText(_translate("Form", "Largura"))
        item = self.tableWidget.horizontalHeaderItem(5)
        item.setText(_translate("Form", "x"))
        item = self.tableWidget.horizontalHeaderItem(6)
        item.setText(_translate("Form", "Altura"))
        self.progressBar.setFormat(_translate("Form", "Carregando... %p%"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Form = QtWidgets.QWidget()
    ui = View_Xml()
    ui.setupUi(Form)
    Form.show()
    sys.exit(app.exec())
