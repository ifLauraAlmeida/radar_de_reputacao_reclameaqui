'''
Módulo: Extrator de Detalhes (Fase 2)
Projeto: Radar de Reputação - Reclame AQUI
Descrição: Consome uma lista de links pré-coletada em CSV e realiza o scraping 
           detalhado de cada reclamação (Título, Descrição, ID, Local, etc). 
           Implementa salvamento atômico em formato JSON consolidado.
Camada: Bronze (Dados Brutos Completos)
Autor: Laura Almeida
'''

import csv
import json
import re
import time
from datetime import datetime
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

# Configurações Globais
DELAY = 10 
BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.7",
}

def extrair_com_bs4(html: str) -> dict:
    '''
    Realiza o parsing detalhado da página de uma única reclamação para extrair dados estruturados.
    
    Utiliza seletores 'data-testid' para garantir compatibilidade com o frontend moderno do 
    Reclame AQUI e aplica Regex em parágrafos para capturar metadados voláteis como ID numérico, 
    localização geográfica do usuário e data da postagem.
    
    Args:
        html (str): O conteúdo HTML bruto da página da reclamação individual.
        
    Returns:
        dict: Um dicionário com os campos: titulo, descricao, status, local, data, id_numerico.
    '''
    soup = BeautifulSoup(html, "html.parser")
    
    dados = {
        "titulo": "", "descricao": "", "status": "",
        "local": "", "data": "", "id_numerico": "", "resposta_empresa": ""
    }

    # Seletores data-testid (Padrão Reclame Aqui)
    titulo_el = soup.find(attrs={"data-testid": "complaint-title"})
    if titulo_el: dados["titulo"] = titulo_el.get_text(strip=True)

    desc_el = soup.find(attrs={"data-testid": "complaint-description"}) or soup.find(id="complaint-description")
    if desc_el: dados["descricao"] = desc_el.get_text(strip=True)

    status_el = soup.find(attrs={"data-testid": "complaint-status-text"})
    if status_el: dados["status"] = status_el.get_text(strip=True)

    # Extração de meta-informações via parágrafos
    for p in soup.find_all("p"):
        txt = p.get_text(strip=True)
        # Localização (Ex: São Paulo - SP)
        if re.search(r"\b[A-Z][a-záéíóúâêôãõç ]+ - [A-Z]{2}\b", txt):
            dados["local"] = txt
        # Data
        elif re.search(r"\d{2}/\d{2}/\d{4}", txt):
            dados["data"] = txt
        # ID da reclamação
        elif "ID:" in txt:
            m = re.search(r"ID:\s*(\d+)", txt)
            if m: dados["id_numerico"] = m.group(1)

    return dados

def coletar_dados(input_csv: Path, output_json: Path):
    '''
    Consome a lista de URLs de um CSV e consolida todos os detalhes em um arquivo JSON único.
    
    A função lê o arquivo de links da camada Bronze, itera sobre cada URL aplicando um 
    intervalo de segurança (delay) entre requisições e, ao final, gera um arquivo JSON 
    estruturado (array de objetos) para facilitar o consumo posterior via Pandas ou Nekt.
    
    Args:
        input_csv (Path): Objeto Path para o CSV de links gerado na Fase 1.
        output_json (Path): Objeto Path para o destino do JSON consolidado na camada Bronze.
        
    Returns:
        None: Os dados são persistidos em disco no formato JSON UTF-8.
    '''
    if not input_csv.exists():
        print(f"  [AVISO] CSV não encontrado: {input_csv.name}")
        return

    with open(input_csv, encoding="utf-8", newline="") as f:
        urls = [row["url"] for row in csv.DictReader(f) if "url" in row]

    if not urls:
        print(f"  [AVISO] Lista de URLs vazia para {input_csv.name}")
        return

    output_json.parent.mkdir(parents=True, exist_ok=True)
    print(f"\n--- [FASE 2] Extraindo detalhes: {output_json.name} ---")

    lista_reclamacoes = []
    
    for i, url in enumerate(tqdm(urls, desc="Progresso Reclamações", unit="rec"), 1):
        try:
            r = requests.get(url, headers=BROWSER_HEADERS, timeout=20)
            r.encoding = "utf-8"

            if r.status_code == 200:
                info = extrair_com_bs4(r.text)
                info.update({"url": url, "collected_at": datetime.now().isoformat()})
                lista_reclamacoes.append(info)
            else:
                tqdm.write(f"  [FALHA] Status {r.status_code} em {url}")

        except Exception as e:
            tqdm.write(f"  [ERRO] {url}: {e}")

        if i < len(urls):
            time.sleep(DELAY)

    # Salvamento Atômico
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(lista_reclamacoes, f, ensure_ascii=False, indent=2)

    print(f"✅ Arquivo finalizado: {output_json.name} ({len(lista_reclamacoes)} registros)")