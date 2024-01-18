from PySide6 import QtCore, QtGui, QtWidgets
from mod_functions import PATH_ICON


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(891, 545)
        Form.setFixedSize(891, 545)
        icon = QtGui.QIcon.fromTheme(PATH_ICON)
        Form.setWindowIcon(icon)
        Form.setStyleSheet("QWidget#Form{\n"
                           "    background-color: rgb(68, 114, 196);\n"
                           "}\n"
                           "\n"
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
                           "QFrame#QTableWidget{\n"
                           "    background: rgb(255, 255, 255);\n"
                           "}")
        self.txt_num_proj = QtWidgets.QLineEdit(parent=Form)
        self.txt_num_proj.setGeometry(QtCore.QRect(453, 90, 91, 22))
        self.txt_num_proj.setObjectName("txt_num_proj")
        self.txt_num_proj.setAlignment(QtCore.Qt.AlignCenter)
        self.lb_num_proj = QtWidgets.QLabel(parent=Form)
        self.lb_num_proj.setGeometry(QtCore.QRect(330, 89, 111, 20))
        self.lb_num_proj.setObjectName("lb_num_proj")
        self.tableWidget = QtWidgets.QTableWidget(parent=Form)
        self.tableWidget.setGeometry(QtCore.QRect(20, 130, 851, 361))
        self.tableWidget.setAutoFillBackground(False)
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.tableWidget.setColumnCount(10)
        self.tableWidget.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        item.setBackground(QtGui.QColor(194, 194, 194))
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
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(7, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(8, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(9, item)
        self.tableWidget.setColumnWidth(0, 15)
        self.tableWidget.setColumnWidth(1, 50)
        self.tableWidget.setColumnWidth(2, 50)
        self.tableWidget.setColumnWidth(3, 60)
        self.tableWidget.setColumnWidth(4, 55)
        self.tableWidget.setColumnWidth(5, 272)
        self.tableWidget.setColumnWidth(6, 70)
        self.tableWidget.setColumnWidth(7, 10)
        self.tableWidget.setColumnWidth(8, 70)
        self.tableWidget.setColumnWidth(9, 100)
        self.lb_principal = QtWidgets.QLabel(parent=Form)
        self.lb_principal.setGeometry(QtCore.QRect(273, 30, 341, 41))
        font = QtGui.QFont()
        font.setPointSize(22)
        self.lb_principal.setFont(font)
        self.lb_principal.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.lb_principal.setObjectName("lb_principal")
        self.bt_buscar_retalhos = QtWidgets.QPushButton(parent=Form)
        self.bt_buscar_retalhos.setGeometry(QtCore.QRect(319, 507, 111, 24))
        self.bt_buscar_retalhos.setObjectName("bt_buscar_retalhos")
        self.bt_reservar_retalhos = QtWidgets.QPushButton(parent=Form)
        self.bt_reservar_retalhos.setGeometry(QtCore.QRect(459, 507, 111, 24))
        self.bt_reservar_retalhos.setObjectName("bt_reservar_retalhos")
        self.progressBar = QtWidgets.QProgressBar(parent=Form)
        self.progressBar.setGeometry(QtCore.QRect(295, 299, 301, 23))
        self.progressBar.setProperty("value", 0)
        self.progressBar.setTextVisible(False)
        self.progressBar.setObjectName("progressBar")
        self.progressBar.setVisible(False)
        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Reservas"))
        self.lb_num_proj.setText(_translate("Form", "Numero do Projeto:"))
        item = self.tableWidget.horizontalHeaderItem(0)
        item.setText(_translate("Form", "+"))
        item = self.tableWidget.horizontalHeaderItem(1)
        item.setText(_translate("Form", "id"))
        item = self.tableWidget.horizontalHeaderItem(2)
        item.setText(_translate("Form", "Setor"))
        item = self.tableWidget.horizontalHeaderItem(3)
        item.setText(_translate("Form", "Cod"))
        item = self.tableWidget.horizontalHeaderItem(4)
        item.setText(_translate("Form", "MM"))
        item = self.tableWidget.horizontalHeaderItem(5)
        item.setText(_translate("Form", "Descrição"))
        item = self.tableWidget.horizontalHeaderItem(6)
        item.setText(_translate("Form", "Largura"))
        item = self.tableWidget.horizontalHeaderItem(7)
        item.setText(_translate("Form", "x"))
        item = self.tableWidget.horizontalHeaderItem(8)
        item.setText(_translate("Form", "Altura"))
        item = self.tableWidget.horizontalHeaderItem(9)
        item.setText(_translate("Form", "Reserva"))
        self.lb_principal.setText(_translate("Form", "RESERVA POR PROJETO"))
        self.bt_buscar_retalhos.setText(_translate("Form", "Buscar Retalhos"))
        self.bt_reservar_retalhos.setText(
            _translate("Form", "Reservar Retalhos"))
        self.create_functions()

    def create_functions(self):
        ...


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Form = QtWidgets.QWidget()
    ui = Ui_Form()
    ui.setupUi(Form)
    Form.show()
    sys.exit(app.exec())
