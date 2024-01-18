from PySide6 import QtCore, QtGui, QtWidgets
from mod_functions import PATH_ICON


class Ui_RemoveReserva(object):
    def setupUi(self, RemoveReserva):
        RemoveReserva.setObjectName("RemoveReserva")
        RemoveReserva.resize(891, 545)
        RemoveReserva.setFixedSize(891, 545)
        icon = QtGui.QIcon.fromTheme(PATH_ICON)
        RemoveReserva.setWindowIcon(icon)
        RemoveReserva.setStyleSheet("QWidget#RemoveReserva{\n"
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
        self.txt_num_proj = QtWidgets.QLineEdit(RemoveReserva)
        self.txt_num_proj.setGeometry(QtCore.QRect(460, 90, 91, 22))
        self.txt_num_proj.setAlignment(QtCore.Qt.AlignCenter)
        self.txt_num_proj.setObjectName("txt_num_proj")
        self.lb_num_proj = QtWidgets.QLabel(RemoveReserva)
        self.lb_num_proj.setGeometry(QtCore.QRect(337, 89, 111, 20))
        self.lb_num_proj.setObjectName("lb_num_proj")
        self.tableWidget = QtWidgets.QTableWidget(RemoveReserva)
        self.tableWidget.setGeometry(QtCore.QRect(20, 130, 851, 361))
        self.tableWidget.setAutoFillBackground(False)
        self.tableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tableWidget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.tableWidget.setObjectName("tableWidget")
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
        self.lb_remove_reserva = QtWidgets.QLabel(RemoveReserva)
        self.lb_remove_reserva.setGeometry(QtCore.QRect(276, 30, 341, 41))
        font = QtGui.QFont()
        font.setPointSize(22)
        self.lb_remove_reserva.setFont(font)
        self.lb_remove_reserva.setAlignment(QtCore.Qt.AlignCenter)
        self.lb_remove_reserva.setObjectName("lb_remove_reserva")
        self.bt_remove_reservar = QtWidgets.QPushButton(RemoveReserva)
        self.bt_remove_reservar.setGeometry(QtCore.QRect(390, 507, 111, 24))
        self.bt_remove_reservar.setObjectName("bt_remove_reservar")
        self.bt_remove_reservar.setEnabled(False)
        self.retranslateUi(RemoveReserva)
        QtCore.QMetaObject.connectSlotsByName(RemoveReserva)
        self.create_functions()

    def create_functions(self):
        ...

    def retranslateUi(self, RemoveReserva):
        _translate = QtCore.QCoreApplication.translate
        RemoveReserva.setWindowTitle(_translate("RemoveReserva", "Remover Reservas"))
        self.lb_num_proj.setText(_translate("RemoveReserva", "Numero do Projeto:"))
        item = self.tableWidget.horizontalHeaderItem(0)
        item.setText(_translate("RemoveReserva", "+"))
        item = self.tableWidget.horizontalHeaderItem(1)
        item.setText(_translate("RemoveReserva", "id"))
        item = self.tableWidget.horizontalHeaderItem(2)
        item.setText(_translate("RemoveReserva", "Setor"))
        item = self.tableWidget.horizontalHeaderItem(3)
        item.setText(_translate("RemoveReserva", "Cod"))
        item = self.tableWidget.horizontalHeaderItem(4)
        item.setText(_translate("RemoveReserva", "MM"))
        item = self.tableWidget.horizontalHeaderItem(5)
        item.setText(_translate("RemoveReserva", "Descrição"))
        item = self.tableWidget.horizontalHeaderItem(6)
        item.setText(_translate("RemoveReserva", "Largura"))
        item = self.tableWidget.horizontalHeaderItem(7)
        item.setText(_translate("RemoveReserva", "x"))
        item = self.tableWidget.horizontalHeaderItem(8)
        item.setText(_translate("RemoveReserva", "Altura"))
        item = self.tableWidget.horizontalHeaderItem(9)
        item.setText(_translate("RemoveReserva", "Responsavel"))
        self.lb_remove_reserva.setText(_translate("RemoveReserva", "REMOVER RESERVA"))
        self.bt_remove_reservar.setText(_translate("RemoveReserva", "Remover"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    RemoveReserva = QtWidgets.QWidget()
    ui = Ui_RemoveReserva()
    ui.setupUi(RemoveReserva)
    RemoveReserva.show()
    sys.exit(app.exec())
