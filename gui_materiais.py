from PySide6 import QtCore, QtGui, QtWidgets
from mod_functions import PATH_ICON


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(539, 392)
        Form.setFixedSize(539, 392)
        icon = QtGui.QIcon.fromTheme(PATH_ICON)
        Form.setWindowIcon(icon)
        Form.setStyleSheet("QWidget#Form{\n"
"background-color: rgb(68, 114, 196);\n"
"}\n"
"QLabel{\n"
"    color: rgb(255, 255, 255);\n"
"}\n"
"QLineEdit{\n"
"    border-radius: 5px;\n"
"    background-color: rgba(255, 170, 0, 50);\n"
"    color: rgb(255, 255, 255)\n"
"}\n"
"QLineEdit:focus{\n"
"    border-radius: 5px;\n"
"    background-color: rgba(255, 170, 0, 50);\n"
"    color: rgb(255, 255, 255);\n"
"    border: 1px solid rgb(255, 255, 255)\n"
"}")
        self.horizontalLayout = QtWidgets.QHBoxLayout(Form)
        self.horizontalLayout.setContentsMargins(15, -1, 15, 15)
        self.horizontalLayout.setSpacing(20)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.lb_material = QtWidgets.QLabel(Form)
        font = QtGui.QFont()
        font.setPointSize(30)
        self.lb_material.setFont(font)
        self.lb_material.setAlignment(QtCore.Qt.AlignCenter)
        self.lb_material.setObjectName("label")
        self.verticalLayout.addWidget(self.lb_material)
        self.txt_material = QtWidgets.QLineEdit(Form)
        self.txt_material.setObjectName("lineEdit")
        self.verticalLayout.addWidget(self.txt_material)
        self.tableWidget = QtWidgets.QTableWidget(Form)
        self.tableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tableWidget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setColumnCount(3)
        self.tableWidget.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(0, item)
        self.tableWidget.setColumnWidth(0, 70)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(1, item)
        self.tableWidget.setColumnWidth(1, 50)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(2, item)
        self.tableWidget.setColumnWidth(2, 334)
        self.verticalLayout.addWidget(self.tableWidget)
        self.horizontalLayout.addLayout(self.verticalLayout)

        self.retranslateUi(Form)
        self.tableWidget.doubleClicked.connect(Form.close)
        QtCore.QMetaObject.connectSlotsByName(Form)
        self.create_functions()
        self.data_table()
    
    def create_functions(self):
        ...

    def data_table(self):
        ...

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Cadastros"))
        self.lb_material.setText(_translate("Form", "MATERIAIS"))
        item = self.tableWidget.horizontalHeaderItem(0)
        item.setText(_translate("Form", "COD"))
        item = self.tableWidget.horizontalHeaderItem(1)
        item.setText(_translate("Form", "MM"))
        item = self.tableWidget.horizontalHeaderItem(2)
        item.setText(_translate("Form", "Descrição"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Form = QtWidgets.QWidget()
    ui = Ui_Form()
    ui.setupUi(Form)
    Form.show()
    sys.exit(app.exec_())
