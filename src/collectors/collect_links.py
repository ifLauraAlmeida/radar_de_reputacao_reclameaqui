"""
Coleta dados individuais de cada reclamação a partir das URLs no CSV.

Fonte: páginas individuais de reclamação (Astro SSR — HTML estático)
Técnica: requests + BeautifulSoup com seletores data-testid
"""

import csv
import json
import re
import time
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

INPUT_CSV = Path("data/mcdonalds_reclamacoes_links.csv")
OUTPUT_DIR = Path("data/reclamacoes")
DELAY = 10  # segundos entre requisições

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
    "image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.7",
    "Accept-Encoding": "gzip, deflate",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Upgrade-Insecure-Requests": "1",
}


def extrair_com_bs4(html: str) -> dict:
    """Extrai os campos da página de detalhe de uma reclamação."""
    soup = BeautifulSoup(html, "html.parser")

    titulo = ""
    el = soup.find(attrs={"data-testid": "complaint-title"})
    if el:
        titulo = el.get_text(strip=True)

    descricao = ""
    el = soup.find(attrs={"data-testid": "complaint-description"})
    if not el:
        el = soup.find(id="complaint-description")
    if el:
        descricao = el.get_text(strip=True)

    status = ""
    el = soup.find(attrs={"data-testid": "complaint-status-text"})
    if el:
        status = el.get_text(strip=True)

    local = ""
    data_rec = ""
    id_numerico = ""
    for p in soup.find_all("p"):
        txt = p.get_text(strip=True)
        if p.find("svg") and re.search(r"\b[A-Z][a-záéíóúâêôãõç]+ - [A-Z]{2}\b", txt):
            m = re.search(r"([A-Z][a-záéíóúâêôãõç ]+\s*-\s*[A-Z]{2})", txt)
            local = m.group(1).strip() if m else txt
        elif re.search(r"\d{2}/\d{2}/\d{4}", txt):
            data_rec = txt
        elif re.search(r"\bID:\s*\d+", txt):
            m = re.search(r"ID:\s*(\d+)", txt)
            id_numerico = m.group(1) if m else ""

    resposta_empresa = ""
    el = soup.find(attrs={"data-testid": "company-reply"})
    if not el:
        el = soup.find(id="company-reply")
    if not el:
        heading = soup.find(
            lambda t: t.name in ("h2", "h3", "h4")
            and "empresa" in t.get_text(strip=True).lower()
        )
        if heading:
            nxt = heading.find_next("p")
            if nxt:
                el = nxt
    if el:
        txt = el.get_text(strip=True)
        resposta_empresa = txt if len(txt) >= 20 else ""

    return {
        "titulo": titulo,
        "descricao": descricao,
        "status": status,
        "local": local,
        "data": data_rec,
        "id_numerico": id_numerico,
        "resposta_empresa": resposta_empresa,
    }


def nome_arquivo(url: str, id_numerico: str, timestamp: str) -> str:
    """Gera o nome do arquivo JSON com ID (ou slug) e timestamp de coleta."""
    base = id_numerico if id_numerico else url.rstrip("/").split("/")[-1]
    return f"{base}_{timestamp}.json"


def coletar_dados():
    """Lê o CSV de links e salva os dados de cada reclamação em JSON."""
    if not INPUT_CSV.exists():
        print(f"CSV não encontrado: {INPUT_CSV}")
        print("Execute primeiro a Fase 1 (coletar_links).")
        return

    with open(INPUT_CSV, encoding="utf-8", newline="") as f:
        urls = [row["url"] for row in csv.DictReader(f)]

    if not urls:
        print("Nenhuma URL no CSV.")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"=== Fase 2: Coletando dados de {len(urls)} reclamações ===")

    ok = 0
    erros = 0

    for i, url in enumerate(tqdm(urls, desc="Reclamações", unit="rec"), 1):
        tqdm.write(f"\n[{i}/{len(urls)}] {url}")

        try:
            r = requests.get(url, headers=BROWSER_HEADERS, timeout=20)
            r.encoding = "utf-8"
            tqdm.write(f"  HTTP {r.status_code} | {len(r.text)} chars")

            if r.status_code != 200:
                tqdm.write(f"  Pulando — status {r.status_code}")
                erros += 1
            else:
                dados = extrair_com_bs4(r.text)
                dados["url"] = url

                id_numerico = dados.get("id_numerico", "")

                # Pula se já existe algum arquivo com o mesmo ID (independente do timestamp)
                padrao = (
                    f"{id_numerico}_*.json"
                    if id_numerico
                    else f"{url.rstrip('/').split('/')[-1]}_*.json"
                )
                if list(OUTPUT_DIR.glob(padrao)):
                    tqdm.write(f"  Já coletado ({id_numerico}) — pulando")
                    ok += 1
                else:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    arquivo = OUTPUT_DIR / nome_arquivo(url, id_numerico, timestamp)
                    arquivo.write_text(
                        json.dumps(dados, ensure_ascii=False, indent=2),
                        encoding="utf-8",
                    )
                    tqdm.write(
                        f"  Salvo: {arquivo.name} | título: {dados.get('titulo', '')[:60]}"
                    )
                    ok += 1

        except Exception as e:
            tqdm.write(f"  Erro: {e}")
            erros += 1

        if i < len(urls):
            tqdm.write(f"  Aguardando {DELAY}s...")
            time.sleep(DELAY)

    print(f"\n=== Fase 2 concluída: {ok} OK | {erros} erros ===")
