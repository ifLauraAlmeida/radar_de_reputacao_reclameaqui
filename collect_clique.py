import os
import pandas as pd
import time
import random
from dotenv import load_dotenv
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

load_dotenv()
URL_BASE = os.getenv("URL_ALVO")
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

def navegar_proximo(driver):
    try:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        btn = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="next-page-navigation-button"]'))
        )
        driver.execute_script("arguments[0].click();", btn)
        return True
    except: return False

def extrair_dados_estavel(driver, pagina_atual):
    dados = []
    try:
        links = driver.find_elements(By.XPATH, '//a[@id="site_bp_lista_ler_reclamacao"]')
        for link in links:
            try:
                titulo = link.find_element(By.TAG_NAME, "h4").text.strip()
                url_href = link.get_attribute("href")
                if titulo and url_href:
                    dados.append({"pagina": pagina_atual, "titulo": titulo, "link": url_href})
            except: continue
        return dados
    except: return []

# --- EXECUÇÃO ---
driver = configurar_driver_edge()
if driver:
    try:
        print(f"🚀 Iniciando Radar para: {nome_loja}")
        driver.get(f"{URL_BASE}/?pagina=51")
        
        print("\n" + "!"*50)
        print(f"AÇÃO MANUAL PARA {nome_loja.upper()}:")
        print("1. Aceite os cookies e resolva captchas.")
        print("2. Navegue até a página desejada.")
        print("3. Volte aqui e dê ENTER.")
        print("!"*50)
        input("Aguardando ENTER...")

        pbar = tqdm(range(52, 991), desc=f"🖱️ Coleta Ativa: {nome_loja}", unit="pag")
        for p in pbar:
            novos_dados = extrair_dados_estavel(driver, p)
            if novos_dados:
                pd.DataFrame(novos_dados).to_csv(arquivo_csv, mode='a', index=False, sep=';', 
                                              encoding='utf-8-sig', header=not os.path.exists(arquivo_csv))
                pbar.set_postfix({"Pag": p, "Itens": len(novos_dados)})
            
            if not navegar_proximo(driver):
                input(f"\n⚠️ Falha na pág {p+1}. Avance manualmente e dê ENTER...")
            
            time.sleep(random.uniform(20, 35))
    finally:
        driver.quit()