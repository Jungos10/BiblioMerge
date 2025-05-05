
# fusion_app.py (adaptado fielmente desde tu código en Colab)
import streamlit as st
import pandas as pd
import io
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict
import zipfile
import base64

st.set_page_config(page_title="Fusionador Scopus + WoS", layout="centered")
st.title("Fusionador de archivos bibliográficos: Scopus + WoS")
st.markdown("Sube tus archivos CSV de Scopus y TXT de WoS para fusionarlos y depurarlos.")

# ------------------ CARGA DE ARCHIVOS ------------------
scopus_files = st.file_uploader("Sube uno o más archivos CSV de Scopus", type="csv", accept_multiple_files=True)
wos_files = st.file_uploader("Sube uno o más archivos TXT de WoS", type="txt", accept_multiple_files=True)

if scopus_files and wos_files:
    dfsco_list = []
    for file in scopus_files:
        df = pd.read_csv(file)
        dfsco_list.append(df)
    dfsco = pd.concat(dfsco_list, ignore_index=True)
    dfsco['Author full names'] = dfsco['Author full names'].str.replace(r'\s*\(\d+\)', '', regex=True)

    campos_multiples = ['AU', 'AF', 'CR']
    todos_registros = []
    for file in wos_files:
        registros = []
        registro_actual = {}
        ultimo_campo = None
        lines = file.getvalue().decode('ISO-8859-1').splitlines()
        for linea in lines:
            if not linea.strip() or linea.startswith('EF'):
                if registro_actual:
                    registros.append(registro_actual)
                    registro_actual = {}
                    ultimo_campo = None
                continue
            campo = linea[:2].strip()
            valor = linea[3:].strip()
            if not campo:
                if ultimo_campo in campos_multiples:
                    registro_actual[ultimo_campo] += "; " + valor
                else:
                    registro_actual[ultimo_campo] += " " + valor
            else:
                if campo in campos_multiples:
                    if campo in registro_actual:
                        registro_actual[campo] += "; " + valor
                    else:
                        registro_actual[campo] = valor
                else:
                    registro_actual[campo] = valor
                ultimo_campo = campo
        todos_registros.extend(registros)
    dfwos = pd.DataFrame(todos_registros)
