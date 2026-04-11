"""Методы для чтения изаписи excel файлов"""
from typing import List

import pandas as pd


class ExcelValidationError(Exception):
    def __init__(self, errors):
        self.errors = errors
        super().__init__("Ошмбка проверки структуры файла")


class ExcelValidator:
    def __init__(self, df: pd.DataFrame, strcture: List):
        self.df = df
        self.errors = []
        self.strcture = strcture

    def validate(self):
        self._validate_columns()

        return self.errors
    
    def _validate_columns(self):
        actual = {str(c).strip().lower(): c for c in self.df.columns}

        # отсутствующие
        for key, original_name in self.strcture.items():
            if key not in actual:
                self.errors.append({
                    "type": "missing_column",
                    "column": original_name,
                    "message": f"Отсутствует колонка '{original_name}'"
                })



def export_excel(path, data, structure):
    columns = pd.MultiIndex.from_tuples(structure)
    df = pd.DataFrame(data, columns=columns)
    df.to_excel(path, index=False)


def import_excel(path, structure = None):
    df = pd.read_excel(path)

    if structure is not None:
        err = ExcelValidator(df,structure)
        if err:
            raise ExcelValidationError(err)
        
    # return df.to_dict(orient="records")
    return df.values.tolist()