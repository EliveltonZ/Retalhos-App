import pictures_rc
from PySide6 import QtCore, QtGui, QtWidgets
from mod_functions import PATH_ICON


class Ui_MainWindow(object):

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1200, 669)
        MainWindow.setMinimumSize(QtCore.QSize(1200, 669))
        icon = QtGui.QIcon.fromTheme(PATH_ICON)
        MainWindow.setWindowIcon(icon)
        MainWindow.setStyleSheet("QWidget#centralwidget{\n"
                                 "background-color: rgb(68, 114, 196);\n"
                                 "}\n"
                                 "QPushButton#bt_add{\n"
                                 "    border-image: url(:/pictures/pictures/Add_Icon.png);\n"
                                 "}\n"
                                 "QPushButton#bt_removed{\n"
                                 "    border-image: url(:/pictures/pictures/Remove_Icon.png);\n"
                                 "}\n"
                                 "QPushButton#bt_info{\n"
                                 "    border-image: url(:/pictures/pictures/Infor_Icon.png);\n"
                                 "}\n"
                                 "QPushButton#bt_config{\n"
                                 "    border-image: url(:/pictures/pictures/Conf_Icon.png);\n"
                                 "}\n"
                                 "QPushButton:hover{\n"
                                 "    background-color: rgba(195, 195, 195, 100);\n"
                                 "    border-radius: 5px\n"
                                 "}\n"
                                 "QLabel#lb_Menu{\n"
                                 "    color: rgb(255, 255, 255);\n"
                                 "}\n"
                                 "QLabel#lb_desenvolvedor{\n"
                                 "    color: rgb(89, 150, 255);\n"
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
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout_2.setContentsMargins(20, -1, -1, -1)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem = QtWidgets.QSpacerItem(
            40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.lb_Menu = QtWidgets.QLabel(self.centralwidget)
        self.lb_Menu.setMinimumSize(QtCore.QSize(0, 100))
        self.lb_Menu.setBaseSize(QtCore.QSize(0, 0))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(30)
        font.setBold(True)
        self.lb_Menu.setFont(font)
        self.lb_Menu.setObjectName("lb_Menu")
        self.horizontalLayout.addWidget(self.lb_Menu)
        spacerItem1 = QtWidgets.QSpacerItem(
            40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        spacerItem2 = QtWidgets.QSpacerItem(
            40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_4.addItem(spacerItem2)
        self.txt_filter_color = QtWidgets.QLineEdit(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.txt_filter_color.sizePolicy().hasHeightForWidth())
        self.txt_filter_color.setSizePolicy(sizePolicy)
        self.txt_filter_color.setObjectName("txt_filter_color")
        self.horizontalLayout_4.addWidget(self.txt_filter_color)
        spacerItem3 = QtWidgets.QSpacerItem(
            40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_4.addItem(spacerItem3)
        self.verticalLayout_2.addLayout(self.horizontalLayout_4)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        spacerItem4 = QtWidgets.QSpacerItem(
            40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem4)
        self.tableWidget = QtWidgets.QTableWidget(self.centralwidget)
        self.tableWidget.setMinimumSize(QtCore.QSize(1050, 0))
        self.tableWidget.setEditTriggers(
            QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tableWidget.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectRows)
        self.tableWidget.setRowCount(0)
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setColumnCount(12)
        item = QtWidgets.QTableWidgetItem()
        font = QtGui.QFont()
        font.setPointSize(9)
        font.setKerning(True)
        item.setFont(font)
        item.setBackground(QtGui.QColor(255, 255, 255))
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
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(10, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(11, item)
        self.horizontalLayout_2.addWidget(self.tableWidget)
        spacerItem5 = QtWidgets.QSpacerItem(
            40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem5)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setContentsMargins(10, 10, 10, -1)
        self.verticalLayout.setSpacing(30)
        self.verticalLayout.setObjectName("verticalLayout")
        self.bt_add = QtWidgets.QPushButton(self.centralwidget)
        self.bt_add.setMinimumSize(QtCore.QSize(80, 80))
        self.bt_add.setText("")
        self.bt_add.setObjectName("bt_add")
        self.verticalLayout.addWidget(self.bt_add)
        self.bt_removed = QtWidgets.QPushButton(self.centralwidget)
        self.bt_removed.setMinimumSize(QtCore.QSize(80, 80))
        self.bt_removed.setText("")
        self.bt_removed.setObjectName("bt_removed")
        self.verticalLayout.addWidget(self.bt_removed)
        self.bt_config = QtWidgets.QPushButton(self.centralwidget)
        self.bt_config.setMinimumSize(QtCore.QSize(80, 80))
        self.bt_config.setText("")
        self.bt_config.setObjectName("bt_config")
        self.verticalLayout.addWidget(self.bt_config)
        self.bt_info = QtWidgets.QPushButton(self.centralwidget)
        self.bt_info.setMinimumSize(QtCore.QSize(80, 80))
        self.bt_info.setText("")
        self.bt_info.setObjectName("bt_info")
        self.verticalLayout.addWidget(self.bt_info)
        spacerItem6 = QtWidgets.QSpacerItem(
            20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem6)
        self.horizontalLayout_2.addLayout(self.verticalLayout)
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)
        self.lb_desenvolvedor = QtWidgets.QLabel(self.centralwidget)
        self.lb_desenvolvedor.setObjectName("lb_desenvolvedor")
        self.verticalLayout_2.addWidget(self.lb_desenvolvedor)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menuBar = QtWidgets.QMenuBar(MainWindow)
        self.menuBar.setGeometry(QtCore.QRect(0, 0, 1270, 22))
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.menuBar.sizePolicy().hasHeightForWidth())
        self.menuBar.setSizePolicy(sizePolicy)
        self.menuBar.setFocusPolicy(QtCore.Qt.NoFocus)
        self.menuBar.setDefaultUp(False)
        self.menuBar.setNativeMenuBar(False)
        self.menuBar.setObjectName("menuBar")
        self.menuPCP = QtWidgets.QMenu(self.menuBar)
        self.menuPCP.setGeometry(QtCore.QRect(273, 127, 135, 94))
        self.menuPCP.setTearOffEnabled(False)
        self.menuPCP.setTitle("PCP")
        self.menuPCP.setObjectName("menuPCP")
        self.menuOpcoes = QtWidgets.QMenu(self.menuBar)
        self.menuOpcoes.setObjectName("menuOpcoes")
        MainWindow.setMenuBar(self.menuBar)
        self.actionLeitor_XML = QtWidgets.QWidgetAction(MainWindow)
        self.actionLeitor_XML.setObjectName("actionLeitor_XML")
        self.actionReserva = QtWidgets.QWidgetAction(MainWindow)
        self.actionReserva.setObjectName("actionReserva")
        self.actionMateriais = QtWidgets.QWidgetAction(MainWindow)
        self.actionMateriais.setObjectName("actionMateriais")
        self.actionRemover_Reservas = QtWidgets.QWidgetAction(MainWindow)
        self.actionRemover_Reservas.setObjectName("actionRemover_Reservas")
        self.menuPCP.addAction(self.actionLeitor_XML)
        self.menuPCP.addAction(self.actionReserva)
        self.menuOpcoes.addAction(self.actionMateriais)
        self.menuOpcoes.addAction(self.actionRemover_Reservas)
        self.menuBar.addAction(self.menuPCP.menuAction())
        self.menuBar.addAction(self.menuOpcoes.menuAction())
        MainWindow.keyPressEvent = self.keyPressEvent
        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
        self.create_functions()
        self.update_table()
        MainWindow.showMaximized()

    def create_functions(self):
        ...

    def update_table(self):
        ...

    def keyPressEvent(self, event):
        ...

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Retalhos"))
        self.lb_Menu.setText(_translate("MainWindow", "CONTROLE DE RETALHOS"))
        item = self.tableWidget.horizontalHeaderItem(0)
        item.setText(_translate("MainWindow", "ID"))
        item = self.tableWidget.horizontalHeaderItem(1)
        item.setText(_translate("MainWindow", "Setor"))
        item = self.tableWidget.horizontalHeaderItem(2)
        item.setText(_translate("MainWindow", "COD"))
        item = self.tableWidget.horizontalHeaderItem(3)
        item.setText(_translate("MainWindow", "MM"))
        item = self.tableWidget.horizontalHeaderItem(4)
        item.setText(_translate("MainWindow", "MDF"))
        item = self.tableWidget.horizontalHeaderItem(5)
        item.setText(_translate("MainWindow", "Lag"))
        item = self.tableWidget.horizontalHeaderItem(6)
        item.setText(_translate("MainWindow", "X"))
        item = self.tableWidget.horizontalHeaderItem(7)
        item.setText(_translate("MainWindow", "Alt"))
        item = self.tableWidget.horizontalHeaderItem(8)
        item.setText(_translate("MainWindow", "Data Entrada"))
        item = self.tableWidget.horizontalHeaderItem(9)
        item.setText(_translate("MainWindow", "Reserva"))
        item = self.tableWidget.horizontalHeaderItem(10)
        item.setText(_translate("MainWindow", "Data Saída"))
        item = self.tableWidget.horizontalHeaderItem(11)
        item.setText(_translate("MainWindow", "Responsavel"))
        self.lb_desenvolvedor.setText(_translate(
            "MainWindow", "Desenvolvido por: Elivelton Gonzaga"))
        self.menuOpcoes.setTitle(_translate("MainWindow", "Produção"))
        self.actionLeitor_XML.setText(_translate("MainWindow", "Leitor XML"))
        self.actionReserva.setText(_translate("MainWindow", "Reservar"))
        self.actionMateriais.setText(_translate("MainWindow", "Materiais"))
        self.actionRemover_Reservas.setText(
            _translate("MainWindow", "Remover Reservas"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec())
