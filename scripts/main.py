'''
Módulo: Orquestrador do Pipeline
Projeto: Radar de Reputação - Reclame AQUI
Descrição: Motor principal que lê as configurações de empresas do arquivo 
           'companies_list.yaml' e gerencia a execução sequencial dos coletores. 
           Responsável pela injeção de caminhos dinâmicos e controle de prioridades.
Dependências: PyYAML, collectors.collect_links, collectors.collect_links_data
Autor: Laura Almeida
'''

import yaml
from pathlib import Path
# Note: Certifique-se que o nome da pasta é 'src.collectors' se estiver usando o pyproject.toml
from collectors.collect_links import coletar_links
from collectors.collect_links_data import coletar_dados

# Configuração de caminhos
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config" / "companies_list.yaml"
BRONZE_DIR = BASE_DIR / "docs" / "bronze"

def run_pipeline():
    '''
    Executa o pipeline completo de coleta para todas as empresas ativas no YAML.
    Possui travas de segurança para pular empresas já processadas.
    '''
    if not CONFIG_PATH.exists():
        print(f"❌ Erro: Arquivo de configuração não encontrado em {CONFIG_PATH}")
        return

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    companies = config.get("companies", [])
    schedules = config.get("collection_schedule", {})

    BRONZE_DIR.mkdir(parents=True, exist_ok=True)

    for company in companies:
        if not company.get("active"):
            continue

        name = company["name"]
        slug = company["url_slug"]
        priority = company["priority"]
        
        max_pages = schedules.get(priority, {}).get("max_pages", 10)
        
        csv_path = BRONZE_DIR / f"{slug}_links.csv"
        json_path = BRONZE_DIR / f"{slug}_reclamacoes_full.json"

        # --- TRAVA DE SEGURANÇA (IDEMPOTÊNCIA) ---
        if json_path.exists() and json_path.stat().st_size > 500: # 500 bytes para garantir que não está vazio
            print(f"⏩ [PULANDO] {name} já possui dados coletados em: {json_path.name}")
            continue

        print(f"\n🚀 Iniciando Pipeline: {name} (Prioridade: {priority})")
        
        # Fase 1: Links (Esta função já é incremental por natureza, ela não sobrescreve)
        coletar_links(company_slug=slug, output_path=csv_path, paginas=max_pages)
        
        # Fase 2: Dados (Só executa se o JSON completo ainda não existir)
        coletar_dados(input_csv=csv_path, output_json=json_path)

if __name__ == "__main__":
    run_pipeline()