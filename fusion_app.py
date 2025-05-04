
# fusion_app.py
import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Fusionador Scopus + WoS", layout="centered")

st.title("Fusionador de archivos bibliográficos: Scopus + WoS")
st.markdown("Sube tus archivos .csv y .txt exportados desde Scopus y Web of Science para fusionarlos y depurarlos.")

# Carga de archivos
scopus_files = st.file_uploader("Sube uno o más archivos CSV de Scopus", type="csv", accept_multiple_files=True)
wos_files = st.file_uploader("Sube uno o más archivos TXT de WoS", type="txt", accept_multiple_files=True)

if scopus_files:
    dfsco_list = []
    for file in scopus_files:
        df = pd.read_csv(file, encoding='utf-8', sep=',', engine='python')
        dfsco_list.append(df)
    dfsco = pd.concat(dfsco_list, ignore_index=True)
    if 'Author full names' in dfsco.columns:
        dfsco['Author full names'] = dfsco['Author full names'].str.replace(r'\s*\(\d+\)', '', regex=True)
    st.success(f"Archivos CSV de Scopus cargados correctamente: {len(scopus_files)} archivo(s), {dfsco.shape[0]} registros.")
    st.dataframe(dfsco.head())

if wos_files:
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
    st.success(f"Archivos TXT de WoS cargados correctamente: {len(wos_files)} archivo(s), {dfwos.shape[0]} registros.")
    st.dataframe(dfwos.head())
