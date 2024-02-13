from gui_atualizador import Ui_Atualizador
from PySide6 import QtWidgets
from unzip import Zip
from mod_functions import Settings
import os

setting = Settings()
path_zip = setting.key('local_zip')

class FrmAtualizador(Ui_Atualizador):

    def create_functions(self) -> None:
        self.bt_atualizar.clicked.connect(self.update_app)
    
    def teste(self) -> None:
        print(f'{os.path.dirname(os.path.abspath(__file__))}')

    def update_app(self) -> None:
        Zip.extract_zip(path_zip, f'{os.path.dirname(os.path.abspath(__file__))}')
        print('atualização concluída com sucesso')


if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = FrmAtualizador()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec())
