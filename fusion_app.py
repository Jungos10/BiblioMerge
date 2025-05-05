
# fusion_app.py
import streamlit as st
import pandas as pd
import io

# Configuración inicial de la app
st.set_page_config(page_title="Fusionador Scopus + WoS", layout="centered")

# Título y descripción de la aplicación
st.title("Fusionador de archivos bibliográficos: Scopus + WoS")
st.markdown("Sube tus archivos .csv y .txt exportados desde Scopus y Web of Science para fusionarlos y depurarlos.")

# ----------- CARGA DE ARCHIVOS ------------
# Cargar archivos CSV de Scopus (permite múltiples)
scopus_files = st.file_uploader("Sube uno o más archivos CSV de Scopus", type="csv", accept_multiple_files=True)

# Cargar archivos TXT de WoS (permite múltiples)
wos_files = st.file_uploader("Sube uno o más archivos TXT de WoS", type="txt", accept_multiple_files=True)

# ----------- PROCESAMIENTO DE SCOPUS ------------
if scopus_files:
    dfsco_list = []
    for file in scopus_files:
        # Leer cada archivo CSV con el encoding y separador adecuado
        df = pd.read_csv(file, encoding='utf-8', sep=',', engine='python')
        dfsco_list.append(df)
    # Concatenar todos los DataFrames en uno solo
    dfsco = pd.concat(dfsco_list, ignore_index=True)
    # Limpiar los nombres de autor quitando los IDs entre paréntesis
    if 'Author full names' in dfsco.columns:
        dfsco['Author full names'] = dfsco['Author full names'].str.replace(r'\s*\(\d+\)', '', regex=True)
    # Mensaje de éxito y vista previa
    st.success(f"Archivos CSV de Scopus cargados correctamente: {len(scopus_files)} archivo(s), {dfsco.shape[0]} registros.")
    # st.dataframe(dfsco.head())  # Eliminado para evitar mostrar los datos

# ----------- PROCESAMIENTO DE WOS ------------

# ----------- FUSIÓN Y LIMPIEZA DE DATOS ------------
if wos_files:
    campos_multiples = ['AU', 'AF', 'CR']  # Campos que deben unirse con punto y coma
    todos_registros = []
    for file in wos_files:
        registros = []
        registro_actual = {}
        ultimo_campo = None
        # Leer contenido del archivo con codificación adecuada
        lines = file.getvalue().decode('ISO-8859-1').splitlines()
        for linea in lines:
            # Detectar fin de registro
            if not linea.strip() or linea.startswith('EF'):
                if registro_actual:
                    registros.append(registro_actual)
                    registro_actual = {}
                    ultimo_campo = None
                continue
            # Separar campo y valor
            campo = linea[:2].strip()
            valor = linea[3:].strip()
            if not campo:
                # Continuación del campo anterior
                if ultimo_campo in campos_multiples:
                    registro_actual[ultimo_campo] += "; " + valor
                else:
                    registro_actual[ultimo_campo] += " " + valor
            else:
                # Campo nuevo
                if campo in campos_multiples:
                    if campo in registro_actual:
                        registro_actual[campo] += "; " + valor
                    else:
                        registro_actual[campo] = valor
                else:
                    registro_actual[campo] = valor
                ultimo_campo = campo
        # Añadir todos los registros del archivo
        todos_registros.extend(registros)
    # Convertir lista de registros en DataFrame
    dfwos = pd.DataFrame(todos_registros)
    # Mensaje de éxito y vista previa
    st.success(f"Archivos TXT de WoS cargados correctamente: {len(wos_files)} archivo(s), {dfwos.shape[0]} registros.")
    # st.dataframe(dfwos.head())  # Eliminado para evitar mostrar los datos

    # Una vez cargados ambos, mostramos botón para continuar con la fusión
if 'dfsco' in locals() and 'dfwos' in locals():
    if st.button("Fusionar y depurar registros"):
        # Aquí irá la lógica de mapeo, fusión, limpieza y deduplicación
        st.info("🔧 Procesando y fusionando registros. Esto puede tardar unos segundos...")
        # ----------- MAPEO Y FUSIÓN INICIAL -----------
        mapping = {
            'AU': 'Authors', 'AF': 'Author full names', 'TI': 'Title', 'PY': 'Year',
            'SO': 'Source title', 'VL': 'Volume', 'IS': 'Issue', 'CR': 'References', 'BP': 'Page start',
            'EP': 'Page end', 'PG': 'Page count', 'TC': 'Cited by', 'DI': 'DOI',
            'C3': 'Affiliations', 'AB': 'Abstract', 'DE': 'Author Keywords', 'ID': 'Index Keywords',
            'FX': 'Funding Texts', 'RP': 'Correspondence Address',
            'PU': 'Publisher', 'SN': 'ISSN', 'LA': 'Language of Original Document',
            'J9': 'Abbreviated Source Title', 'DT': 'Document Type', 'UT': 'EID', 'C1': 'Authors with affiliations'
        }

        dfwos_selected = dfwos.rename(columns=mapping)[list(mapping.values())]
        dfwos_selected['Source'] = 'wos'
        dfsco['Source'] = 'scopus'

        df_concatenated = pd.concat([dfsco, dfwos_selected], ignore_index=True)
        df_concatenated.fillna('', inplace=True)

        df_concatenated['EID'] = df_concatenated['EID'].astype(str).str.replace('WOS:', '2-w-')

        excepciones = ['Year', 'Cited by', 'Volume', 'Page count', 'Issue', 'Art.No.', 'Page start', 'Page end']
        for columna in df_concatenated.columns:
            if columna not in excepciones and df_concatenated[columna].dtype == 'object':
                df_concatenated[columna] = df_concatenated[columna].str.lower()

        df_concatenated['References'] = df_concatenated['References'].str.replace(",,", ",")

        reemplazos = {
            "‘": "'", "’": "'", "–": "-", "“": '"', "”": '"', "ε": "e", "ℓ": "l", "γ": "y", "ï": "i",
            "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ñ": "n", "ü": "u", "š": "s", "ř": "r", "ö": "o",
            "ņ": "n", "ç": "c", "ć": "c", "ş": "s", "ã": "a", "â": "a", "ń": "n", "ż": "z", "ė": "e", "č": "c",
            "ß": "B", "ä": "a", "ê": "e", "ł": "t", "ı": "i", "å": "a", "ą": "a", "ĭ": "i", "ø": "o", "ý": "y",
            "≥": ">=", "≤": "<=", "è": "e", "ǐ": "i", "—": "-", "×": "x", "‐": "-"
        }
        df_concatenated.replace(reemplazos, regex=True, inplace=True)

        df_concatenated['Authors'] = df_concatenated['Authors'].str.replace(".-", ".")
        df_concatenated['Authors'] = df_concatenated['Authors'].str.replace(r'[.,]', '', regex=True)

        st.success("✔️ Datos fusionados y normalizados correctamente. Próximo paso: eliminación de duplicados y depuración avanzada...")
        # ----------- ELIMINACIÓN DE DUPLICADOS -----------
        # Duplicados con DOI
        df_sin_vacios = df_concatenated[df_concatenated['DOI'] != '']
        duplicados_doi = df_sin_vacios[df_sin_vacios.duplicated(subset=['DOI'], keep=False)]
        indices_a_eliminar_doi = set()
        for doi, group in duplicados_doi.groupby('DOI'):
            if 'scopus' in group['Source'].values:
                indices_a_eliminar_doi.update(group[group['Source'] != 'scopus'].index)
            else:
                indices_a_eliminar_doi.update(group.index[1:])
        duplicados_doi_final = df_concatenated.loc[df_concatenated.index.isin(indices_a_eliminar_doi)].copy()
        df_concatenated = df_concatenated.drop(list(indices_a_eliminar_doi), errors='ignore')

        # Duplicados sin DOI
        df_concatenated['A_T_Y'] = (
            df_concatenated['Authors'].fillna('').str[:3] +
            df_concatenated['Title'].fillna('').str[:8] +
            df_concatenated['Abstract'].fillna('').str[:6]
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
        duplicados_sin_doi_final = df_concatenated.loc[df_concatenated.index.isin(indices_a_eliminar_sin_doi)].copy()
        df_concatenated = df_concatenated.drop(list(indices_a_eliminar_sin_doi), errors='ignore')
        df_concatenated.drop(columns=['A_T_Y'], inplace=True)

        df_concatenated_sin_duplicados = df_concatenated.copy()
        duplicados_final = pd.concat([duplicados_doi_final, duplicados_sin_doi_final], ignore_index=True)

        st.success(f"✔️ Eliminación de duplicados completada. Registros finales: {df_concatenated_sin_duplicados.shape[0]}")

        # ----------- NORMALIZACIÓN DE AUTORES -----------
        codigos_autores = {}
        grafia_asignada = {}
        df = df_concatenated_sin_duplicados.copy()
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
            secuencia = 0
            for i, (codigo, data_codigos) in enumerate(lista_codigos):
                nuevo_autor = nombre_autor if i == 0 else f"{nombre_autor}_{secuencia}"; secuencia += 1
                grafia_asignada[codigo] = nuevo_autor
                codigos_autores[codigo]['autor'] = nuevo_autor
        data_autores = []
        for codigo, data_codigos in codigos_autores.items():
            reg_str = ';'.join(str(reg) for reg in data_codigos['registros'])
            pos_str = ';'.join(str(pos) for pos in data_codigos['posiciones'])
            data_autores.append({
                'Author(s) ID': codigo,
                'Authors': data_codigos['autor'],
                'Author full names': data_codigos['nombre_largo'],
                'Indices': reg_str,
                'Posiciones': pos_str,
                'Articles': data_codigos['articles']
            })
        df_conversion = pd.DataFrame(data_autores)
        total_reemplazos = 0
        for _, row in df_conversion.iterrows():
            registros = [int(r) for r in row['Indices'].split(';')]
            posiciones = [int(p) for p in row['Posiciones'].split(';')]
            nuevo_autor = row['Authors']
            for reg, pos in zip(registros, posiciones):
                autores_viejos = df.at[reg, 'Authors'].split(';')
                if len(autores_viejos) > pos and autores_viejos[pos] != nuevo_autor:
                    autores_viejos[pos] = nuevo_autor
                    df.at[reg, 'Authors'] = '; '.join(autores_viejos)
                    total_reemplazos += 1

        # ----------- CREACIÓN DE TABLAS DE KEYWORDS -----------
        from collections import defaultdict
        def crear_tabla_keywords(columna):
            keywords_dict = defaultdict(list)
            for idx, row in df.iterrows():
                keywords = row[columna].split(';')
                for i, k in enumerate(keywords):
                    if k.strip():
                        keywords_dict[k.strip()].append((idx, i))
            keyword_list, index_list, pos_list, count_list = [], [], [], []
            for k, apariciones in keywords_dict.items():
                index_str = ';'.join(str(x[0]) for x in apariciones)
                pos_str = ';'.join(str(x[1]) for x in apariciones)
                keyword_list.append(k)
                index_list.append(index_str)
                pos_list.append(pos_str)
                count_list.append(len(apariciones))
            return pd.DataFrame({
                columna: keyword_list,
                'Indices': index_list,
                'Posiciones': pos_list,
                'Conteo': count_list,
                'New Keyword': ['0-change-0'] * len(keyword_list)
            })

        df_author_keywords = crear_tabla_keywords('Author Keywords')
        df_index_keywords = crear_tabla_keywords('Index Keywords')

        # ----------- REFERENCIAS -----------
        references_dict = defaultdict(list)
        for idx, row in df.iterrows():
            refs = row['References'].split(';')
            for i, r in enumerate(refs):
                if r.strip():
                    references_dict[r.strip()].append((idx, i))
        ref_list, idx_list, pos_list, count_list = [], [], [], []
        for ref, apariciones in references_dict.items():
            idx_str = ';'.join(str(x[0]) for x in apariciones)
            pos_str = ';'.join(str(x[1]) for x in apariciones)
            ref_list.append(ref)
            idx_list.append(idx_str)
            pos_list.append(pos_str)
            count_list.append(len(apariciones))
        df_references_info = pd.DataFrame({
            'References': ref_list,
            'Indices': idx_list,
            'Posiciones': pos_list,
            'Count': count_list,
            'New Reference': ['0-change-0'] * len(ref_list)
        })

        st.success("✔️ Autores normalizados y tablas de keywords y referencias generadas.")

        # ----------- CREACIÓN DE df_final Y CONVERSIÓN DE TIPOS -----------
        df_final = df.copy()
        cols_numericas = ['Volume', 'Cited by', 'Page count', 'Year']
        df_final[cols_numericas] = df_final[cols_numericas].apply(pd.to_numeric, errors='coerce').fillna(0).astype(int)

        # ----------- OPCIONES DE EXPORTACIÓN -----------
        import tempfile
        import xlsxwriter

        if st.button("📥 Descargar resultados como Excel"):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
                with pd.ExcelWriter(tmp.name, engine='xlsxwriter') as writer:
                    df_final.to_excel(writer, sheet_name='Scopus+WoS', index=False)
                    duplicados_final.to_excel(writer, sheet_name='Duplicados eliminados', index=False)
                    df_conversion.to_excel(writer, sheet_name='Autores', index=False)
                    df_author_keywords.to_excel(writer, sheet_name='Author Keywords', index=False)
                    df_index_keywords.to_excel(writer, sheet_name='Index Keywords', index=False)
                    df_references_info.to_excel(writer, sheet_name='Cited References', index=False)
                tmp_path = tmp.name
            with open(tmp_path, "rb") as f:
                st.download_button(
                    label="📄 Descargar Excel fusionado",
                    data=f,
                    file_name="Fusion_Scopus_WoS_Resultados.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

        # ----------- INFORMES RESUMIDOS -----------
        st.subheader("📊 Informe de la Fusión")
        st.markdown(f"**Registros Scopus:** {dfsco.shape[0]}  |  **Columnas Scopus:** {dfsco.shape[1]}")
        st.markdown(f"**Registros WoS:** {dfwos.shape[0]}  |  **Columnas WoS:** {dfwos.shape[1]}")
        st.markdown(f"**Duplicados eliminados:** {duplicados_final.shape[0]}  |  Sin DOI: {duplicados_sin_doi.shape[0]}")
        st.markdown(f"**Registros finales:** {df_final.shape[0]}  |  **Columnas finales:** {df_final.shape[1]}")

        st.subheader("👤 Top 20 Autores con más artículos")
        import matplotlib.pyplot as plt
        import seaborn as sns
        top_autores = df_conversion.sort_values(by='Articles', ascending=False).head(20)
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.barplot(data=top_autores, y='Authors', x='Articles', ax=ax, palette='Blues_d')
        ax.set_xlabel('Número de Artículos')
        ax.set_ylabel('Autor')
        ax.set_title('Top 20 Autores con Más Artículos')
        st.pyplot(fig)

        st.subheader("🔑 Top 25 Author Keywords")
        top_keywords = df_author_keywords.sort_values(by='Conteo', ascending=False).head(25)
        fig2, ax2 = plt.subplots(figsize=(8, 6))
        sns.barplot(data=top_keywords, y='Author Keyword', x='Conteo', ax=ax2, palette='Greens_d')
        ax2.set_xlabel('Conteo')
        ax2.set_ylabel('Author Keyword')
        ax2.set_title('Principales Author Keywords')
        st.pyplot(fig2)

        st.markdown(f"**Total Author Keywords (sin depurar):** {df_author_keywords.shape[0]}")
        st.markdown(f"**Total Index Keywords (sin depurar):** {df_index_keywords.shape[0]}")

        st.subheader("🔍 Top 25 Index Keywords")
        top_index_keywords = df_index_keywords.sort_values(by='Conteo', ascending=False).head(25)
        fig3, ax3 = plt.subplots(figsize=(8, 6))
        sns.barplot(data=top_index_keywords, y='Index Keywords', x='Conteo', ax=ax3, palette='Purples_d')
        ax3.set_xlabel('Conteo')
        ax3.set_ylabel('Index Keyword')
        ax3.set_title('Principales Index Keywords')
        st.pyplot(fig3)
