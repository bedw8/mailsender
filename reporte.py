#!/usr/bin/env python
# coding: utf-8

import requests
import pandas as pd

seg = pd.read_pickle(
    "/Users/bedw/Documents/work/giftcards/extras/seguimiento_bruto.pkl"
)
seg = seg[["folio_ebs", "interview__key", "coordinador"]].set_index("folio_ebs")

## bbdd
r = requests.get("http://localhost:8000/people")
bbdd_df = pd.DataFrame(r.json())
bbdd_df = (
    bbdd_df[["ivkey", "mail", "nro_tarjeta", "sent_email", "skip", "skip_desc"]]
    .rename({"ivkey": "folio_ebs"}, axis=1)
    .set_index("folio_ebs")
)


def category(row):
    if row.sent_email:
        return "Enviado y Recibido"
    elif row.skip and row.skip_desc != "No hay email":
        return "Enviado y Rebotado"
    elif row.skip_desc == "No hay email":
        return "No hay email"
    else:
        return "Pendiente"


estado = bbdd_df.apply(category, axis=1)
bbdd_df.insert(0, "estado_resumen", estado)

reporte = seg.join(bbdd_df)

reporte.to_excel("reporte_giftcards.xlsx")
reporte[reporte.index.isin(bbdd_df.index)].to_excel("reporte_giftcards_cdf11.xlsx")

print(bbdd_df.estado_resumen.value_counts())
