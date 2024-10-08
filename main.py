#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pdfplumber
import os
from pathlib import Path
import concurrent.futures
import ipaddress

def is_valid_ip(ip):
    """
    Verifica se um endereço IP é válido.
    """
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

def extract_data_from_pdf(pdf_path):
    """
    Extrai dados da terceira coluna de tabelas com pelo menos 3 colunas em um PDF específico.

    Args:
        pdf_path (Path): Caminho para o arquivo PDF.

    Returns:
        list: Linhas formatadas para escrever no arquivo de output.
    """
    output_lines = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Itera sobre todas as páginas do PDF
            for i, page in enumerate(pdf.pages, start=1):
                # Extrai todas as tabelas da página
                tables = page.extract_tables()

                # Verifica se existem tabelas na página
                if tables:
                    for table_index, table in enumerate(tables, start=1):
                        # Itera sobre as linhas da tabela
                        for row_index, row in enumerate(table, start=1):
                            # Verifica se a linha tem pelo menos 3 colunas e pula a primeira linha (cabeçalho)
                            if len(row) >= 3 and row_index > 1 and not is_valid_ip(row[2]):
                                terceiro_dado = row[2]
                                if terceiro_dado and terceiro_dado.strip():
                                    # Formata a linha para o arquivo de output
                                    formatted_line = f"local-zone: \"{terceiro_dado.strip()}\" always_nxdomain\n"
                                    output_lines.append(formatted_line)
                                    # Imprime a mensagem de log
                                    print(f"Arquivo: {pdf_path.name} | Página {i}, Tabela {table_index}, Linha {row_index}: '{terceiro_dado.strip()}' adicionada no output")
                else:
                    # Indica que a página não possui tabelas
                    print(f"Arquivo: {pdf_path.name} | Página {i}: Não possui tabelas.")
    except Exception as e:
        print(f"Erro ao processar o arquivo {pdf_path.name}: {e}")

    return output_lines

def main():
    # Define o diretório atual onde o script está localizado
    current_dir = Path(__file__).parent

    # Define o arquivo de saída
    output_file_path = current_dir / "output.txt"

    # Encontra todos os arquivos PDF na pasta atual
    pdf_files = list(current_dir.glob("*.pdf"))

    if not pdf_files:
        print("Nenhum arquivo PDF encontrado na pasta atual.")
        return

    all_output_lines = []

    # Utiliza ProcessPoolExecutor para processar PDFs em paralelo
    with concurrent.futures.ProcessPoolExecutor() as executor:
        # Mapeia a função extract_data_from_pdf para cada PDF encontrado
        # Isso retorna um gerador de futuros
        futures = {executor.submit(extract_data_from_pdf, pdf_path): pdf_path for pdf_path in pdf_files}

        for future in concurrent.futures.as_completed(futures):
            pdf_path = futures[future]
            try:
                data = future.result()
                all_output_lines.extend(data)
                print(f"Concluída a extração do arquivo: {pdf_path.name}\n")
            except Exception as e:
                print(f"Erro ao processar o arquivo {pdf_path.name}: {e}")

    # Escreve todas as linhas coletadas no arquivo de saída
    try:
        with open(output_file_path, "w", encoding="utf-8") as output_file:
            output_file.writelines(all_output_lines)
        print(f"Extração concluída. Os dados foram salvos em '{output_file_path}'.")
    except Exception as e:
        print(f"Erro ao escrever no arquivo de saída: {e}")

if __name__ == "__main__":
    main()
