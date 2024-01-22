from PySide6 import QtWidgets, QtCore
from gui_remove_reserva import Ui_RemoveReserva
from base_connection import Connection, ConnectionDB
from mod_functions import Settings, Form

setting = Settings()
db_path = setting.key('Directory_data_base')
type_connection = Connection.access()


class Frm_RemoveReserva(Ui_RemoveReserva):

    COLUMN_COUNT = 10

    def create_functions(self) -> None:
        self.bt_remove_reservar.clicked.connect(self.confirm_removed)
        self.txt_num_proj.editingFinished.connect(self.fill_table)

    def select_table_values(self) -> list:
        string_connection = type_connection.config_connection(db_path)
        with ConnectionDB(string_connection) as db:
            sql = f"""SELECT tblRetalhos.id, tblRetalhos.Setor, tblRetalhos.Cod_Material, tblChapas.MM, tblChapas.MDF, 
            tblRetalhos.Largura, 'x' AS X, tblRetalhos.Altura, tblRetalhos.DataEntrada, tblRetalhos.Reserva, 
            tblRetalhos.DataReserva, tblRetalhos.Responsavel FROM tblChapas INNER JOIN tblRetalhos ON tblChapas.COD = tblRetalhos.Cod_Material 
            WHERE tblRetalhos.Reserva = '{self.txt_num_proj.text()}' ORDER BY tblChapas.MDF;"""
            data = db.select(sql)
        return data

    def search_reservations(self) -> list:
        data = self.select_table_values()
        values = []
        for i in data:
            values.append(['-', i[0], i[1], int(i[2]), i[3],
                           i[4], i[5], i[6], i[7], i[11]])
        return values

    def fill_table(self) -> None:
        num_proj_text = self.txt_num_proj.text()
        if num_proj_text:
            data = self.search_reservations()
            if data:
                self.bt_remove_reservar.setEnabled(True)
                self.tableWidget.setRowCount(len(data))
                for i, row_data in enumerate(data):
                    self.fill_table_row(i, row_data)
            else:
                self.show_empty_table_message()

    def fill_table_row(self, row_index: int, row_data: list) -> None:
        for j in range(self.COLUMN_COUNT):
            item_text = str(row_data[j])
            item = QtWidgets.QTableWidgetItem(item_text)
            self.tableWidget.setItem(row_index, j, item)
            if item_text == 'None':
                item.setText('')
            if j != 5:
                item.setTextAlignment(QtCore.Qt.AlignCenter)  # type: ignore

    def show_empty_table_message(self) -> None:
        self.txt_num_proj.setText('')
        self.clear_table()
        self.bt_remove_reservar.setEnabled(False)
        title = 'Erro'
        message = 'Projeto nao encontrado'
        Form.form_information(title, message)
        self.txt_num_proj.setFocus()

    def clear_table(self) -> None:
        self.tableWidget.clearContents()
        self.tableWidget.setRowCount(0)

    def confirm_removed(self) -> None:
        title = "Reserva"
        message = "Deseja deletar reservas do Projeto ?"
        result = Form.form_question(title, message)
        if result:
            self.remove_item()
            message = "Operação Concluída !!!"
            Form.form_information(title, message)

    def remove_item(self):
        if self.tableWidget.currentItem() is not None:
            for i in range(self.tableWidget.rowCount()):
                _id = self.tableWidget.item(i, 1).text()
                string_connection = type_connection.config_connection(db_path)
                with ConnectionDB(string_connection) as db:
                    db.delete('tblRetalhos', 'id', _id)


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QWidget()
    ui = Frm_RemoveReserva()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec())
