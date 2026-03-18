import pandas as pd


def load_complaints_csv(csv_path):
    """Carrega o complaints.csv da camada bronze."""
    return pd.read_csv(csv_path, sep=";", encoding="utf-8-sig")


def remove_duplicates(df):
    """Remove duplicatas do DataFrame de reclamações.
    Duplicatas são consideradas pelo campo 'link'.
    """
    return df.drop_duplicates(subset=["link"])


def save_cleaned_csv(df, csv_path):
    """Salva o DataFrame limpo no complaints.csv."""
    df.to_csv(csv_path, index=False, sep=";", encoding="utf-8-sig")


def clean_complaints_csv(csv_path):
    """Carrega, remove duplicatas e salva complaints.csv limpo."""
    df = load_complaints_csv(csv_path)
    df_clean = remove_duplicates(df)
    save_cleaned_csv(df_clean, csv_path)
    return df_clean
