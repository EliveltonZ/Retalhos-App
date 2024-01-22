from gui_reserva import Ui_Form
from PySide6 import QtWidgets, QtCore
from mod_functions import Settings, Form, check_file_name
from mod_connection import CheckedOrder
from openpyxl import Workbook
from base_connection import Connection, ConnectionDB
from base_update_file import CSV
from typing import List, Any

setting = Settings()
path = setting.key('Directory_data_base')
type_connection = Connection.access()


class Frm_Reserva(Ui_Form):
    def __init__(self) -> None:
        super().__init__()
        self.result = list()

    def create_functions(self) -> None:
        self.bt_buscar_retalhos.clicked.connect(self.search_patchworks)
        self.tableWidget.itemClicked.connect(self.clicked_item)
        self.bt_reservar_retalhos.clicked.connect(self.confirm_reserve)

    def list_of_found(self, sql) -> List[str]:
        string_connection = type_connection.config_connection(path)
        with ConnectionDB(string_connection) as db:
            _sql = f'''SELECT '+' AS D, tblRetalhos.id, tblRetalhos.Setor, tblRetalhos.Cod_Material, tblChapas.MM, 
                        tblChapas.MDF, tblRetalhos.Largura, 'x' AS X, tblRetalhos.Altura, tblRetalhos.Reserva
                        FROM tblChapas INNER JOIN tblRetalhos ON tblChapas.COD = tblRetalhos.Cod_Material
                        WHERE ({sql}) ORDER BY tblChapas.MDF;'''
            data = db.select(_sql)
        return data

    def search_patchworks(self) -> None:
        if self.txt_num_proj.text() != '':
            try:
                file = self.check_file()
                name_file = check_file_name(
                    self.txt_num_proj.text(), first_name='PED')
                result = file.read_lines(name_file)
                values = file.search_date(result, 5)
                sql = file.sql_condition(values)
                data = self.list_of_found(sql)
                self.for_data(data)
                self.fill_table()
                self.config_table()
            except TypeError:
                self.clear_table()
                self.erro_find_project()
        else:
            self.clear_table()

    def erro_find_project(self) -> None:
        title = 'ERRO !!!'
        message = 'Projeto não encontrado'
        Form.form_warning(title, message)
        self.txt_num_proj.setText('')
        self.txt_num_proj.setFocus()

    def check_file(self) -> CheckedOrder:
        result = CheckedOrder(setting.key('Directory_cc') + setting.key('ped'))
        return result

    def for_data(self, data) -> None:
        for i in data:
            if i[9] == self.txt_num_proj.text() or i[9] == None or i[9] == '':
                values = ([i[0], str(i[1]), str(i[2]), int(i[3]), i[4],
                           i[5], str(i[6]), i[7], str(i[8]), str(i[9])])
                self.result.append(values)

    def select_list(self) -> list:
        values = self.values_table()
        sorted(values, key=lambda x: x[0])
        list_reservation = []
        for i in values:
            if i[0] == '+':
                value = [i[3], i[1], i[2], i[4], i[5], '', '', '',
                         '', i[6], i[7], i[8], self.txt_num_proj.text()]
                list_reservation.append(value)
        return list_reservation

    def values_table(self) -> list[Any]:
        data = []
        for row in range(self.tableWidget.rowCount()):
            linha = self.extract_row_data(row)
            data.append(linha)
        return data

    def extract_row_data(self, row) -> list[Any]:
        linha = []
        for col in range(self.tableWidget.columnCount()):
            item = self.tableWidget.item(row, col)
            if item is not None:
                linha.append(item.text())
            else:
                linha.append('')
        return linha

    def confirm_reserve(self) -> None:
        title = "Reserva"
        message = f"Confirmar reservas ?\n(Confirme somente após gerar o corte do projeto)"
        result = Form.form_question(title, message)
        if result:
            self.data_workbook()
            message = "Operação Concluída !!!"
            Form.form_information(title, message)

    def data_workbook(self) -> None:
        _list = self.select_list()
        for i in _list:
            table = 'tblRetalhos'
            column = 'Reserva'
            condition = 'id'
            value_condition = i[1]
            self.update_data_table(table, condition, value_condition, column)
            self.update_file(i[0], i[1])
        self.create_workbook(_list)

    def update_data_table(self, table: str, condition: str, value_condition: str, column: str) -> None:
        string_connection = type_connection.config_connection(path)
        with ConnectionDB(string_connection) as db:
            db.update(
                table, condition, value_condition, {f"{column}": f"{self.txt_num_proj.text()}"})

    def create_workbook(self, data) -> None:
        wb = Workbook()
        ws = wb.active
        nome_arquivo = 'PRJ_' + self.txt_num_proj.text() + '.xlsx'

        for k, row in enumerate(data):
            for v, item in enumerate(row[2:]):
                ws.cell(row=k+1, column=v+1, value=item) # type: ignore
        wb.save(nome_arquivo)

    def update_file(self, file_name, condition) -> None:
        name = check_file_name(file_name)
        self.del_row(name, condition)

    def del_row(self, file_name,  condition) -> None:
        path = setting.key('Directory_cc') + setting.key('ret')
        CSV.del_row(path, file_name, condition)

    def fill_table(self) -> None:
        self.tableWidget.setRowCount(len(self.result))
        for i in range(len(self.result)):
            for j in range(10):
                item = QtWidgets.QTableWidgetItem(str(self.result[i][j]))
                self.tableWidget.setItem(i, j, item)

                if item.text() == 'None':
                    item.setText('')

                if j != 5:
                    item.setTextAlignment(
                        QtCore.Qt.AlignCenter)  # type: ignore

    def clear_table(self) -> None:
        self.tableWidget.clearContents()
        self.tableWidget.setRowCount(0)

    def clicked_item(self, item: QtWidgets.QTableWidget) -> None:
        if item.column() == 0:  # type: ignore
            value_first_column = item.text()  # type: ignore
            if value_first_column == '+':
                new_item = QtWidgets.QTableWidgetItem('')
            else:
                new_item = QtWidgets.QTableWidgetItem('+')
            new_item.setTextAlignment(QtCore.Qt.AlignCenter)  # type: ignore
            self.tableWidget.setItem(item.row(), 0, new_item)  # type: ignore

    def config_table(self) -> None:
        self.tableWidget.setEditTriggers(
            QtWidgets.QTableWidget.NoEditTriggers)  # type: ignore
        columns_width = [44, 50, 50, 60, 55, 272, 70, 10, 70, 100]
        for k, v in enumerate(columns_width):
            self.tableWidget.setColumnWidth(k, v)
        new_height = 25
        for row in range(self.tableWidget.rowCount()):
            self.tableWidget.setRowHeight(row, new_height)
        self.bt_buscar_retalhos.setEnabled(True)
        self.result = []
        self.progressBar.setVisible(False)


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Frm_Reserva()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec())
