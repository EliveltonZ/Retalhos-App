from typing import Any, Dict
import xml.dom.minidom
import xml.etree.ElementTree as ET
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMessageBox, QDialog
from os import path, listdir, remove
from json import load, dump

PATH_ICON = path.dirname(__file__) + '\\' + 'icon_retalho.ico'

v = []


class ReaderXml:
    def __init__(self, file_path: str) -> None:
        self.directory = file_path
        self.date = ''
        self.organized_xml()
        self.dom = xml.dom.minidom.parseString(self.date)

    def organized_xml(self) -> str | None:
        with open(self.directory, 'r', encoding='utf-8') as file:
            xml_string = file.read()
        dom = xml.dom.minidom.parseString(xml_string)
        xml_formatado = dom.toprettyxml()
        self.date = xml_formatado


class XmlParser:
    def __init__(self, xml_str) -> None:
        self.root = ET.fromstring(xml_str)
        self.data = list()
        self.parckwork_tag()
        self.data_barcode = self.tag_barcode_value()

    def search_tag_atribute(self, tag_name, atribute, value_atrubute) -> list[str]:
        elements = self.root.findall(
            f'.//{tag_name}[@{atribute}="{value_atrubute}"]')
        return [ET.tostring(elemento).decode() for elemento in elements]

    def parckwork_tag(self) -> None:
        result = self.search_tag_atribute(
            'com.geeksystem.cutplanning.cutplan.material.program.cut.data', 'template', '2')
        if result:
            for tag in result:
                self.data.append(tag)

    def tag_barcode_value(self) -> list:
        valores = []
        for field in self.root.findall('.//com.geeksystem.cutplanning.cutplan.material.program.cut.data.field'):
            if field.get('name') == '160':
                valores.append(field.get('value'))
            valid = list()
            for i in valores:
                if len(i) == 21:
                    valid.append(i)
        return valid


class Settings:
    def __init__(self, file_name: str = 'Settings.json') -> None:
        self.__file_settings(file_name)

    def __file_settings(self, file_name: str) -> Dict:
        with open(file_name, 'r') as file:
            self.settings_dict: dict = load(file)
        return self.settings_dict

    def key(self, key: str) -> str:  # type: ignore
        for i, value in self.settings_dict.items():
            if i == key:
                return value

    def update_json(self, key: str, value: str) -> None:
        with open('Settings.json', 'r') as file:
            data = load(file)

        data[key] = value

        # Salvando as alterações de volta no arquivo
        with open('Settings.json', 'w') as file:
            dump(data, file, indent=2)


class Form:

    @staticmethod
    def show(class_form) -> None:
        dialog = QDialog()
        form = class_form
        form.setupUi(dialog)
        dialog.exec()

    @staticmethod
    def form_warning(title: str, message: str) -> None:
        form = QMessageBox()
        icon = QIcon.fromTheme(PATH_ICON)
        form.setWindowIcon(icon)
        form.setWindowTitle(title)
        form.setText(message)
        form.setStandardButtons(QMessageBox.Ok)
        form.setIcon(QMessageBox.Warning)
        form.exec()

    @staticmethod
    def form_critical(title: str, message: str) -> None:
        form = QMessageBox()
        icon = QIcon.fromTheme(PATH_ICON)
        form.setWindowIcon(icon)
        form.setWindowTitle(title)
        form.setText(message)
        form.setStandardButtons(QMessageBox.Ok)
        form.setIcon(QMessageBox.Critical)
        form.exec()

    @staticmethod
    def form_information(title: str, message: str) -> None:
        form = QMessageBox()
        icon = QIcon.fromTheme(PATH_ICON)
        form.setWindowIcon(icon)
        form.setWindowTitle(title)
        form.setText(message)
        form.setStandardButtons(QMessageBox.Ok)
        form.setIcon(QMessageBox.Information)
        form.exec()

    @staticmethod
    def form_question(title: str, message: str) -> bool:
        form = QMessageBox()
        icon = QIcon.fromTheme(PATH_ICON)
        form.setWindowIcon(icon)
        form.setWindowTitle(title)
        form.setText(message)
        form.setIcon(QMessageBox.Question)
        form.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        result = form.exec()
        if result == 16384:
            return True
        else:
            return False


def check_file_name(value: str, first_name: str = 'RET', last_name: str = '.TAB') -> str:
    result = ''
    if len(value) < 5:
        number = '0'
        result = (first_name + number*(5-len(value)) + value + last_name)
    else:
        result = (first_name + value + last_name)
    return result


def del_files(_path: str, condition: str = 'RET') -> None:
    if path.isdir(_path):
        for file in listdir(_path):
            if file.startswith(condition):
                file_name = path.join(_path, file)
                remove(file_name)
    else:
        raise f'Caminho Invalido'


if __name__ == '__main__':
    directory = r'C:\Users\GD\Desktop\RetalhosApp\28_ASSIST_WAGNER PEREIRA BARROS_20_10_2023_08_06_13.cutplanning'
    # directory = r'C:\\Users\\GD\\Desktop\\RetalhosApp\\28_ASSIST_WAGNER PEREIRA BARROS_20_10_2023_08_06_13.cutplanning'
    xml = ReaderXml(directory)
    parser = XmlParser(xml.date)
    # print(parser.data_barcode)
    for i in parser.data_barcode:
        cod = int(i[:7])
        larg = float(i[8:14])
        alt = float(i[14:21])
        # print(cod, larg, alt)
    # print(xml.date)
    # print(PATH_ICON)
    s = Settings('Settings.json')
    caminho = s.key('Directory_cc') + s.key('ret')
    s.update_json('Remover', 'Desativado')
    print(caminho)
    # print(s.key('backup_data_base'))
    # print(s.key('site'))
    # for row in (s.set_settings('Settings.json').items()):
    #     print(row[0], '-', row[1])
    # del_files('C:\\corte_certo_plus\\CHP\\')
