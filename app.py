
import streamlit as st
import pandas as pd
import io
import matplotlib.pyplot as plt
from collections import defaultdict

st.set_page_config(page_title="Fusionador Scopus + WoS", layout="centered")
st.title("Fusionador de archivos bibliográficos: Scopus + WoS")
st.markdown("Sube tus archivos CSV de Scopus y TXT de WoS para fusionarlos, limpiar duplicados y generar tablas de análisis.")

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

        mapping = {'AU': 'Authors' ,'AF': 'Author full names','TI': 'Title', 'PY': 'Year',
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
        df_concatenated.replace({"‘": "'", "’": "'", "–": "-", "“": '"', "”": '"', "ε": "e", "ℓ": "l", "γ": "y",
                                 ",,": ",", "ï": "i", "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ñ": "n",
                                 "ü": "u", "š": "s", "ř": "r", "ö": "o", "ņ": "n", "ç": "c", "ć": "c", "ş": "s",
                                 "ã": "a", "â": "a", "ń": "n", "ż": "z", "ė": "e", "č": "c", "ß": "B", "ä": "a",
                                 "ê": "e", "ł": "t", "ı": "i", "å": "a", "ą": "a", "ĭ": "i", "ø": "o", "ý": "y",
                                 "≥": ">=", "≤": "<=", "è": "e", "ǐ": "i", "—": "-", "×": "x", "‐": "-"},
                                regex=True, inplace=True)

        df_concatenated['Authors'] = df_concatenated['Authors'].str.replace(".-", ".")
        df_concatenated['Authors'] = df_concatenated['Authors'].str.replace(r'[.,]', '', regex=True)

        df_sin_vacios = df_concatenated[df_concatenated['DOI'] != '']
        duplicados_doi = df_sin_vacios[df_sin_vacios.duplicated(subset=['DOI'], keep=False)]

        indices_a_eliminar_doi = set()
        for doi, group in duplicados_doi.groupby('DOI'):
            if 'scopus' in group['Source'].values:
                indices_a_eliminar_doi.update(group[group['Source'] != 'scopus'].index)
            else:
                indices_a_eliminar_doi.update(group.index[1:])

        duplicados_doi_final = df_concatenated.loc[list(indices_a_eliminar_doi)].copy()
        df_concatenated = df_concatenated.drop(list(indices_a_eliminar_doi), errors='ignore')

        df_concatenated['A_T_Y'] = (
            df_concatenated['Authors'].fillna("").str[:3] +
            df_concatenated['Title'].fillna("").str[:8] +
            df_concatenated['Abstract'].fillna("").str[:6]
        ).str.lower()

        duplicados_sin_doi = df_concatenated[df_concatenated.duplicated(subset=['A_T_Y'], keep=False)]

        indices_a_eliminar_sin_doi = set()
        for key, group in duplicados_sin_doi.groupby('A_T_Y'):
            tiene_doi = group['DOI'] != ''
            if tiene_doi.any():
                indices_a_eliminar_sin_doi.update(group[~tiene_doi].index)
            else:
                if 'scopus' in group['Source'].values:
                    indices_a_eliminar_sin_doi.update(group[group['Source'] != 'scopus'].index)
                else:
                    indices_a_eliminar_sin_doi.update(group.index[1:])

        duplicados_sin_doi_final = df_concatenated.loc[list(indices_a_eliminar_sin_doi)].copy()
        df_concatenated = df_concatenated.drop(list(indices_a_eliminar_sin_doi), errors='ignore')
        df_concatenated.drop(columns=['A_T_Y'], inplace=True)
        df_concatenated_sin_duplicados = df_concatenated.copy()
        duplicados_final = pd.concat([duplicados_doi_final, duplicados_sin_doi_final], ignore_index=True)

        st.success("Fusión completada. Se han eliminado registros duplicados.")
        st.write("Registros finales:", df_concatenated_sin_duplicados.shape[0])
        st.dataframe(df_concatenated_sin_duplicados.head())


        # -------- UNIFICACIÓN DE AUTORES POR ID --------
        def crear_df_conversion(df):
            codigos_autores = {}
            grafia_asignada = {}

            df['Author(s) ID'] = df['Author(s) ID'].fillna('').astype(str)
            df['Authors'] = df['Authors'].fillna('').astype(str)
            df['Author full names'] = df['Author full names'].fillna('').astype(str)

            for index, row in df.iterrows():
                autores = [a.strip() for a in row['Authors'].split(';') if a.strip()]
                nombres_largos = [n.strip() for n in row['Author full names'].split(';') if n.strip()]
                codigos = [c.strip() for c in row['Author(s) ID'].split(';') if c.strip()]

                for autor, nombre_largo, codigo in zip(autores, nombres_largos, codigos):
                    if codigo:
                        if codigo not in codigos_autores:
                            codigos_autores[codigo] = {
                                'autor': autor, 'nombre_largo': nombre_largo,
                                'registros': [], 'posiciones': [], 'articles': 0
                            }
                        codigos_autores[codigo]['registros'].append(index)
                        codigos_autores[codigo]['posiciones'].append(autores.index(autor))
                        codigos_autores[codigo]['articles'] += 1

            autores_ordenados = {}
            for codigo, data in sorted(codigos_autores.items(), key=lambda x: x[1]['articles'], reverse=True):
                nombre_autor = data['autor']
                if nombre_autor not in autores_ordenados:
                    autores_ordenados[nombre_autor] = []
                autores_ordenados[nombre_autor].append((codigo, data))

            for nombre_autor, lista_codigos in autores_ordenados.items():
                for i, (codigo, data_codigos) in enumerate(lista_codigos):
                    nuevo_autor = nombre_autor if i == 0 else f"{nombre_autor}_{i}"
                    grafia_asignada[codigo] = nuevo_autor
                    codigos_autores[codigo]['autor'] = nuevo_autor

            data = []
            for codigo, data_codigos in codigos_autores.items():
                reg_str = ';'.join(str(reg) for reg in data_codigos['registros'])
                pos_str = ';'.join(str(pos) for pos in data_codigos['posiciones'])

                data.append({
                    'Author(s) ID': codigo,
                    'Authors': data_codigos['autor'],
                    'Author full names': data_codigos['nombre_largo'],
                    'Indices': reg_str,
                    'Posiciones': pos_str,
                    'Articles': data_codigos['articles']
                })

            return pd.DataFrame(data)

        def realizar_reemplazos(df, df_conversion):
            total_reemplazos = 0
            for _, row in df_conversion.iterrows():
                registros = [int(reg) for reg in row['Indices'].split(';')]
                posiciones = [int(pos) for pos in row['Posiciones'].split(';')]
                nuevo_autor = row['Authors']

                for registro, posicion in zip(registros, posiciones):
                    autores_viejos = df.at[registro, 'Authors'].split(';')
                    if len(autores_viejos) > posicion:
                        if autores_viejos[posicion] != nuevo_autor:
                            autores_viejos[posicion] = nuevo_autor
                            df.at[registro, 'Authors'] = '; '.join(autores_viejos)
                            total_reemplazos += 1
            return df, total_reemplazos

        df_conversion = crear_df_conversion(df_concatenated_sin_duplicados)
        df_concatenated_sin_duplicados, total_reemplazos = realizar_reemplazos(df_concatenated_sin_duplicados, df_conversion)

        # Autores sin código
        df_autores_sin_cod = df_concatenated_sin_duplicados[df_concatenated_sin_duplicados['Author(s) ID'].str.strip() == ''].copy()
        df_autores_sin_cod['Indices'] = df_autores_sin_cod.index
        df_autores_sin_cod = df_autores_sin_cod.assign(Authors=df_autores_sin_cod['Authors'].str.split(';'),
                                                       Author_full_names=df_autores_sin_cod['Author full names'].str.split(';'))
        df_autores_sin_cod = df_autores_sin_cod.explode(['Authors', 'Author_full_names'])
        df_autores_sin_cod['Authors'] = df_autores_sin_cod['Authors'].str.strip()
        df_autores_sin_cod['Author_full_names'] = df_autores_sin_cod['Author_full_names'].str.strip()
        df_autores_sin_cod['Posiciones'] = df_autores_sin_cod.groupby(['Authors', 'Author_full_names']).cumcount()
        df_autores_sin_cod['Articles'] = df_autores_sin_cod.groupby(['Authors', 'Author_full_names'])['Authors'].transform('count')
        df_autores_sin_cod = df_autores_sin_cod.groupby(['Authors', 'Author_full_names']).agg({
            'Indices': lambda x: '; '.join(map(str, x)),
            'Posiciones': lambda x: '; '.join(map(str, x)),
            'Articles': 'first'
        }).reset_index()

        autores = df_conversion[['Authors', 'Author full names', 'Author(s) ID', 'Indices', 'Posiciones', 'Articles']].copy()
        autores['Authors'] = autores['Authors'].str.strip()
        autores = pd.concat([
            autores,
            df_autores_sin_cod.rename(columns={'Author_full_names': 'Author full names'})
        ], ignore_index=True)
        autores['New Author'] = '0-change-0'

        # --- Author Keywords ---
        author_keywords_dict = defaultdict(list)
        for index, row in df_concatenated_sin_duplicados.iterrows():
            for position, keyword in enumerate(row['Author Keywords'].split(';')):
                if keyword.strip():
                    author_keywords_dict[keyword.strip()].append((index, position))

        df_author_keywords = pd.DataFrame([
            {
                'Author Keyword': kw,
                'Indices': ';'.join(map(str, zip(*v)[0])),
                'Posiciones': ';'.join(map(str, zip(*v)[1])),
                'Conteo': len(v)
            }
            for kw, v in author_keywords_dict.items()
        ])
        df_author_keywords['New Keyword'] = '0-change-0'

        # --- Index Keywords ---
        index_keywords_dict = defaultdict(list)
        for index, row in df_concatenated_sin_duplicados.iterrows():
            for position, keyword in enumerate(row['Index Keywords'].split(';')):
                if keyword.strip():
                    index_keywords_dict[keyword.strip()].append((index, position))

        df_index_keywords = pd.DataFrame([
            {
                'Index Keywords': kw,
                'Indices': ';'.join(map(str, zip(*v)[0])),
                'Posiciones': ';'.join(map(str, zip(*v)[1])),
                'Conteo': len(v)
            }
            for kw, v in index_keywords_dict.items()
        ])
        df_index_keywords['New Keyword'] = '0-change-0'

        # --- Cited References ---
        references_dict = defaultdict(list)
        for index, row in df_concatenated_sin_duplicados.iterrows():
            for position, reference in enumerate(row['References'].split(';')):
                if reference.strip():
                    references_dict[reference.strip()].append((index, position))

        df_references_info = pd.DataFrame([
            {
                'References': ref,
                'Indices': ';'.join(map(str, zip(*v)[0])),
                'Posiciones': ';'.join(map(str, zip(*v)[1])),
                'Count': len(v)
            }
            for ref, v in references_dict.items()
        ])
        df_references_info['New Reference'] = '0-change-0'

        # --- Export final Excel con varias hojas ---
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            autores.to_excel(writer, sheet_name='Authors', index=False)
            df_author_keywords.to_excel(writer, sheet_name='Author Keywords', index=False)
            df_index_keywords.to_excel(writer, sheet_name='Index Keywords', index=False)
            df_references_info.to_excel(writer, sheet_name='Cited References', index=False)

        st.download_button("📥 Descargar: Tablas_para_depuraciones.xlsx", output.getvalue(), "Tablas_para_depuraciones.xlsx")

        # --- Informes e Histogramas ---
        st.subheader("📊 Top 20 autores con más artículos")
        top_autores = autores.sort_values(by='Articles', ascending=False).head(20)
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.bar(top_autores['Authors'], top_autores['Articles'])
        ax.set_title('Top 20 Autores con Más Artículos')
        ax.set_xticklabels(top_autores['Authors'], rotation=90)
        st.pyplot(fig)

        st.subheader("📊 Top 25 Author Keywords")
        top_kw = df_author_keywords.sort_values(by='Conteo', ascending=False).head(25)
        fig_kw, ax_kw = plt.subplots(figsize=(7, 5))
        ax_kw.bar(top_kw['Author Keyword'], top_kw['Conteo'])
        ax_kw.set_xticklabels(top_kw['Author Keyword'], rotation=90)
        ax_kw.set_title("Top 25 Author Keywords")
        st.pyplot(fig_kw)

        st.subheader("📊 Top 25 Index Keywords")
        top_idx = df_index_keywords.sort_values(by='Conteo', ascending=False).head(25)
        fig_idx, ax_idx = plt.subplots(figsize=(7, 5))
        ax_idx.bar(top_idx['Index Keywords'], top_idx['Conteo'])
        ax_idx.set_xticklabels(top_idx['Index Keywords'], rotation=90)
        ax_idx.set_title("Top 25 Index Keywords")
        st.pyplot(fig_idx)
