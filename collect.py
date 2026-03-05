import os
import pandas as pd
import time
import random
from dotenv import load_dotenv
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By

load_dotenv()
URL_BASE = os.getenv("URL_ALVO")

# Extrai o nome da loja da URL (ex: bagaggio-loja-fisica)
nome_loja = URL_BASE.split('/')[-2] if URL_BASE else "extração"
arquivo_csv = f'reclamacoes_{nome_loja}_edge.csv'

def configurar_driver_edge():
    edge_options = Options()
    edge_options.add_argument("--log-level=3") 
    edge_options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
    edge_options.add_experimental_option("useAutomationExtension", False)
    edge_options.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Edge(options=edge_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def coletar_pagina(driver, pagina):
    url = f"{URL_BASE}/?pagina={pagina}"
    driver.get(url)
    time.sleep(35) 
    driver.execute_script("window.scrollBy(0, 500);")
    time.sleep(2)

    dados_pagina = []
    try:
        links = driver.find_elements(By.XPATH, '//a[@id="site_bp_lista_ler_reclamacao"]')
        for link in links:
            try:
                titulo = link.find_element(By.TAG_NAME, "h4").text.strip()
                url_reclamacao = link.get_attribute("href")
                if titulo and url_reclamacao:
                    dados_pagina.append({"pagina": pagina, "titulo": titulo, "link": url_reclamacao})
            except: continue
    except Exception as e:
        print(f"Erro na extração: {e}")
    return dados_pagina

# --- EXECUÇÃO ---
ultima_pagina = 0
if os.path.exists(arquivo_csv):
    try:
        df_ex = pd.read_csv(arquivo_csv, sep=';', encoding='utf-8-sig')
        if not df_ex.empty: ultima_pagina = int(df_ex['pagina'].max())
        print(f"📊 Retomando {nome_loja} da página {ultima_pagina + 1}...")
    except: pass

driver = configurar_driver_edge()
if driver:
    try:
        pbar = tqdm(range(ultima_pagina + 1, 991), desc=f"🚀 Coletando {nome_loja}", unit="pag")
        for p in pbar:
            dados = coletar_pagina(driver, p)
            if dados:
                df = pd.DataFrame(dados)
                df.to_csv(arquivo_csv, mode='a', index=False, sep=';', 
                          encoding='utf-8-sig', header=not os.path.exists(arquivo_csv))
                pbar.set_postfix({"Pag": p, "Itens": len(dados)})
            time.sleep(random.uniform(5, 10))
    finally:
        driver.quit()