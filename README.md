# Radar de Reputação — Reclame AQUI
 
> Pipeline de alta performance para mineração, análise e visualização de dados de reputação empresarial a partir do Reclame AQUI.
 
## Visão Geral
 
O Radar de Reputação é um sistema de engenharia de dados focado na coleta estruturada e análise de reclamações públicas disponíveis no Reclame AQUI. Ao invés de depender de emulação de navegador via Selenium — uma abordagem lenta e frágil — o sistema extrai dados diretamente das respostas de Server-Side Rendering (SSR) do portal, o que resulta em uma eficiência significativamente superior.
 
Com esse modelo de extração direta, o pipeline processa mais de 700 reclamações por hora e contorna limitações nativas da plataforma, como o bloqueio de paginação após a página 51. O projeto é configurável por empresa, tolerante a falhas e projetado para escalar horizontalmente.
 
<br>
 
## Diferenciais Técnicos
 
**Extração via SSR** — Os dados são lidos diretamente do HTML estruturado gerado pelo servidor, eliminando a sobrecarga de renderização de JavaScript e tornando a coleta até 12x mais rápida que abordagens baseadas em Selenium ou Playwright.
 
**Bypass de paginação** — O Reclame AQUI limita a navegação convencional a 50 páginas por empresa. O pipeline implementa uma estratégia alternativa de requisição que contorna essa restrição e acessa o histórico completo de reclamações.
 
**Pipeline orquestrado em duas fases** — A coleta é dividida em (1) extração de links de reclamações e (2) extração dos detalhes de cada reclamação. O orquestrador central gerencia a execução sequencial dessas fases para todas as empresas configuradas, com controle de profundidade por prioridade.
 
**Configuração declarativa** — Empresas são adicionadas e gerenciadas exclusivamente via arquivo YAML, sem necessidade de alterar código.
 
<br>
 
## ⚙️ Stack Tecnológica
 
| Componente | Função |
|---|---|
| **Python 3.12+** | Runtime principal |
| **Requests** | Requisições HTTP de baixo overhead |
| **BeautifulSoup4** | Parse e extração de dados do HTML |
| **Pandas** | Estruturação e manipulação dos dados coletados |
| **YAML** | Configuração declarativa de empresas-alvo |
| **TQDM** | Monitoramento visual do progresso no terminal |
| **Streamlit** | Interface de visualização *(em desenvolvimento)* |
 
<br>
 
## Configuração de Empresas
 
O arquivo `config/companies_list.yaml` é o ponto central de configuração do sistema. Para monitorar uma nova empresa, localize o seu slug na URL do Reclame AQUI (ex.: `reclameaqui.com.br/nubank/`) e adicione uma entrada no arquivo:
 
```yaml
companies:
  - name: "Nubank"
    url_slug: "nubank"
    priority: "high"   # Define a profundidade da coleta: high → max_pages
    active: true
```
 
O campo `priority` controla quantas páginas de reclamações serão coletadas para aquela empresa. Empresas com `active: false` são ignoradas pelo orquestrador.
 
<br>
 
## 🖥️ Instalação e Execução
 
### 1. Instalar dependências
 
Com o ambiente virtual ativado, instale o projeto em modo de desenvolvimento:
 
```bash
pip install -e .[dev]
```
 
### 2. Executar o pipeline
 
O script principal orquestra automaticamente as duas fases de coleta para todas as empresas ativas:
 
```bash
python scripts/main.py
```
 
O terminal exibirá barras de progresso individuais por empresa e fase.
 
<br>
 
## Roadmap
 
- [ ] **Data Cleaning** — Script de normalização de datas, remoção de ruído textual e padronização de campos.
- [ ] **Retry Logic** — Política de retentativas com backoff exponencial para falhas de DNS e instabilidades de rede.
- [ ] **Sentiment Analysis** — Integração com pipeline de NLP para classificação automática do tom das reclamações (positivo, neutro, negativo).
- [ ] **Streamlit Dashboard** — Painel interativo com KPIs de reputação, evolução temporal e comparação entre empresas.
 
<br>
 
## 📁 Estrutura do Projeto
 
```
radar_reputacao_reclameaqui/
├── src/                          # Código fonte principal
│   ├── collectors/               # Coletores de dados (links e detalhes)
│   ├── processors/               # Limpeza e análise de sentimento
│   └── analyzers/                # Cálculo de KPIs e tendências
├── data/
│   ├── raw/                      # Dados brutos coletados
│   ├── processed/                # Dados após limpeza e enriquecimento
│   └── external/                 # Fontes de dados complementares
├── streamlit_app/                # Dashboard interativo
│   ├── app.py                    # Entrypoint da aplicação
│   ├── pages/                    # Páginas do dashboard (multi-page)
│   ├── components/               # Componentes de UI reutilizáveis
│   └── utils/                    # Carregamento e cache de dados
├── notebooks/                    # Análise exploratória e prototipagem
├── tests/                        # Testes automatizados
├── scripts/                      # Scripts de coleta, processamento e deploy
├── config/
│   ├── companies_list.yaml       # Empresas monitoradas e configuração de coleta
│   └── settings.yaml             # Parâmetros globais do pipeline
├── docs/                         # Documentação técnica e dicionário de dados
├── pyproject.toml
└── requirements.txt
```
 
<br>
 
## Contribuição
 
Este projeto tem foco acadêmico e profissional em Engenharia de Dados. Contribuições são bem-vindas — abra uma *Issue* para discutir melhorias ou envie um *Pull Request* diretamente.
 
<br>
 
*Projeto desenvolvido como parte de uma iniciativa de estudo em coleta, estruturação e análise de dados públicos.*