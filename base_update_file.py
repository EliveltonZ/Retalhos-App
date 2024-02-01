from csv import reader, writer

class CSV:
    #função que acrescenta linha com dados no arquivo de retalho
    @staticmethod
    def write(path: str, file_name: str, dados: list) -> None:
        with open(path + file_name, 'a', newline='') as arquivo:
            escritor = writer(arquivo)
            escritor.writerows(dados)

    @staticmethod
    def create_file(path: str, file_name: str) -> None:
        with open(path + file_name, 'w', newline='') as file:
            pass  # Não faz nada, apenas cria o arquivo vazio

    # função que abre o arquivo e deleta a linha na qual se enquadra na condição e reescreve o arquivo
    @staticmethod
    def del_row(path: str, file_name: str,  condition: str) -> None:
        lines: list = list()
        with open(path + file_name, 'r', newline='') as csv_file:
            _reader = reader(csv_file, delimiter=',')
            for line in _reader:
                if line[6] == condition:
                    continue 
                lines.append(line)
        
        with open(path + file_name, 'w', newline='') as csv_file:
            escritor = writer(csv_file, delimiter=',')
            escritor.writerows(lines)

