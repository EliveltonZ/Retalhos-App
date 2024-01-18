from gui_materiais import Ui_Form
from PySide6 import QtWidgets, QtCore
from base_connection import ConnectionDB, Connection
from mod_functions import Settings

setting = Settings()
path = setting.key('Directory_data_base')
type_connection = Connection.access()


class Frm_Materiais(Ui_Form):

    def create_functions(self) -> None:
        self.txt_material.textChanged.connect(self.filter_table)
        self.txt_material.textChanged.connect(self.convert_to_uppercase)
        self.tableWidget.doubleClicked.connect(self.catch_value)
        self.update_table()

    def catch_value(self) -> None:
        item = self.tableWidget.item(self.tableWidget.currentRow(), 0).text()
        if item:
            from mod_functions import v
            v.clear()
            v.append(item)

    def update_table(self) -> None:
        data = self.data_table()
        self.fill_table(data)

    def data_table(self) -> list:
        str_connection = type_connection.config_connection(path)
        with ConnectionDB(str_connection) as db:
            data = db.select('''SELECT tblChapas.COD, tblChapas.MM, tblChapas.MDF
                                FROM tblChapas ORDER BY tblChapas.MDF;
                                ''')
        return data

    def fill_table(self, data: list) -> None:
        self.tableWidget.setRowCount(len(data))
        for i in range(len(data)):
            for j in range(3):
                item = QtWidgets.QTableWidgetItem(str(data[i][j]))
                self.tableWidget.setItem(i, j, item)
                if j != 2:
                    item.setTextAlignment(QtCore.Qt.AlignCenter)

    def filter_table(self) -> None:
        filter_text = self.txt_material.text()
        for i in range(self.tableWidget.rowCount()):
            item = self.tableWidget.item(i, 2)
            if item is not None:
                item_text = item.text()
                if filter_text.lower() in item_text.lower():
                    self.tableWidget.setRowHidden(i, False)
                else:
                    self.tableWidget.setRowHidden(i, True)

    def convert_to_uppercase(self) -> None:
        text = self.txt_material.text()
        self.txt_material.setText(text.upper())


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QWidget()
    ui = Frm_Materiais()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec())
