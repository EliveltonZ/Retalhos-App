from PySide6 import QtWidgets, QtCore
from PySide6.QtCore import QThread, Signal
from gui_view_xml import View_Xml
from mod_functions import Settings, ReaderXml, XmlParser, Form, check_file_name
from base_connection import Connection, ConnectionDB
from base_update_file import CSV
from datetime import datetime
from os.path import exists

setting = Settings()
path = setting.key('Directory_cc') + setting.key('ret')
path_db = setting.key('Directory_data_base')
user = setting.key('User')
type_connection = Connection.access()


class WorkerThread(QThread):
    update_progress = Signal(int)
    update_table = Signal(list)
    finished = Signal()
    text = Signal(str)

    def path(self, path: str) -> None:
        self._path = path

    def run(self) -> None:
        try:
            xml = ReaderXml(self._path)
            parser = XmlParser(xml.date)
            list_itens = parser.data_barcode
            if list_itens != 0:
                value_update = 100 / len(list_itens)
                v = 0
                self.result = []
                for item in list_itens:
                    self.__search_barcode(str(item))
                    v += value_update
                    self.update_progress.emit(v)

            data = self.result
            self.update_table.emit(data)
            self.finished.emit()
        except ZeroDivisionError:
            self.text.emit('Não Existem retalhos no programa selecionado !!!')

    def __search_barcode(self, value: str) -> None:
        cod = int(value[:7])
        wight = float(value[8:14])
        height = float(value[14:21])
        self.__search_item(cod, wight, height)

    def __search_item(self, cod, wight, height) -> None:
        string_connection = type_connection.config_connection(path_db)
        with ConnectionDB(string_connection) as db:
            sql = f'SELECT * FROM tblChapas WHERE COD = {cod};'
            mat = db.select_item(sql)[2]
            mm = db.select_item(sql)[1]
            tuple = ('+', cod, mm, mat, wight, 'x', height)
            self.result.append(tuple)


class Frm_View_Xml(View_Xml):
    def __init__(self) -> None:
        super().__init__()
        self.result = list()

    def create_functions(self) -> None:
        self.bt_buscar.clicked.connect(self.select_file)
        self.bt_exibir_retalhos.clicked.connect(self.thread_worker)
        self.tableWidget.itemClicked.connect(self.clicked_item)
        self.bt_lancar_retalhos.clicked.connect(self.confirm_insert)
        self.config_table()

    def select_file(self) -> None:
        path_file, _ = QtWidgets.QFileDialog.getOpenFileName(
            None, "Selecione um arquivo", "", "Corte Certo (*.cutplanning)")  # type: ignore
        self.txt_caminho.setText(path_file)

    def get_table_and_columns(self) -> tuple:
        table = 'tblRetalhos'
        columns = (
            'Cod_Material', 'Largura',
            'Altura', 'Reserva', 'DataReserva', 'Responsavel'
        )
        return table, columns

    def get_current_datetime(self) -> str:
        return datetime.now().strftime('%d/%m/%Y %H:%M:%S')

    def get_input_values(self, cod: str, width: float, height: float, reserve: str) -> tuple:
        hour = self.get_current_datetime()
        user = setting.key('User')
        values = (cod, width, height, reserve, hour, user)
        return values

    def get_last_id(self, db: ConnectionDB) -> int:
        sql = 'SELECT TOP 1 id FROM tblRetalhos ORDER BY id DESC;'
        last_id = db.select_item(sql)[0]
        return last_id

    def create_data_csv(self, _id: int, width: float, height: float, reserve: str) -> list[list]:
        return [[_id, '+', '1', width, height, reserve, _id, ''],]

    def get_file_name(self, cod: str) -> str:
        result = check_file_name(cod)
        return result

    def insert_into_database(self, db: ConnectionDB, table: str, columns: tuple[str], values: tuple) -> None:
        db.insert(table, columns, values)  # type: ignore

    def write_csv_file(self, path: str, file: str, data_csv: list) -> None:
        CSV.write(path, file, data_csv)

    def insert_into(self, cod: str, width: float, height: float, reserve: str) -> None:
        table, columns = self.get_table_and_columns()
        values = self.get_input_values(cod, width, height, reserve)
        string_connection = type_connection.config_connection(path_db)
        with ConnectionDB(string_connection) as db:
            self.insert_into_database(db, table, columns, values)
            last_id = self.get_last_id(db)

        data_csv = self.create_data_csv(last_id, width, height, reserve)
        file_name = self.get_file_name(cod)
        self.write_csv_file(path, file_name, data_csv)

    def insert_values_table(self) -> None:
        valores = self.list_values()
        for i in valores:
            self.insert_into(i[1], float(i[4]), float(
                i[6]), self.txt_sobra.text())

    def list_values(self) -> list:
        valores = []
        for row in range(self.tableWidget.rowCount()):
            linha = []
            for col in range(self.tableWidget.columnCount()):
                item = self.tableWidget.item(row, col)
                if item is not None:
                    linha.append(item.text())
                else:
                    linha.append('')
            if linha[0] != '':
                valores.append(linha)
        return valores

    def confirm_insert(self) -> None:
        title = "Reserva"
        if self.txt_sobra.text() != '':
            message = "Confirmar Lançamento ?"
            result = Form.form_question(title, message)
            if result:
                self.insert_values_table()
                message = "Retalho reservado com sucesso !!!"
                Form.form_information(title, message)
        else:
            message = "Defina um projeto para as reservas !!!"
            Form.form_information(title, message)

    def thread_worker(self) -> None:
        if exists(self.txt_caminho.text()):
            self.progressBar.setProperty("value", 0)
            self.clear_table()
            self.worker_thread = WorkerThread()
            self.progressBar.setVisible(True)
            self.worker_thread.path(self.txt_caminho.text())
            self.worker_thread.update_progress.connect(self.update_progress)
            self.worker_thread.update_table.connect(self.fill_table)
            self.worker_thread.finished.connect(self.progress_bar_visible)
            self.worker_thread.finished.connect(self.bt_buscar_disable)
            self.worker_thread.start()
            self.bt_exibir_retalhos.setEnabled(False)
            self.worker_thread.text.connect(self._file_empty)
        else:
            self.select_file()
            self.clear_table()
            self.bt_lancar_retalhos.setEnabled(False)

    def _file_empty(self, _str) -> None:
        if _str != '':
            self.txt_caminho.setText(_str)
            self.bt_lancar_retalhos.setEnabled(False)

    def progress_bar_visible(self) -> None:
        self.progressBar.setVisible(False)

    def update_progress(self, value: int) -> None:
        self.progressBar.setValue(value)

    def bt_buscar_disable(self) -> None:
        self.bt_exibir_retalhos.setEnabled(True)
        if self.tableWidget.rowCount() != 0:
            self.bt_lancar_retalhos.setEnabled(True)
            self.config_table()

    def fill_table(self, data: list) -> None:
        self.tableWidget.setRowCount(len(data))
        for i in range(len(data)):
            for j in range(7):
                item = QtWidgets.QTableWidgetItem(str(data[i][j]))
                self.tableWidget.setItem(i, j, item)

                if j != 3:
                    item.setTextAlignment(
                        QtCore.Qt.AlignCenter)  # type: ignore

    def config_table(self) -> None:
        self.tableWidget.setEditTriggers(
            QtWidgets.QTableWidget.NoEditTriggers)  # type: ignore
        width_columns = [15, 50, 40, 262, 50, 10, 50, 70]
        for k, v in enumerate(width_columns):
            self.tableWidget.setColumnWidth(k, v)
        new_height = 25
        for row in range(self.tableWidget.rowCount()):
            self.tableWidget.setRowHeight(row, new_height)
        self.bt_lancar_retalhos.setEnabled(True)
        self.result = []
        self.progressBar.setVisible(False)

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


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Frm_View_Xml()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec())
