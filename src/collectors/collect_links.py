'''
Módulo: Coletor de Links (Fase 1)
Projeto: Radar de Reputação - Reclame AQUI
Descrição: Responsável por navegar nas páginas de listagem de empresas e extrair 
           as URLs de cada reclamação individual. Utiliza técnicas de parse de 
           JSON (Next.js SSR) e Regex para garantir a captura dos dados.
Camada: Bronze (Extração de Links)
Autor: Laura Almeida
'''

import csv
import json
import re
import time
from datetime import datetime
from pathlib import Path
import requests
from tqdm import tqdm

# Configuração Base
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DELAY = 10 

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.7",
}

def extrair_links(html: str, link_re: re.Pattern) -> list:
    '''
    Extrai URLs de reclamações individuais de uma página de listagem do Reclame AQUI.
    
    A função busca os dados no objeto JSON '__NEXT_DATA__' injetado pelo Next.js (SSR). 
    Caso o objeto não seja encontrado ou falhe no parse, utiliza uma busca via Regex 
    direto no HTML como estratégia de fallback.
    
    Args:
        html (str): O conteúdo HTML bruto da página de listagem.
        link_re (re.Pattern): Expressão regular compilada para validar e capturar 
                              os slugs de link específicos da empresa alvo.
        
    Returns:
        list: Uma lista de strings contendo as URLs completas e únicas das reclamações.
    '''
    links = []
    match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.+?)</script>', html, re.DOTALL)
    
    if match:
        try:
            data = json.loads(match.group(1))
            def walk(obj):
                if isinstance(obj, str) and link_re.search(obj):
                    yield obj
                elif isinstance(obj, dict):
                    for v in obj.values(): yield from walk(v)
                elif isinstance(obj, list):
                    for item in obj: yield from walk(item)

            for h in walk(data):
                m = link_re.search(h)
                if m: links.append(f"https://www.reclameaqui.com.br{m.group(0)}")
        except json.JSONDecodeError: pass

    if not links:
        raw = link_re.findall(html)
        for slug in raw: links.append(f"https://www.reclameaqui.com.br{slug}")

    return list(dict.fromkeys(links))

def coletar_links(company_slug: str, output_path: Path, paginas: int = 15):
    '''
    Orquestra a navegação pelas páginas de listagem e salva os links de forma incremental.
    
    Acessa sequencialmente as páginas de reclamações de uma empresa, identifica novos links, 
    compara com os já existentes no CSV para evitar duplicatas e registra a data da coleta.
    
    Args:
        company_slug (str): O slug identificador da empresa (ex: 'mcdonalds').
        output_path (Path): Objeto Path indicando o destino do arquivo CSV na camada Bronze.
        paginas (int): O número total de páginas que o coletor deve percorrer.
        
    Returns:
        None: A função realiza o salvamento direto no sistema de arquivos.
    '''
    target_url = f"https://www.reclameaqui.com.br/empresa/{company_slug}/lista-reclamacoes/?pagina="
    link_re = re.compile(rf'/{company_slug}/[^"\'<>\s]+_[A-Za-z0-9_-]+/')
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Carregar existentes para evitar duplicatas
    existentes = set()
    if output_path.exists():
        with open(output_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            existentes = {row["url"] for row in reader if "url" in row}

    print(f"\n--- [FASE 1] Coletando links: {company_slug} ---")
    
    for pagina in tqdm(range(1, paginas + 1), desc=f"Páginas {company_slug}"):
        url = f"{target_url}{pagina}"
        try:
            r = requests.get(url, headers=BROWSER_HEADERS, timeout=20)
            if r.status_code == 200:
                links = extrair_links(r.text, link_re)
                novos = [l for l in links if l not in existentes]
                
                if novos:
                    escrever_header = not output_path.exists() or output_path.stat().st_size == 0
                    with open(output_path, "a", encoding="utf-8", newline="") as f:
                        writer = csv.DictWriter(f, fieldnames=["url", "collected_at"])
                        if escrever_header: writer.writeheader()
                        for l in novos:
                            writer.writerow({"url": l, "collected_at": datetime.now().isoformat()})
                    existentes.update(novos)
            
            time.sleep(2) # Delay entre páginas de listagem (pode ser menor que o de detalhe)
        except Exception as e:
            tqdm.write(f"  [ERRO] Falha na página {pagina}: {e}")