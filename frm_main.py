from gui_main import Ui_MainWindow
from PySide6 import QtCore, QtGui, QtWidgets
from frm_config import Frm_Config
from frm_novo_retalho import Frm_NovoRetalho
from frm_view_xml import Frm_View_Xml
from frm_reserva import Frm_Reserva
from frm_materiais import Frm_Materiais
from frm_remove_reserva import Frm_RemoveReserva
from datetime import datetime
from base_connection import Connection, ConnectionDB
from mod_functions import Settings, Form, check_file_name, del_files
from mod_create import Files
from mod_config import Testing
from base_update_file import CSV
from typing import Tuple

setting = Settings()
path = setting.key('Directory_data_base')
permission = setting.key('Remover')
password = setting.key('Password')
type_connection = Connection.access()


class Frm_Main(Ui_MainWindow):

    def keyPressEvent(self, event) -> None:
        if event.modifiers() & QtCore.Qt.ControlModifier and event.key() == QtCore.Qt.Key_R:  # type: ignore
            self.create_files()

    def active_menu(self) -> None:
        menu_enabled = setting.key('Menu').upper() == 'ATIVADO'
        self.menuPCP.setEnabled(menu_enabled)

    def config_table(self) -> None:
        column_widths = [50, 40, 50, 20, 290, 50, 10, 50, 120, 60, 120]
        for col, width in enumerate(column_widths):
            self.tableWidget.setColumnWidth(col, width)

    def create_functions(self) -> None:
        self.bt_add.clicked.connect(self.open_add)
        self.bt_config.clicked.connect(self.open_config)
        self.bt_removed.clicked.connect(self.msg_confirm)
        self.bt_info.clicked.connect(self.update_table)
        self.actionLeitor_XML.triggered.connect(self.open_view_xml)
        self.actionReserva.triggered.connect(self.open_reserva)
        self.actionMateriais.triggered.connect(self.open_material)
        self.txt_filter_color.textChanged.connect(self.filter_table)
        self.txt_filter_color.textChanged.connect(self.uppercase_text)
        self.tableWidget.doubleClicked.connect(self.remove_reserve)
        self.actionRemover_Reservas.triggered.connect(self.open_remove_reserva)
        self.check_cc()
        self.active_menu()
        self.config_table()

    def uppercase_text(self) -> None:
        text = self.txt_filter_color.text()
        self.txt_filter_color.setText(text.upper())

    def connection(self) -> Connection:
        if password:
            connection = type_connection.config_connection(path, password)
            return connection
        connection = type_connection.config_connection(path)
        return connection

    def del_row_table(self) -> None:
        value = self.get_id_value()
        str_connection = self.connection()
        with ConnectionDB(str_connection) as db:
            db.delete('tblRetalhos', 'id', value)
        self.update_table()

    def get_id_value(self) -> str:
        index_line = self.tableWidget.currentRow()
        value = self.tableWidget.item(index_line, 0).text()
        return value

    def del_row_csv(self) -> None:
        _id, cod = self.get_select_item_data()
        name, path = self.get_name_and_path(cod)
        CSV.del_row(path, name, _id)

    def get_name_and_path(self, cod: str) -> Tuple[str, str]:
        name = check_file_name(cod)
        path = setting.key('Directory_cc') + setting.key('ret')
        return name, path

    def get_select_item_data(self) -> Tuple[str, str]:
        index_line = self.tableWidget.currentRow()
        _id = self.tableWidget.item(index_line, 0).text()
        cod = self.tableWidget.item(index_line, 2).text()
        return _id, cod

    def remove_reserve_csv(self) -> None:
        current_item = self.tableWidget.currentItem()
        if current_item is not None:
            _id, cod = self.get_select_item_data()
            name = check_file_name(cod)
            path = setting.key('Directory_cc') + setting.key('ret')
            self.write_csv(_id, path, name)

    def write_csv(self, _id: str, path: str, name: str) -> None:
        lines = []
        for i in range(11):
            index_line = self.tableWidget.currentRow()
            value = self.tableWidget.item(index_line, i).text()
            if i == 0:
                lines.append(value)
            elif i == 1:
                lines.append('+')
            elif i == 2:
                lines.append('1')
            elif i == 5:
                lines.append(value)
            elif i == 7:
                lines.append(value)
            elif i == 8:
                lines.append(' ')
            elif i == 9:
                lines.append(_id)
            elif i == 10:
                lines.append('')
        CSV.write(path, name, [lines])

    def remove_reserve_db(self, _id) -> None:
        now = datetime.now().strftime('%d/%m/%Y %H:%M')
        user = setting.key('User')
        str_connection = self.connection()
        with ConnectionDB(str_connection) as conn:
            conn.update('tblRetalhos', 'id', _id, {
                        "Reserva": "", "Responsavel": f"{user}", "DataReserva": "", "DataEntrada": f"{now}"})

    def get_select_item_reserve(self) -> Tuple[str, str]:
        index_line = self.tableWidget.currentRow()
        _id = self.tableWidget.item(index_line, 0).text()
        reserve = self.tableWidget.item(index_line, 9).text()
        return _id, reserve

    def check_permission(self) -> bool:
        permission = setting.key('Remover')
        if permission.lower() != 'ativado':
            return True
        return False

    def remove_reserve(self) -> None:
        title = "Reserva"
        if self.tableWidget.currentItem() is not None:
            _id, reserve = self.get_select_item_reserve()
            # No else desse if é possível encaixar a reserva manual do retalho (futuramente)
            if reserve:
                if self.check_permission():
                    message = "Você não tem Permissão para remover Reservas"
                    Form.form_warning(title, message)
                else:
                    message = "Deseja remover reserva ?"
                    result = Form.form_question(title, message)
                    if result:
                        self.remove_reserve_csv()
                        self.remove_reserve_db(_id)
                        message = "Retalho disponível no estoque !!!"
                        Form.form_information(title, message)
                        self.update_table()

    def msg_confirm(self) -> None:
        try:
            reserva = self.get_value_reserve()
            title = "Exclusão"
            if reserva == '':
                message = "Confirmar Exclusão de Retalho?"
                result = Form.form_question(title, message)
                if result:
                    self.confirm_del()
                    message = "Retalho deletado com Sucesso !!!"
                    Form.form_information(title, message)
            else:
                message = "Não é possível deletar retalho reservado !!!"
                Form.form_critical(title, message)
        except Exception as e:
            title = 'Erro !!!'
            message = f'Selecione um item da Tabela para remover\n {e}'
            Form.form_critical(title, message)

    def confirm_del(self) -> None:
        try:
            self.del_row_csv()
            self.del_row_table()
            self.set_empty_text(self.txt_filter_color.text())
        except:
            ...

    def get_value_reserve(self) -> str:
        index_line = self.tableWidget.currentRow()
        reserve = self.tableWidget.item(index_line, 9).text()
        return reserve

    def open_material(self) -> None:
        Form.show(Frm_Materiais())

    def open_config(self) -> None:
        Form.show(Frm_Config())

    def open_add(self) -> None:
        Form.show(Frm_NovoRetalho())

    def open_view_xml(self) -> None:
        Form.show(Frm_View_Xml())

    def open_reserva(self) -> None:
        Form.show(Frm_Reserva())

    def open_remove_reserva(self) -> None:
        Form.show(Frm_RemoveReserva())

    def data_table(self) -> list:
        str_connection = self.connection()
        with ConnectionDB(str_connection) as db:
            data = db.select('''SELECT tblRetalhos.id, tblRetalhos.Setor, tblRetalhos.Cod_Material, 
            tblChapas.MM, tblChapas.MDF, tblRetalhos.Largura,'x' AS X, tblRetalhos.Altura, 
            tblRetalhos.DataEntrada, tblRetalhos.Reserva, tblRetalhos.DataReserva, 
            tblRetalhos.Responsavel 
            FROM tblChapas INNER JOIN tblRetalhos ON tblChapas.COD = tblRetalhos.Cod_Material
            ORDER BY tblChapas.MDF, tblRetalhos.Cod_Material, tblRetalhos.id;''')
        return data

    def update_table(self) -> None:
        try:
            data = self.data_table()
            self.tableWidget.setRowCount(len(data))
            for i in range(len(data)):
                test = False
                color = QtGui.QColor(0, 0, 0)

                for j in range(12):
                    item = QtWidgets.QTableWidgetItem(
                        str(data[i][j]))
                    self.tableWidget.setItem(i, j, item)

                    if item.text() == 'None':
                        item.setText('')

                    if j == 2:
                        value = item.text()
                        item.setText(value[:-2])

                    if j != 4:
                        item.setTextAlignment(
                            QtCore.Qt.AlignCenter)  # type: ignore

                    if j == 7 and item.text() == '1840.0':
                        color = QtGui.QColor(219, 105, 19)
                        test = True

                    if j == 9 and item.text() != '':
                        color = QtGui.QColor(255, 255, 0)
                        test = True

                    if j == 8:
                        datetime_str = item.text()
                        if datetime_str != '':
                            date = datetime.strptime(
                                datetime_str, '%Y-%m-%d %H:%M:%S')
                            format_date = date.strftime('%d/%m/%Y %H:%M:%S')
                            item.setText(format_date)

                if test:
                    for k in range(12):
                        current_item = self.tableWidget.item(i, k)
                        if current_item is not None:
                            current_item.setBackground(color)

                else:
                    test = False

        except Exception:
            self.txt_filter_color.setText(
                'Faça as configurações e após isso reinicie a aplicação')

    def filter_table(self) -> None:
        filter_text = self.txt_filter_color.text()
        lines = self.tableWidget.rowCount()
        for i in range(lines):
            item = self.tableWidget.item(i, 4)
            if item is not None:
                item_text = item.text()
                if filter_text.lower() in item_text.lower():
                    self.tableWidget.setRowHidden(i, False)
                else:
                    self.tableWidget.setRowHidden(i, True)

    def create_files(self) -> None:
        title = "Retalhos"
        message = '''Deseja criar o arquivos do corte certo com a base de dados ? 
(isso ira deletar todos os dados fora da base recriando os arquivos )'''
        result = Form.form_question(title, message)
        if result is True:
            del_files(setting.key('Directory_cc') + setting.key('ret'))
            file = Files()
            dados = file.get_data_table(self.tableWidget)
            file.create_files_ret(dados)
            message = "Arquivos gerados com Sucesso !!!"
            Form.form_information(title, message)

    def disable_button(self, btn: QtWidgets.QPushButton) -> None:
        btn.setEnabled(False)
        btn.setStyleSheet(
            "background-color: rgb(255, 30, 0); border-radius: 5px")

    def check_cc(self) -> None:
        t = Testing()
        directory = t.setting.key('Directory_cc')
        cut_app = t.setting.key('Corte_certo')
        check_test_cc = t.check_cut_app(directory, cut_app)
        if not check_test_cc:
            self.disable_button(self.bt_add)
            self.disable_button(self.bt_removed)

    def set_empty_text(self, text) -> None:
        self.txt_filter_color.setText('')
        self.txt_filter_color.setText(text)


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Frm_Main()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec())
