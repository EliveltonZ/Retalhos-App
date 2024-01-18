from mod_functions import Settings
from os.path import isfile

class Testing:

    def __init__(self) -> None:
        self.setting = Settings()

    def file_test(self, directory) -> bool:
        path = isfile(directory)
        if path:
            return True
        return False

    def check_cut_app(self, directory, cut_app) -> bool:
        exe = directory + cut_app
        path = isfile(exe)
        if path:
            return True
        return False
    
if __name__ == '__main__':
    t = Testing()
    print(t.file_test(t.setting.key('Directory_data_base')))
    print(t.check_cut_app(Settings().key('Directory_cc'), Settings().key('Corte_certo')))