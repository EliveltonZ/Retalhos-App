from PySide6 import QtWidgets
from gui_novo_retalho import Ui_Add
from datetime import datetime
from mod_functions import Settings, Form, check_file_name, v
from base_connection import Connection, ConnectionDB
from base_update_file import CSV
from frm_materiais import Frm_Materiais
from typing import Tuple

setting = Settings()
path = setting.key('Directory_data_base')
type_connection = Connection.access()


class Frm_NovoRetalho(Ui_Add):

    def create_functions(self) -> None:
        self.txt_cod.editingFinished.connect(self.result_search_cod)
        self.txt_codigo_barra.editingFinished.connect(self.result_search_barcode)
        self.txt_setor.textChanged.connect(self.text_upper)
        self.bt_salvar.clicked.connect(self.msg_confirm)
        self.txt_responsavel.setText(setting.key('User'))
        self.bt_materiais.clicked.connect(self.open_form)

    def result_search_cod(self) -> None:
        try:
            dados = self.search_cod()
            self.txt_descricao.setText(dados[2])
            self.txt_mm.setText(dados[1])
            self.lb_message.setText('...')
            self.bt_salvar.setEnabled(True)
        except Exception as e:
            self.exception_search_cod()

    def search_cod(self) -> str:
        string_connection = type_connection.config_connection(path)
        with ConnectionDB(string_connection) as db:
            sql = f'SELECT * FROM tblChapas WHERE COD = {int(self.txt_cod.text())};'
            dados = db.select_item(sql)
            return dados

    def exception_search_cod(self) -> None:
        self.txt_descricao.setText('CÓDIGO INEXISTENTE')
        self.lb_message.setText(
            'Verifique se o código foi digitado corretamente')
        self.txt_mm.setText('')
        self.bt_salvar.setEnabled(False)

    def is_floating(self) -> bool:
        value1 = float(self.txt_largura.text())
        value2 = float(self.txt_altura.text())
        if isinstance(value1, float) and isinstance(value2, float):
            return True
        return False

    def validation_barcode(self) -> bool:
        if len(self.txt_codigo_barra.text()) == 21:
            return True
        return False

    def result_search_barcode(self) -> None:
        if self.validation_barcode():
            self.load_values()
            self.result_search_cod()
        else:
            if self.txt_codigo_barra.text() != '':
                self.except_result_search_barcorde()

    def except_result_search_barcorde(self) -> None:
        self.txt_descricao.setText('CÓDIGO DE BARRA INVÁLIDO')
        self.txt_cod.setText('')
        self.txt_largura.setText('')
        self.txt_altura.setText('')
        self.txt_mm.setText('')
        self.txt_data_entrada.setText('')
        self.txt_setor.setText('')

    def load_values(self) -> None:
        cod = self.txt_codigo_barra.text()[:7]
        large = self.txt_codigo_barra.text()[8:14]
        alt = self.txt_codigo_barra.text()[14:21]
        self.txt_cod.setText(str(int(cod)))
        self.txt_largura.setText(str(float(large)))
        self.txt_altura.setText(str(float(alt)))

    def text_upper(self) -> None:
        value = self.txt_setor.text().upper()
        self.txt_setor.setText(value)

    def insert_item(self) -> None:
        table, columns = self.get_table_and_columns()
        values = self.get_input_values()
        string_connection = type_connection.config_connection(path)
        with ConnectionDB(string_connection) as db:
            self.insert_item_into_database(db, table, columns, values)
            last_id = self.get_last_id(db)
        values_line = self.values_line(last_id)
        file_name = self.get_file_name()
        self.write_csv(file_name, values_line)

    def get_last_id(self, db: ConnectionDB) -> str:
        sql = 'SELECT TOP 1 id FROM tblRetalhos ORDER BY id DESC;'
        last_id = db.select_item(sql)[0]
        return last_id

    def get_file_name(self) -> str:
        return check_file_name(str(self.txt_cod.text()))

    def insert_item_into_database(self, db: ConnectionDB, table: str, columns: Tuple[str], values: Tuple[str, str, float, float, str, str]) -> None:
        db.insert(table, columns, values)  # type: ignore

    def get_table_and_columns(self) -> Tuple:
        table = 'tblRetalhos'
        columns = (
            'Setor', 'Cod_Material', 'Largura',
            'Altura', 'DataEntrada', 'Responsavel'
        )
        return table, columns

    def get_input_values(self) -> Tuple[str, str, float, float, str, str]:
        values = (
            self.txt_setor.text(),
            self.txt_cod.text(),
            float(self.txt_largura.text()),
            float(self.txt_altura.text()),
            self.txt_data_entrada.text(),
            self.txt_responsavel.text()
        )
        return values

    def values_line(self, last_id: str) -> list[list]:
        width = float(self.txt_largura.text())
        height = float(self.txt_altura.text())
        result = [[last_id, '+', '1', width, height, ' ', last_id, ''],]
        return result

    def write_csv(self, file_name: str, values_line: list[list]) -> None:
        path_ret = setting.key('Directory_cc') + setting.key('ret')
        CSV.write(path_ret, file_name, values_line)

    def msg_confirm(self) -> None:
        try:
            if self.is_floating() == True:
                title = "Retalhos"
                message = "Deseja Lançar novo retalho?"
                result = Form.form_question(title, message)
                self.lb_message.setText('...')
                if result:
                    now = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
                    self.txt_data_entrada.setText(now)
                    self.insert_item()
                    title = "Sucesso"
                    message = "Retalho Lançado com Sucesso !!!"
                    Form.form_information(title, message)
        except Exception as e:
            self.lb_message.setText('Dimensões de Retalho inválidos ...')
            print(e)

    def open_form(self) -> None:
        try:
            Form.show(Frm_Materiais())
            self.txt_cod.setText(v[0])
            self.txt_cod.setFocus()
            self.txt_descricao.setText('')
            self.txt_mm.setText('')
        except:
            ...


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QWidget()
    ui = Frm_NovoRetalho()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec())

