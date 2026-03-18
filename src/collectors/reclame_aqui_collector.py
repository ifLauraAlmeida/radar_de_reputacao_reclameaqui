"""Coletor mínimo do Reclame AQUI.

Este módulo abre o Chrome (via Selenium) e aguarda o usuário navegar manualmente
até a lista de reclamações da loja alvo.

O objetivo é ser simples e confiável: o script *não* tenta extrair dados automaticamente.
"""

import os
import random
import shutil
import time
from pathlib import Path

import yaml
from dotenv import load_dotenv
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


load_dotenv()

# Caminho padrão do arquivo de configuração (gera a base_url se não for informada via env/args)
DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "settings.yaml"


def _load_base_url_from_config(config_path: str | Path) -> str | None:
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        return cfg.get("collection", {}).get("base_url")
    except Exception:
        return None


def _load_config(config_path: str | Path) -> dict:
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def _find_chrome_binary(explicit_path: str | None = None) -> str | None:
    """Tenta resolver o caminho para o binário do Chrome/Chromium."""

    if explicit_path:
        return explicit_path

    candidates = [
        "google-chrome-stable",
        "google-chrome",
        "chromium-browser",
        "chromium",
    ]

    for candidate in candidates:
        path = shutil.which(candidate)
        if path:
            return path

    # Caminhos comuns em algumas distros
    common_paths = [
        "/opt/google/chrome/google-chrome",
        "/usr/bin/google-chrome",
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
    ]
    for path in common_paths:
        if os.path.exists(path):
            return path

    return None


def _configurar_driver_chrome(chrome_binary: str | None = None):
    chrome_options = Options()
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_experimental_option(
        "excludeSwitches", ["enable-logging", "enable-automation"]
    )
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")

    # Flags úteis em ambientes Linux/containers onde o Chrome pode falhar ao iniciar
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")

    # Permite personalizar args via variável de ambiente CHROME_ARGS
    chrome_args = os.getenv("CHROME_ARGS")
    if chrome_args:
        for arg in chrome_args.split():
            chrome_options.add_argument(arg)

    binary_path = _find_chrome_binary(chrome_binary)
    if binary_path:
        chrome_options.binary_location = binary_path
        print(f"🧩 Usando Chrome/Chromium: {binary_path}")
    else:
        print(
            "⚠️  Não encontrou binário do Chrome/Chromium automaticamente. "
            "Defina CHROME_BINARY_PATH para apontar para o executável."
        )

    # O Selenium 4.10+ inclui Selenium Manager, que busca e gerencia o driver automaticamente.
    # Assim, não precisamos fornecer o `Service` explicitamente.
    try:
        driver = webdriver.Chrome(options=chrome_options)
    except Exception:
        # Fallback: use webdriver-manager para baixar o driver compatível.
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver


class ReclameAquiCollector:
    """Coletor mínimo para abrir o navegador e aguardar ação manual."""

    def __init__(
        self,
        base_url: str | None = None,
        config_path: str | Path | None = None,
        chrome_binary: str | None = None,
    ):
        self.base_url = base_url or os.getenv("URL_ALVO")
        self.chrome_binary = chrome_binary or os.getenv("CHROME_BINARY_PATH")

        if not self.base_url and config_path is None:
            config_path = DEFAULT_CONFIG_PATH

        if not self.base_url and config_path:
            self.base_url = _load_base_url_from_config(config_path)

        if not self.base_url:
            raise SystemExit(
                "❌ URL base não definida. Defina URL_ALVO ou configure collection.base_url."
            )

        self.config = _load_config(config_path) if config_path else {}
        collection_cfg = self.config.get("collection", {})

        self.max_pages = collection_cfg.get("max_pages_per_company", 100)
        delay = collection_cfg.get("delay_between_requests", {})
        self.min_delay = delay.get("min", 10)
        self.max_delay = delay.get("max", 20)

        self.bronze_dir = Path("docs") / "bronze"
        self.bronze_dir.mkdir(parents=True, exist_ok=True)
        self.csv_path = self.bronze_dir / "complaints.csv"
        self.driver = None

    def _get_last_page(self):
        import pandas as pd

        if self.csv_path.exists():
            try:
                df = pd.read_csv(self.csv_path, sep=";", encoding="utf-8-sig")
                if not df.empty and "page" in df.columns:
                    return int(df["page"].max())
            except Exception:
                pass
        return 0

    def _append_bronze(self, rows: list[dict[str, str]]):
        import pandas as pd

        header = not self.csv_path.exists()
        df = pd.DataFrame(rows)
        df.to_csv(
            self.csv_path, mode="a", index=False, header=header, sep=";", encoding="utf-8-sig"
        )

    def _scrape_current_page(self, page_num: int) -> list[dict[str, str]]:
        """Extrai os dados estruturados da página atual."""
        complaints = []
        try:
            cards = self.driver.find_elements("xpath", '//a[@id="site_bp_lista_ler_reclamacao"]')
            for card in cards:
                try:
                    title = card.find_element("tag name", "h4").text.strip()
                    link = card.get_attribute("href")
                    complaints.append({"page": str(page_num), "title": title, "link": link})
                except Exception:
                    continue
        except Exception:
            pass
        return complaints

    def _click_next(self) -> bool:
        """Clica no botão de navegação de próxima página (barra de navegação)."""
        try:
            btn = self.driver.find_element(
                "css selector", "[data-testid='next-page-navigation-button']"
            )
            self.driver.execute_script("arguments[0].click();", btn)
            return True
        except Exception:
            return False

    def open_and_wait(self):
        """Abre o navegador, retoma coleta e salva complaints.csv em bronze/."""
        import pandas as pd

        try:
            self.driver = _configurar_driver_chrome(self.chrome_binary)
        except WebDriverException as e:
            raise SystemExit(
                "❌ Não foi possível iniciar o Chrome. Verifique se o Chrome/Chromium está instalado "
                "e/ou defina CHROME_BINARY_PATH.\n"
                f"Erro: {e}"
            )

        last_page = self._get_last_page()
        if last_page > 0:
            print(f"A última página lida foi a {last_page}.")
            print("Faça login manualmente e resolva desafios no navegador.")
            print("Posicione-se na página correta (recuada) e pressione ENTER.")
            recuo = max(1, last_page - 1)
            print(f"Voltando para a página {recuo} para garantir integridade.")
            input("Aguardando ENTER...")
            page = recuo
        else:
            print(f"🚀 Abrindo: {self.base_url}")
            self.driver.get(self.base_url)
            print("\n" + "=" * 60)
            print("⚠️  Ação manual necessária:")
            print("  1) Resolva cookies / captchas no navegador")
            print("  2) Navegue até a lista de reclamações da loja alvo")
            print("  3) Volte para este terminal e pressione ENTER para começar a coleta")
            print("=" * 60 + "\n")
            input("Aguardando ENTER...")
            page = 1

        while page <= self.max_pages:
            rows = self._scrape_current_page(page)
            if rows:
                self._append_bronze(rows)
                print(f"✅ Página {page} coletada: {len(rows)} itens")
            else:
                print(f"⚠️ Página {page} coletada: 0 itens")

            if page >= self.max_pages:
                break

            if not self._click_next():
                input(
                    "\n⚠️ Não consegui clicar em Próxima Página. Avance manualmente e pressione ENTER para continuar..."
                )

            wait_sec = random.uniform(self.min_delay, self.max_delay)
            print(f"⏳ Aguardando {wait_sec:.1f}s para evitar duplicados...")
            time.sleep(wait_sec)

            page += 1

        self.close()

    def close(self):
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            finally:
                self.driver = None


def main():
    collector = ReclameAquiCollector()
    collector.open_and_wait()


if __name__ == "__main__":
    main()
