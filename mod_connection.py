from os.path import isfile
from csv import reader
from mod_functions import Settings

setting = Settings('Settings.json')


class CheckedOrder:
    def __init__(self, directory) -> None:
        self.directory = directory

    def checked_file(self, file_name: str) -> bool:
        file_path = self.directory + file_name
        if isfile(file_path) is True:
            return True
        else:
            return False

    # função para ler o arquivo de retalhos na pasta
    def read_lines(self, file_name: str) -> list[list[str]] | None:
        if self.checked_file(file_name) is True:
            with open(self.directory + file_name, 'r', newline='') as file:
                _reader = reader(file, delimiter=' ')
                rows = list(_reader)
            return rows

    def search_date(self, _list: list, item_position: int) -> list:
        list_colors = []
        date = _list
        for row in date:
            if row[item_position] in list_colors:
                ...
            else:
                list_colors.append(row[item_position])
        return list_colors

    def sql_condition(self, list_color) -> str:
        _str = ''
        for k, v in enumerate(list_color):
            if k == 0:
                _str += f'(tblRetalhos.Cod_Material)={v}'
            elif k == len(list_color)-1:
                _str += f' Or (tblRetalhos.Cod_Material)={v}'
            else:
                _str += f' Or (tblRetalhos.Cod_Material)={v}'
        return _str

    def sql_id(self, list_id: list) -> str:
        _str = ''
        for k, v in enumerate(list_id):
            if k == 0:
                _str += f'(tblRetalhos.id)={v}'
            elif k == len(list_id)-1:
                _str += f' Or (tblRetalhos.id)={v}'
            else:
                _str += f' Or (tblRetalhos.id)={v}'
        return _str


if __name__ == '__main__':
    ...
