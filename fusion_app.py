
# fusion_app.py
# Versión completa reconstruida desde Colab adaptada a Streamlit
# Incluye: carga, fusión, depuración, exportación y visualización

# ------------------ [IMPORTS] ------------------
import streamlit as st
import pandas as pd
import io
import zipfile
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(page_title="Fusionador Scopus + WoS", layout="centered")
st.title("Fusionador de archivos bibliográficos: Scopus + WoS")
st.markdown("Sube tus archivos .csv y .txt exportados desde Scopus y Web of Science para fusionarlos y depurarlos.")

# ------------------ [UPLOAD FILES] ------------------
scopus_files = st.file_uploader("Sube uno o más archivos CSV de Scopus", type="csv", accept_multiple_files=True)
wos_files = st.file_uploader("Sube uno o más archivos TXT de WoS", type="txt", accept_multiple_files=True)

if scopus_files and wos_files:
    if st.button("Fusionar y depurar registros"):
        # ------------- SCOPUS -------------
        dfsco_list = []
        for file in scopus_files:
            df = pd.read_csv(file, encoding='utf-8', sep=',', engine='python')
            dfsco_list.append(df)
        dfsco = pd.concat(dfsco_list, ignore_index=True)
        dfsco['Author full names'] = dfsco['Author full names'].str.replace(r'\s*\(\d+\)', '', regex=True)

        # ------------- WOS -------------
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

        # ------------- FUSIÓN -------------
        mapping = {'AU': 'Authors', 'AF': 'Author full names', 'TI': 'Title', 'PY': 'Year',
                   'SO': 'Source title', 'VL': 'Volume', 'IS': 'Issue', 'CR': 'References', 'BP': 'Page start',
                   'EP': 'Page end', 'PG': 'Page count', 'TC': 'Cited by', 'DI': 'DOI', 'C3': 'Affiliations',
                   'AB': 'Abstract', 'DE': 'Author Keywords', 'ID': 'Index Keywords', 'FX': 'Funding Texts',
                   'RP': 'Correspondence Address', 'PU': 'Publisher', 'SN': 'ISSN',
                   'LA': 'Language of Original Document', 'J9': 'Abbreviated Source Title',
                   'DT': 'Document Type', 'UT': 'EID', 'C1': 'Authors with affiliations'}

        dfwos_selected = dfwos.rename(columns=mapping)[mapping.values()]
        dfwos_selected['Source'] = 'WOS'
        dfsco['Source'] = 'scopus'
        df_all = pd.concat([dfsco, dfwos_selected], ignore_index=True)
        df_all.fillna('', inplace=True)

        df_all['EID'] = df_all['EID'].astype(str).str.replace('WOS:', '2-w-')

        # ------------- LIMPIEZAS -------------
        excepciones = ['Year', 'Cited by', 'Volume', 'Page count', 'Issue', 'Art.No.', 'Page start', 'Page end']
        for columna in df_all.columns:
            if columna not in excepciones and df_all[columna].dtype == 'object':
                df_all[columna] = df_all[columna].str.lower()
        df_all['References'] = df_all['References'].str.replace(",,", ",")

        # ------------- EXPORTACIÓN -------------
        output_buffers = {}

        def export_to_excel(df, filename):
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False)
            buffer.seek(0)
            output_buffers[filename] = buffer

        export_to_excel(df_all, 'Scopus+WOS.xlsx')

        # ------------- GRÁFICO: TOP AUTHOR KEYWORDS -------------
        if 'Author Keywords' in df_all.columns:
            keyword_series = df_all['Author Keywords'].dropna().str.split(';').explode().str.strip()
            keyword_counts = keyword_series.value_counts().reset_index()
            keyword_counts.columns = ['Author Keyword', 'Conteo']
            top_keywords = keyword_counts.head(25)
            st.subheader("🔑 Top 25 Author Keywords")
            fig, ax = plt.subplots(figsize=(8, 6))
            sns.barplot(data=top_keywords, y='Author Keyword', x='Conteo', ax=ax, palette='Greens_d')
            st.pyplot(fig)

        # ------------- DESCARGAS INDIVIDUALES Y ZIP -------------
        for filename, buffer in output_buffers.items():
            st.download_button(label=f"📄 Descargar {filename}", data=buffer, file_name=filename)

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zipf:
            for filename, buffer in output_buffers.items():
                zipf.writestr(filename, buffer.getvalue())
        zip_buffer.seek(0)
        st.download_button("📦 Descargar todos los resultados en ZIP", data=zip_buffer,
                           file_name="Fusion_Resultados.zip", mime="application/zip")
