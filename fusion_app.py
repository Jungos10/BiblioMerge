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

    # ------------------ FUSIÓN INICIAL ------------------
    mapping = {
        'AU': 'Authors', 'AF': 'Author full names', 'TI': 'Title', 'PY': 'Year',
        'SO': 'Source title', 'VL': 'Volume', 'IS': 'Issue', 'CR': 'References',
        'BP': 'Page start', 'EP': 'Page end', 'PG': 'Page count', 'TC': 'Cited by',
        'DI': 'DOI', 'C3': 'Affiliations', 'AB': 'Abstract', 'DE': 'Author Keywords',
        'ID': 'Index Keywords', 'FX': 'Funding Texts', 'RP': 'Correspondence Address',
        'PU': 'Publisher', 'SN': 'ISSN', 'LA': 'Language of Original Document',
        'J9': 'Abbreviated Source Title', 'DT': 'Document Type', 'UT': 'EID', 'C1': 'Authors with affiliations'
    }

    dfwos_selected = dfwos.rename(columns=mapping)[mapping.values()]
    dfwos_selected['Source'] = 'WOS'
    dfsco['Source'] = 'scopus'
    df_concatenated = pd.concat([dfsco, dfwos_selected], ignore_index=True)
    df_concatenated.fillna('', inplace=True)

    df_concatenated['EID'] = df_concatenated['EID'].astype(str).str.replace('WOS:', '2-w-')

    excepciones = ['Year', 'Cited by', 'Volume', 'Page count', 'Issue', 'Art.No.', 'Page start', 'Page end']
    for columna in df_concatenated.columns:
        if columna not in excepciones and df_concatenated[columna].dtype == 'object':
            df_concatenated[columna] = df_concatenated[columna].str.lower()

    df_concatenated['References'] = df_concatenated['References'].str.replace(",,", ",")
    df_concatenated['Authors'] = df_concatenated['Authors'].str.replace(".-", ".")
    df_concatenated['Authors'] = df_concatenated['Authors'].str.replace(r'[.,]', '', regex=True)

    st.success("Archivos cargados y fusionados correctamente.")
    st.write("Vista previa del DataFrame fusionado:")
    st.dataframe(df_concatenated.head())

    # Guardar en sesión para reutilizar en otras fases
    st.session_state['df_concatenated'] = df_concatenated
    st.session_state['dfsco'] = dfsco
    st.session_state['dfwos'] = dfwos

else:
    st.warning("Por favor, sube los archivos CSV de Scopus y TXT de WoS para comenzar.")
