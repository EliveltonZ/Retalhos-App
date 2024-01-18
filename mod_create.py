from mod_functions import Settings, check_file_name
from csv import writer
from PySide6.QtWidgets import QTableWidget

setting = Settings()


class Files:
    def get_data_table(self, table_widget: QTableWidget) -> list:
        dados = []

        for linha in range(table_widget.rowCount()):
            linha_dados = []

            for coluna in range(table_widget.columnCount()):
                if coluna == 1:
                    continue
                elif coluna == 3:
                    continue
                elif coluna == 4:
                    continue
                elif coluna == 6:
                    continue
                elif coluna == 8:
                    continue
                elif coluna == 10:
                    continue
                elif coluna == 11:
                    continue
                else:
                    item = table_widget.item(linha, coluna)

                    if item is not None:
                        linha_dados.append(item.text())
                    else:
                        linha_dados.append(None)
            if linha_dados[4] == '':
                dados.append(linha_dados)
        return dados

    def create_files_ret(self, dados: list) -> None:
        self.path = setting.key('Directory_cc') + setting.key('ret')
        for cod in dados:
            file = check_file_name(cod[1])
            dados = [[cod[0], '+', '1', cod[2], cod[3], ' ', cod[0], '',]]
            self.write(file, dados)

    def write(self, file_name: str, dados: list) -> None:
        with open(self.path + file_name, 'a', newline='') as arquivo:
            escritor = writer(arquivo)
            escritor.writerows(dados)
