
import streamlit as st
import pandas as pd
import io
import matplotlib.pyplot as plt
from collections import defaultdict

st.set_page_config(page_title="Fusionador Scopus + WoS", layout="centered")
st.title("Fusionador de archivos bibliográficos: Scopus + WoS")
st.markdown("Sube tus archivos CSV de Scopus y TXT de WoS para fusionarlos, limpiar duplicados y generar tablas de análisis.")

# Subida de archivos
scopus_files = st.file_uploader("Sube archivos CSV de Scopus", type="csv", accept_multiple_files=True)
wos_files = st.file_uploader("Sube archivos TXT de WoS", type="txt", accept_multiple_files=True)

if scopus_files and wos_files:
    if st.button("🔄 Iniciar fusión"):
        dfsco = pd.concat([pd.read_csv(f) for f in scopus_files], ignore_index=True)
        dfsco['Author full names'] = dfsco['Author full names'].str.replace(r'\s*\(\d+\)', '', regex=True)
        dfsco['Source'] = 'scopus'

        campos_multiples = ['AU', 'AF', 'CR']
        registros = []
        for file in wos_files:
            current = {}
            last = None
            lines = file.getvalue().decode('ISO-8859-1').splitlines()
            for line in lines:
                if not line.strip() or line.startswith('EF'):
                    if current:
                        registros.append(current)
                        current = {}
                        last = None
                    continue
                campo = line[:2].strip()
                valor = line[3:].strip()
                if not campo:
                    if last in campos_multiples:
                        current[last] += "; " + valor
                    else:
                        current[last] += " " + valor
                else:
                    if campo in campos_multiples:
                        current[campo] = current.get(campo, "") + "; " + valor if campo in current else valor
                    else:
                        current[campo] = valor
                    last = campo
        dfwos = pd.DataFrame(registros)

        mapping = {'AU': 'Authors', 'AF': 'Author full names','TI': 'Title', 'PY': 'Year',
                   'SO': 'Source title', 'VL': 'Volume', 'IS': 'Issue', 'CR': 'References', 'BP': 'Page start',
                   'EP': 'Page end', 'PG': 'Page count', 'TC': 'Cited by', 'DI': 'DOI',
                   'C3': 'Affiliations', 'AB': 'Abstract', 'DE': 'Author Keywords', 'ID': 'Index Keywords',
                   'FX': 'Funding Texts', 'RP': 'Correspondence Address', 'PU': 'Publisher', 'SN': 'ISSN',
                   'LA': 'Language of Original Document', 'J9': 'Abbreviated Source Title', 'DT': 'Document Type',
                   'UT': 'EID', 'C1': 'Authors with affiliations'}

        dfwos_selected = dfwos.rename(columns=mapping)[list(mapping.values())]
        dfwos_selected['Source'] = 'WOS'
        df_concatenated = pd.concat([dfsco, dfwos_selected], ignore_index=True)
        df_concatenated.fillna('', inplace=True)
        df_concatenated['EID'] = df_concatenated['EID'].astype(str).str.replace('WOS:', '2-w-')

        excepciones = ['Year', 'Cited by', 'Volume', 'Page count', 'Issue', 'Art.No.', 'Page start', 'Page end']
        for col in df_concatenated.columns:
            if col not in excepciones and df_concatenated[col].dtype == 'object':
                df_concatenated[col] = df_concatenated[col].str.lower()

        df_concatenated['References'] = df_concatenated['References'].str.replace(",,", ",")

        df_sin_vacios = df_concatenated[df_concatenated['DOI'] != '']
        duplicados_doi = df_sin_vacios[df_sin_vacios.duplicated(subset=['DOI'], keep=False)]

        indices_doi = set()
        for doi, group in duplicados_doi.groupby('DOI'):
            if 'scopus' in group['Source'].values:
                indices_doi.update(group[group['Source'] != 'scopus'].index)
            else:
                indices_doi.update(group.index[1:])

        duplicados_doi_final = df_concatenated.loc[list(indices_doi)].copy()
        df_concatenated.drop(list(indices_doi), inplace=True, errors='ignore')

        df_concatenated['A_T_Y'] = (
            df_concatenated['Authors'].fillna("").str[:3] +
            df_concatenated['Title'].fillna("").str[:8] +
            df_concatenated['Abstract'].fillna("").str[:6]
        ).str.lower()

        duplicados_sin_doi = df_concatenated[df_concatenated.duplicated(subset=['A_T_Y'], keep=False)]
        indices_sin_doi = set()
        for key, group in duplicados_sin_doi.groupby('A_T_Y'):
            tiene_doi = group['DOI'] != ''
            if tiene_doi.any():
                indices_sin_doi.update(group[~tiene_doi].index)
            else:
                if 'scopus' in group['Source'].values:
                    indices_sin_doi.update(group[group['Source'] != 'scopus'].index)
                else:
                    indices_sin_doi.update(group.index[1:])

        duplicados_sin_doi_final = df_concatenated.loc[list(indices_sin_doi)].copy()
        df_concatenated = df_concatenated.drop(list(indices_sin_doi), errors='ignore')
        df_concatenated.drop(columns=['A_T_Y'], inplace=True)

        df_final = df_concatenated.copy()
        duplicados_final = pd.concat([duplicados_doi_final, duplicados_sin_doi_final], ignore_index=True)

        # Generación de Excel
        buffer1, buffer2, buffer3 = io.BytesIO(), io.BytesIO(), io.BytesIO()
        with pd.ExcelWriter(buffer1, engine='xlsxwriter') as writer:
            df_final.to_excel(writer, sheet_name='Scopus+WOS', index=False)
        with pd.ExcelWriter(buffer2, engine='xlsxwriter') as writer:
            duplicados_final.to_excel(writer, sheet_name='Duplicados', index=False)
        with pd.ExcelWriter(buffer3, engine='xlsxwriter') as writer:
            df_final.head(10).to_excel(writer, sheet_name='Resumen', index=False)

        st.download_button("📥 Descargar: Scopus+WOS.xlsx", buffer1.getvalue(), "Scopus+WOS.xlsx")
        st.download_button("📥 Descargar: Scopus+WOS(duplicados).xlsx", buffer2.getvalue(), "Scopus+WOS(duplicados).xlsx")
        st.download_button("📥 Descargar: Tablas_para_depuraciones.xlsx", buffer3.getvalue(), "Tablas_para_depuraciones.xlsx")

        st.success("¡Fusión finalizada! Archivos generados y disponibles para descarga.")
