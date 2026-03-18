#!/usr/bin/env python3
"""Script simples para abrir o Reclame AQUI no Chrome e esperar você navegar até a lista de reclamações."""

import sys
from pathlib import Path

import click

# Adiciona o diretório src ao path (permitindo executar este script de qualquer lugar)
# Usa o root do projeto (pasta pai de `scripts/`), não `scripts/src`.
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "src"))

from collectors.reclame_aqui_collector import ReclameAquiCollector


@click.command()
@click.option("--url", default=None, help="URL inicial para abrir no navegador")
@click.option(
    "--config",
    default="config/settings.yaml",
    help="Arquivo de configuração (opcional, usado para ler base_url)",
)
def main(url, config):
    """Abre o navegador e espera o usuário navegar até a lista de reclamações."""

    collector = ReclameAquiCollector(base_url=url, config_path=config)
    collector.open_and_wait()


if __name__ == "__main__":
    main()
