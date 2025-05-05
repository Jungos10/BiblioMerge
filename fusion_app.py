
import streamlit as st
import pandas as pd
import io
import tempfile
import xlsxwriter
import zipfile
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict

st.set_page_config(page_title="Fusionador Scopus + WoS", layout="centered")
st.title("Fusionador de archivos bibliográficos: Scopus + WoS")
st.markdown("Sube tus archivos .csv y .txt exportados desde Scopus y Web of Science para fusionarlos y depurarlos.")

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
    st.success(f"Scopus: {len(scopus_files)} archivo(s), {dfsco.shape[0]} registros.")

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
    st.success(f"WOS: {len(wos_files)} archivo(s), {dfwos.shape[0]} registros.")

if 'dfsco' in locals() and 'dfwos' in locals():
    if st.button("Fusionar y depurar registros"):
        mapping = {'AU': 'Authors', 'AF': 'Author full names', 'TI': 'Title', 'PY': 'Year', 'SO': 'Source title',
                   'VL': 'Volume', 'IS': 'Issue', 'CR': 'References', 'BP': 'Page start', 'EP': 'Page end',
                   'PG': 'Page count', 'TC': 'Cited by', 'DI': 'DOI', 'C3': 'Affiliations', 'AB': 'Abstract',
                   'DE': 'Author Keywords', 'ID': 'Index Keywords', 'FX': 'Funding Texts', 'RP': 'Correspondence Address',
                   'PU': 'Publisher', 'SN': 'ISSN', 'LA': 'Language of Original Document',
                   'J9': 'Abbreviated Source Title', 'DT': 'Document Type', 'UT': 'EID', 'C1': 'Authors with affiliations'}

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

        df_final = df_concatenated.copy()

        # ---------------- CONSTRUCCIÓN DE df_author_keywords ----------------
        author_keywords_dict = defaultdict(list)
        for index, row in df_final.iterrows():
            author_keywords = row['Author Keywords'].split(';')
            for position, keyword in enumerate(author_keywords):
                if keyword.strip():
                    author_keywords_dict[keyword.strip()].append((index, position))

        author_keywords_list = []
        author_indices_list = []
        author_posiciones_list = []
        author_conteo_list = []

        for keyword, apariciones in author_keywords_dict.items():
            author_keywords_list.append(keyword)
            indices, posiciones = zip(*apariciones)
            author_indices_list.append(';'.join(map(str, indices)))
            author_posiciones_list.append(';'.join(map(str, posiciones)))
            author_conteo_list.append(len(apariciones))

        df_author_keywords = pd.DataFrame({
            'Author Keyword': author_keywords_list,
            'Indices': author_indices_list,
            'Posiciones': author_posiciones_list,
            'Conteo': author_conteo_list
        })

        # ---------------- GRÁFICA ----------------
        st.subheader("🔑 Top 25 Author Keywords")
        df_sorted = df_author_keywords.sort_values(by='Conteo', ascending=False)
        top_20_keywords = df_sorted.head(25)

        if not top_20_keywords.empty:
            fig, ax = plt.subplots(figsize=(7, 6))
            plt.bar(top_20_keywords['Author Keyword'], top_20_keywords['Conteo'], color='skyblue')
            plt.xlabel('Authors Keywords')
            plt.ylabel('Conteo')
            plt.title('Top 25 Author Keywords')
            plt.xticks(rotation=90)
            plt.tight_layout()
            st.pyplot(fig)
        else:
            st.warning("No hay Author Keywords válidas para mostrar.")
