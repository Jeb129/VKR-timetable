"""Методы для чтения изаписи excel файлов"""
from io import BytesIO

import pandas as pd

def export_excel(target, data, structure):
    columns = pd.MultiIndex.from_tuples(structure)
    df = pd.DataFrame(data, columns=columns)
    # CASE 1: обычный путь (старое поведение)
    if isinstance(target, str):
        df.to_excel(target, index=True)
        return

    # CASE 2: file-like объект (BytesIO, UploadFile и т.п.)
    buffer = BytesIO()

    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=True)

    buffer.seek(0)

    # пишем в переданный поток
    target.write(buffer.read())


def import_excel(source, structure = None):
    df = pd.read_excel(source,dtype=str,header=[0,1],)
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