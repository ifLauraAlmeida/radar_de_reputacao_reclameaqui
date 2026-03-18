"""
Coleta URLs de reclamações individuais a partir das páginas de listagem.

Fonte: https://www.reclameaqui.com.br/empresa/mcdonalds/lista-reclamacoes/?pagina=N
Técnica: parse do __NEXT_DATA__ (Next.js SSR) via requests
"""

import csv
import json
import re
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import requests
from tqdm import tqdm

OUTPUT_CSV = Path("data/mcdonalds_reclamacoes_links.csv")
DELAY = 10  # segundos entre páginas

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


def extrair_links(html: str, link_re: re.Pattern) -> list:
    """Extrai URLs de reclamações do HTML da página de listagem."""
    links = []

    # Tentativa 1: parse do JSON embutido em __NEXT_DATA__
    match = re.search(
        r'<script id="__NEXT_DATA__"[^>]*>(.+?)</script>', html, re.DOTALL
    )
    if match:
        try:
            data = json.loads(match.group(1))
            hrefs = []

            def walk(obj):
                if isinstance(obj, str) and link_re.search(obj):
                    hrefs.append(obj)
                elif isinstance(obj, dict):
                    for v in obj.values():
                        walk(v)
                elif isinstance(obj, list):
                    for item in obj:
                        walk(item)

            walk(data)
            for h in hrefs:
                m = link_re.search(h)
                if m:
                    links.append(f"https://www.reclameaqui.com.br{m.group(0)}")
        except json.JSONDecodeError:
            pass

    # Tentativa 2: regex direto no HTML (fallback)
    if not links:
        raw = link_re.findall(html)
        for slug in raw:
            links.append(f"https://www.reclameaqui.com.br{slug}")

    return list(dict.fromkeys(links))  # remove duplicatas mantendo ordem


def carregar_links_existentes() -> set:
    """Lê o CSV e retorna o conjunto de URLs já salvas."""
    if not OUTPUT_CSV.exists():
        return set()
    with open(OUTPUT_CSV, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return {row["url"] for row in reader}


def salvar_links(novos_links: list, collected_at: str):
    """Adiciona os novos links ao CSV (cria o arquivo + cabeçalho se necessário)."""
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    novo_arquivo = not OUTPUT_CSV.exists()

    with open(OUTPUT_CSV, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["url", "collected_at"])
        if novo_arquivo:
            writer.writeheader()
        for url in novos_links:
            writer.writerow({"url": url, "collected_at": collected_at})


def coletar_links(target_url: str, paginas: int = 15, sleep_delay: int = DELAY):
    """Percorre as páginas de listagem e salva as URLs no CSV."""
    # Extrai o slug da empresa a partir da URL (ex: .../empresa/mcdonalds/lista-...)
    partes = urlparse(target_url).path.strip("/").split("/")
    company_slug = partes[1] if len(partes) > 1 else partes[0]
    link_re = re.compile(rf'/{company_slug}/[^"\'<>\s]+_[A-Za-z0-9_-]+/')
    print(f"  Slug identificado: {company_slug}")

    print(f"=== Fase 1: Coletando links de {paginas} páginas ===")
    existentes = carregar_links_existentes()
    print(f"  Links já no CSV: {len(existentes)}")

    total_novos = 0

    for pagina in tqdm(range(1, paginas + 1), desc="Páginas", unit="pág"):
        url = f"{target_url}{pagina}"
        tqdm.write(f"\n[Página {pagina}/{paginas}] {url}")

        try:
            r = requests.get(url, headers=BROWSER_HEADERS, timeout=20)
            print(f"  HTTP {r.status_code} | {len(r.text)} chars")

            if r.status_code != 200:
                tqdm.write(f"  Pulando — status {r.status_code}")
            else:
                collected_at = datetime.now().isoformat(timespec="seconds")
                links = extrair_links(r.text, link_re)
                novos = [l for l in links if l not in existentes]
                salvar_links(novos, collected_at)
                existentes.update(novos)
                total_novos += len(novos)
                tqdm.write(
                    f"  {len(links)} links extraídos | {len(novos)} novos | total acumulado: {len(existentes)}"
                )

        except Exception as e:
            tqdm.write(f"  Erro: {e}")

        if pagina < paginas:
            tqdm.write(f"  Aguardando {DELAY}s...")
            time.sleep(DELAY)

    print(
        f"\n=== Fase 1 concluída: {total_novos} novos links salvos em {OUTPUT_CSV} ==="
    )
