import pandas as pd
import re
from send_emails import Sender, send

## leemos el template html. las variables estan entre {}
from fastapi import Depends, FastAPI, HTTPException, status


def integration(
    p,
    temp_base,
    mssg_generator,
    sender_str,
    subject,
    email_col,
    test_mail_address=None,
    TEST=True,
    **kwargs,
):
    if not test_mail_address and TEST:
        raise Exception("Falta direccion")

    # l = locals()
    # print(l)
    # return

    # list template variables.
    # re.findall('{\w+}',temp_base) # output: ['{nombre}', '{monto}', '{nconvenio}']

    # def temp(**dict_):ebs2025@fen.uchile.cl
    #     '''Retorna el mensaje remplazando los valores indicados
    #
    #     ejemplo:
    #         mssg = temp(nombre='Benjamin',nconvenio='123',monto='$ 1000')
    #     '''
    #
    #     mssg = temp_base
    #     for k in dict_:
    #         mssg = re.sub('{'+k+'}',str(dict_[k]),mssg)
    #
    #     return mssg

    #### TEST
    if TEST:
        p = p.sample(1)

        p[email_col] = test_mail_address
        # p['mail'] = 'bedwards@fen.uchile.cl'

    # ## formato: punto delimitador para miles
    #
    #     def fmt_dinero(col):
    #         col = col.astype(float).round()
    #         col = col.apply(lambda x:f'{x:,}').str.replace(',','.')
    #         return col
    #
    #     cols = p.columns
    #     monto_cols = cols.where(cols.str.contains('[Mm]onto')).dropna()
    #     assert len(monto_cols) == 1
    #     monto_str = monto_cols[0]
    #     print()
    #     p[monto_str] =  fmt_dinero(p[monto_str])

    ## sender: nombre y direccion de salida
    # sender = Sender('Gestion Personas <gestionpersonas@microdatos.cl>')
    sender = Sender(sender_str)

    for i, row in p.iterrows():
        ## send(CORREO_DESTINO,ASUNTO,MENSAJE,html=True,sender=sender)
        # mssg = temp(**kwargs)
        v = {var: row[col] for var, col in kwargs.items()}
        mssg = mssg_generator(**v)

        send(row[email_col], subject, mssg, html=True, sender=sender)
        yield i
