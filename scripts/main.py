from collectors.collect_link_data import coletar_dados
from collectors.collect_links import coletar_links

if __name__ == "__main__":
    # Fase 1: coleta as URLs das páginas de listagem (páginas 1–15)
    target_url = (
        "https://www.reclameaqui.com.br/empresa/mcdonalds/lista-reclamacoes/?pagina="
    )
    coletar_links(target_url, paginas=15, sleep_delay=10)

    # Fase 2: coleta os dados individuais de cada reclamação
    coletar_dados()
