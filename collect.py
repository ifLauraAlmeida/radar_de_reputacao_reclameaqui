# %%

import requests
from bs4 import BeautifulSoup
from urllib.parse import urlencode

chave_api_proxy = ''

def get_scrapeops_url(url):
    payload = {'api_key': chave_api_proxy, 'url': url, 'bypass': 'cloudflare_level_1'}
    proxy_url = 'https://proxy.scrapeops.io/v1/?' + urlencode(payload)
    return proxy_url

resp = requests.get(get_scrapeops_url('https://www.reclameaqui.com.br/empresa/bagaggio-loja-fisica/lista-reclamacoes/'))

#%%
resp.status_code
# %%
resp.text
# %%
soup = BeautifulSoup(resp.text)
soup
# %%
blocos = soup.find_all("div", class_="sc-1pe7b5t-0 eJgBOc")

dados = []

for bloco in blocos:
    a = bloco.find("a")
    if a:
        dados.append({
            "link": a["href"],
            "titulo": a.get_text(strip=True)
        })

dados
#%%
dados
# %%
# pega o primeiro link do dicionário
primeiro_link = dados[0]["link"]

# monta a url completa
base_url = "https://www.reclameaqui.com.br/empresa"
url_detalhe = base_url + primeiro_link

# faz nova requisição usando o proxy
resp_detalhe = requests.get(get_scrapeops_url(url_detalhe))

# verifica status
print(resp_detalhe.status_code)

# cria novo soup
soup_detalhe = BeautifulSoup(resp_detalhe.text, "html.parser")

# imprime para verificar
print(soup_detalhe)
# %%
