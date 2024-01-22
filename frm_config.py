from gui_config import Ui_Config
from PySide6 import QtWidgets, QtGui
from mod_functions import Settings, Form
from mod_config import Testing


class Frm_Config(Ui_Config):

    def __init__(self) -> None:
        super().__init__()
        self.run_tests()

    def create_functions(self) -> None:
        self.bt_search_path_3.clicked.connect(self.save_configuration)
        self.txt_maquina.textChanged.connect(self.convert_to_uppercase)
        self.load_json_values()

    def text_line_edit(self, value: bool) -> str:
        if value:
            return f'SUCESSO...'
        return f'FALHOU...'

    def run_tests(self) -> None:
        testing = Testing()
        directory, cut_app, data_base = self.data_json(testing)
        bool_cc, bool_db = self.check_configuration(
            testing, directory, cut_app, data_base)
        check_test_cc, check_test_db = self.values_test(bool_cc, bool_db)
        self.test_db = check_test_db
        self.test_cc = check_test_cc

    def values_test(self, bool_cc: bool, bool_db: bool) -> tuple[str, str]:
        check_test_cc = self.text_line_edit(bool_cc)
        check_test_db = self.text_line_edit(bool_db)
        return check_test_cc, check_test_db

    def check_configuration(self, testing: Testing, directory: str, cut_app: str, data_base: str) -> tuple[bool, bool]:
        bool_cc = testing.check_cut_app(directory, cut_app)
        bool_db = testing.file_test(data_base)
        return bool_cc, bool_db

    def data_json(self, testing: Testing) -> tuple[str, str, str]:
        testing = Testing()
        directory = testing.setting.key('Directory_cc')
        cut_app = testing.setting.key('Corte_certo')
        data_base = testing.setting.key('Directory_data_base')
        return directory, cut_app, data_base

    def load_json_values(self) -> None:
        setting = Settings()
        self.txt_corte_certo.setText(setting.key("Directory_cc"))
        self.txt_maquina.setText(setting.key("User"))
        self.txt_data_base.setText(setting.key("Directory_data_base"))

    def test_configuration(self) -> None:
        self.run_tests()
        self.lb_testing_cc_2.setText(self.test_cc)
        self.lb_testing_db_2.setText(self.test_db)
        self.color_label()

    def configuration_label(self, label: QtWidgets.QLabel) -> None:
        fonte = QtGui.QFont()
        fonte.setBold(True)
        label.setFont(fonte)
        if label.text() == 'SUCESSO...':
            label.setStyleSheet('color: rgb(0, 220, 0);')
        else:
            label.setStyleSheet('color: rgb(255, 255, 0);')

    def color_label(self) -> None:
        self.configuration_label(self.lb_testing_cc_2)
        self.configuration_label(self.lb_testing_db_2)

    def update_configuration(self) -> None:
        setting = Settings()
        setting.update_json('Directory_cc', self.txt_corte_certo.text())
        setting.update_json('User', self.txt_maquina.text())
        setting.update_json('Directory_data_base', self.txt_data_base.text())

    def convert_to_uppercase(self) -> None:
        text = self.txt_maquina.text().upper()
        self.txt_maquina.setText(text)

    def save_configuration(self) -> None:
        title = 'Configurações'
        message = 'Deseja Salva Configurações ?'
        result = Form.form_question(title, message)
        if result is True:
            self.update_configuration()
            self.test_configuration()
            message = 'Salvo com Sucesso !!!'
            Form.form_information(title, message)


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QWidget()
    ui = Frm_Config()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec())
