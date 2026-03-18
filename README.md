# Radar de Reputação - Reclame AQUI
Sistema completo para coleta, análise e visualização de dados de reclamações do Reclame AQUI.

## 📁 Estrutura do Projeto

```
radar_reputacao_reclameaqui/
├── src/                          # Código fonte principal
│   ├── collectors/              # Coletores de dados
│   │   ├── __init__.py
│   │   ├── reclame_aqui_collector.py
│   │   └── complaint_details_collector.py
│   ├── processors/              # Processamento de dados
│   │   ├── __init__.py
│   │   ├── data_cleaner.py
│   │   └── sentiment_analyzer.py
│   └── analyzers/               # Análise e KPIs
│       ├── __init__.py
│       ├── kpi_calculator.py
│       └── trend_analyzer.py
├── data/                        # Dados do projeto
│   ├── raw/                     # Dados brutos coletados
│   ├── processed/               # Dados processados
│   └── external/                # Dados externos (se necessário)
├── notebooks/                   # Jupyter notebooks para exploração
│   ├── exploratory_analysis.ipynb
│   └── kpi_dashboard.ipynb
├── streamlit_app/               # Aplicação Streamlit
│   ├── app.py                   # App principal
│   ├── pages/                   # Páginas do dashboard
│   │   ├── 1_📊_Visão_Geral.py
│   │   ├── 2_📈_Tendências.py
│   │   ├── 3_🏢_Empresas.py
│   │   └── 4_⚙️_Configurações.py
│   ├── components/              # Componentes reutilizáveis
│   │   ├── __init__.py
│   │   ├── charts.py
│   │   └── filters.py
│   └── utils/                   # Utilitários do dashboard
│       ├── __init__.py
│       └── data_loader.py
├── tests/                       # Testes automatizados
│   ├── __init__.py
│   ├── test_collectors.py
│   └── test_analyzers.py
├── docs/                        # Documentação
│   ├── README.md
│   ├── api_documentation.md
│   └── data_dictionary.md
├── scripts/                     # Scripts de automação
│   ├── collect_data.py
│   ├── process_data.py
│   └── deploy_dashboard.py
├── config/                      # Configurações
│   ├── settings.yaml
│   └── companies_list.yaml
├── requirements.txt             # Dependências Python
├── pyproject.toml              # Configuração do projeto
├── .gitignore                  # Arquivos ignorados pelo Git
└── README.md                   # Documentação principal
```

## 🚀 Funcionalidades

### 📊 Coleta de Dados
- Lista de reclamações por empresa
- Detalhes completos das reclamações individuais
- Metadados (datas, status, categorias)

### 🔄 Processamento
- Limpeza e padronização de dados
- Análise de sentimento das reclamações
- Categorização automática

### 📈 Análise e KPIs
- Métricas de satisfação por empresa
- Tendências temporais
- Comparativos entre empresas
- Alertas de reputação

### 🎨 Dashboard Streamlit
- Visão geral com KPIs principais
- Gráficos interativos
- Filtros por empresa, período, categoria
- Exportação de relatórios

## 🛠️ Tecnologias

- **Python 3.8+**
- **Selenium** - Coleta de dados
- **Pandas/Polars** - Processamento
- **Streamlit** - Dashboard
- **Plotly** - Visualizações
- **SQLAlchemy** - Banco de dados (opcional)
- **Docker** - Containerização

## 🏢 Configuração de Empresas

### Como encontrar o slug de uma empresa

1. Acesse o Reclame AQUI: https://www.reclameaqui.com.br/
2. Procure pela empresa desejada
3. O slug é a parte final da URL, exemplo:
   - URL: `https://www.reclameaqui.com.br/empresa/magazine-luiza-loja-online/`
   - Slug: `magazine-luiza-loja-online`

### Configurando empresas para monitoramento

Edite o arquivo `config/companies_list.yaml`:

```yaml
companies:
  - name: "Nome da Empresa"
    url_slug: "slug-da-empresa-no-reclame-aqui"
    sector: "Setor da empresa"
    priority: "high|medium|low"
    active: true|false
```

### Exemplos de empresas já configuradas

- Magazine Luiza: `magazine-luiza-loja-online`
- Americanas: `americanas-com`
- Casas Bahia: `casas-bahia`
- Nubank: `nubank`
- iFood: `ifood`
- Uber: `uber`

### Scripts de coleta

```bash
# Testar uma empresa específica
python scripts/test_single_company.py

# Coletar dados de todas as empresas ativas
python scripts/collect_multiple_companies.py
```

## 📦 Instalação

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/radar-reputacao-reclameaqui.git
cd radar-reputacao-reclameaqui

# Instale dependências
pip install -r requirements.txt

# Execute o dashboard
streamlit run streamlit_app/app.py
```

## 🔧 Configuração

Edite `config/settings.yaml` para configurar:
- URLs das empresas a monitorar
- Intervalos de coleta
- Parâmetros de análise

## 📊 Uso

### Coleta de Dados
```bash
python scripts/collect_data.py --company "nome-empresa"
```

### Processamento
```bash
python scripts/process_data.py
```

### Dashboard
```bash
streamlit run streamlit_app/app.py
```

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para detalhes.