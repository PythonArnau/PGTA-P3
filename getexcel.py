import pandas as pd
from openpyxl.utils.dataframe import dataframe_to_rows

def getKPIs(named_dicts, ws):
    offset = 1

    for name, d in named_dicts:

        df = pd.DataFrame(list(d.items()), columns=[f"{name}_Clave", f"{name}_Valor"])

        for r_idx, row in enumerate(dataframe_to_rows(df, index=False, header=True), start=1):
            for c_idx, value in enumerate(row, start=offset):
                ws.cell(row=r_idx, column=c_idx, value=value)

        offset += len(df.columns) + 2

