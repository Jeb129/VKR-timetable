"""Методы для чтения изаписи excel файлов"""
import pandas as pd

def export_excel(path, data, structure):
    columns = pd.MultiIndex.from_tuples(structure)
    df = pd.DataFrame(data, columns=columns)
    df.to_excel(path, index=True)


def import_excel(path, structure = None):
    df = pd.read_excel(path,dtype=str,header=[0,1],)
    # Проверяем наличие пустой строки между заголовком и данными
    # Если есть - удаляем
    if df.iloc[0].isna().all():
        df = df.iloc[1:]

    # Удаляем колонки индекса
    def is_index_col(col):
        # MultiIndex случай
        if isinstance(col, tuple):
            return any(
                "Unnamed: 0" in str(part) for part in col
            )
        # fallback для single index
        return "Unnamed: 0" in str(col)

    # ищем индекс-колонку
    index_cols = [c for c in df.columns if is_index_col(c)]

    if index_cols:
        df = df.drop(columns=index_cols)
    # Проверяем, что состав колонок совпадает
    if structure is not None and list(df.columns) != structure:
        raise ValueError("Структура колонок не соответствует экспортируемой структуре")
    
    return df.to_numpy()