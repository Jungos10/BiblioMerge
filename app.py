# -------------------- PARTE 1: CARGAR FICHEROS --------------------

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from collections import defaultdict
import io
import time  # <- necesario para el spinner

# Configuración inicial
st.set_page_config(page_title="Fusionador Scopus + WoS", layout="centered")
st.title("Fusionador de archivos bibliográficos: Scopus + WoS")
st.markdown("Sube tus archivos CSV de Scopus y TXT de WoS para fusionarlos y generar informes.")

# 🔁 Botón de reinicio global
st.markdown("#### ")
col_reset = st.columns([5, 1])[1]
with col_reset:
    if st.button("🔁 Reiniciar todo", key="btn_reset", type="primary", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# Inicializar estados
if "procesado" not in st.session_state:
    st.session_state["procesado"] = False
if "fusion_en_proceso" not in st.session_state:
    st.session_state["fusion_en_proceso"] = False

# BLOQUE 1 – Subida de archivos y botón de inicio (solo si no se ha procesado)
if not st.session_state["procesado"]:
    scopus_files = st.file_uploader("Sube archivos Scopus (CSV)", type="csv", accept_multiple_files=True)
    wos_files = st.file_uploader("Sube archivos WoS (TXT)", type="txt", accept_multiple_files=True)

    if scopus_files:
        st.markdown(f"**📄 Archivos Scopus cargados ({len(scopus_files)}):**")
        for f in scopus_files:
            st.markdown(f"- {f.name}")
    if wos_files:
        st.markdown(f"**📄 Archivos WoS cargados ({len(wos_files)}):**")
        for f in wos_files:
            st.markdown(f"- {f.name}")

    col1, _ = st.columns([1, 1])
    with col1:
        if st.button("🔄 Iniciar fusión", key="btn_iniciar", use_container_width=True):
            if scopus_files and wos_files:
                st.session_state["scopus_files"] = scopus_files
                st.session_state["wos_files"] = wos_files
                st.session_state["fusion_en_proceso"] = True
                st.session_state["procesado"] = True
                st.rerun()
            else:
                st.warning("Debes cargar archivos de Scopus y WoS antes de iniciar.")

# BLOQUE 2 – Fusión de archivos con spinner y mensajes
if st.session_state["procesado"]:
    if st.session_state["fusion_en_proceso"]:
        st.info("✅ Fusión iniciada correctamente. Procesando datos...")

        with st.spinner("🔄 Fusionando archivos y limpiando registros..."):
            time.sleep(0.1)  # Forzar visualización del spinner

            scopus_files = st.session_state["scopus_files"]
            wos_files = st.session_state["wos_files"]

            # --- SCOPUS ---
            dfsco_list = []
            for file in scopus_files:
                df = pd.read_csv(file)
                dfsco_list.append(df)
            dfsco = pd.concat(dfsco_list, ignore_index=True)
            dfsco['Author full names'] = dfsco['Author full names'].str.replace(r'\s*\(\d+\)', '', regex=True)
            dfsco['Source'] = 'scopus'

                       
            # --- WoS ---
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

            # Guardamos los originales para informes
            st.session_state["dfsco"] = dfsco
            st.session_state["dfwos"] = dfwos
        

        # ✅ Fusión finalizada
        st.session_state["fusion_en_proceso"] = False
       



# -------------------- PARTE 2: FUSIÓN, INFORMES PRELIMINARES Y TABLAS DEPURACIÓN --------------------
    
    # ---------IMPORTAMOS AMBOS ARCHIVOS, MAPEAMOS, Y LOS UNIMOS. ADECUAMOS UN CAMPO DE IDENTIFICACIÓN Y LIMPIAMOS CAMPOS CON 'NaN'-----

    # Mapeamos el archivo WOS(dfwos) con el archivo Scopus (dfsco)
    mapping = {'AU': 'Authors' ,'AF': 'Author full names','TI': 'Title', 'PY': 'Year',
               'SO': 'Source title', 'VL': 'Volume', 'IS': 'Issue', 'CR': 'References', 'BP': 'Page start',
               'EP': 'Page end', 'PG': 'Page count', 'TC': 'Cited by', 'DI': 'DOI',
               'C3': 'Affiliations', 'AB': 'Abstract', 'DE': 'Author Keywords', 'ID': 'Index Keywords',
               'FX': 'Funding Texts', 'RP': 'Correspondence Address',
               'PU': 'Publisher', 'SN': 'ISSN', 'LA': 'Language of Original Document',
               'J9': 'Abbreviated Source Title', 'DT': 'Document Type', 'UT': 'EID', 'C1': 'Authors with affiliations'}


    # ✅ Asegurarse de que dfwos está disponible
    if "dfwos" not in locals():
        if "dfwos" in st.session_state:
            dfwos = st.session_state["dfwos"]
        else:
            st.error("❌ El DataFrame dfwos no está disponible. Ejecuta la fusión primero.")
            st.stop()
      
    dfwos_selected = dfwos.rename(columns=mapping)
    dfwos_selected = dfwos_selected[[col for col in mapping.values() if col in dfwos_selected.columns]]
    dfwos_selected['Source'] = 'WOS'
           
    df_concatenated = pd.concat([dfsco, dfwos_selected], ignore_index=True)
    df_concatenated.fillna('', inplace=True)

    df_concatenated['EID'] = (
        df_concatenated['EID']
        .astype(str)
        .str.replace('WOS:', '2-w-')
    )

    # Transformar todo en minúsculas salvo excepciones
    excepciones = ['Year', 'Cited by', 'Volume', 'Page count', 'Issue', 'Art.No.', 'Page start', 'Page end']
    for columna in df_concatenated.columns:
        if columna not in excepciones and df_concatenated[columna].dtype == 'object':
            df_concatenated[columna] = df_concatenated[columna].str.lower()

    df_concatenated['References'] = df_concatenated['References'].str.replace(",,", ",")

    # Reemplazos de caracteres problemáticos
    sustituciones = {
        "‘": "'", "’": "'", "–": "-", "“": '"', "”": '"', "ε": "e", "ℓ": "l", "γ": "y", ",,": ",",
        "ï": "i", "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ñ": "n", "ü": "u", "š": "s",
        "ř": "r", "ö": "o", "ņ": "n", "ç": "c", "ć": "c", "ş": "s", "ã": "a", "â": "a", "ń": "n",
        "ż": "z", "ė": "e", "č": "c", "ß": "B", "ä": "a", "ê": "e", "ł": "t", "ı": "i", "å": "a",
        "ą": "a", "ĭ": "i", "ø": "o", "ý": "y", "≥": ">=", "≤": "<=", "è": "e", "ǐ": "i", "—": "-",
        "×": "x", "‐": "-"
    }
    for old, new in sustituciones.items():
        df_concatenated.replace(old, new, regex=True, inplace=True)

    # Limpieza adicional de 'Authors'
    df_concatenated['Authors'] = df_concatenated['Authors'].str.replace(".-", ".")
    df_concatenated['Authors'] = df_concatenated['Authors'].str.replace(r'[.,]', '', regex=True)


    # ----- FASE 1: Eliminación de duplicados con DOI -----
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

    # ----- FASE 2: Eliminación de duplicados sin DOI -----
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
    duplicados_sin_doi_final = df_concatenated.loc[df_concatenated.index.isin(indices_a_eliminar_sin_doi)].copy()
    df_concatenated = df_concatenated.drop(list(indices_a_eliminar_sin_doi), errors='ignore')
    df_concatenated.drop(columns=['A_T_Y'], inplace=True)

    df_concatenated_sin_duplicados = df_concatenated.copy()
    duplicados_final = pd.concat([duplicados_doi_final, duplicados_sin_doi_final], ignore_index=True)


    # --------IDENTIFICAMOS AUTORES CON DIFERENTE GRAFÍA Y UNIFICAMOS EN UNA ÚNICA GRAFÍA---------------------
    def crear_df_conversion(df):
        codigos_autores = {}
        grafia_asignada = {}

        df['Author(s) ID'] = df['Author(s) ID'].fillna('').astype(str)
        df['Authors'] = df['Authors'].fillna('').astype(str)
        df['Author full names'] = df['Author full names'].fillna('').astype(str)

        for index, row in df.iterrows():
            autores = [autor.strip() for autor in row['Authors'].split(';') if autor.strip()]
            nombres_largos = [nombre.strip() for nombre in row['Author full names'].split(';') if nombre.strip()]
            codigos = [codigo.strip() for codigo in row['Author(s) ID'].split(';') if codigo.strip()]

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
                if i == 0:
                    nuevo_autor = nombre_autor
                else:
                    secuencia += 1
                    nuevo_autor = f"{nombre_autor}_{secuencia}"

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

    df_autores_sin_cod = df_concatenated_sin_duplicados[df_concatenated_sin_duplicados['Author(s) ID'].apply(lambda x: str(x).strip()) == ''].copy()
    df_autores_sin_cod['Indices'] = df_autores_sin_cod.index

    df_autores_sin_cod = df_autores_sin_cod.assign(Authors=df_autores_sin_cod['Authors'].str.split(';'),
                                                   Author_full_names=df_autores_sin_cod['Author full names'].str.split(';'))
    df_autores_sin_cod = df_autores_sin_cod.explode(['Authors', 'Author_full_names'])
    df_autores_sin_cod['Authors'] = df_autores_sin_cod['Authors'].str.strip()
    df_autores_sin_cod['Author_full_names'] = df_autores_sin_cod['Author_full_names'].str.strip()
    df_autores_sin_cod['Posiciones'] = df_autores_sin_cod.groupby(['Authors', 'Author_full_names']).cumcount()
    df_autores_sin_cod['Articles'] = df_autores_sin_cod.groupby(['Authors', 'Author_full_names'])['Authors'].transform('count')

    df_autores_sin_cod = df_autores_sin_cod.groupby(['Authors', 'Author_full_names']).agg(
        {'Indices': lambda x: '; '.join(map(str, x)), 'Posiciones': lambda x: '; '.join(map(str, x)), 'Articles': 'first'}
    ).reset_index()

    autores = df_conversion[['Authors', 'Author full names', 'Author(s) ID', 'Indices', 'Posiciones', 'Articles']].copy()
    autores['Authors'] = autores['Authors'].str.strip()
    autores = pd.concat([autores, df_autores_sin_cod.rename(columns={'Author_full_names': 'Author full names'})], ignore_index=True)
    autores['New Author'] = '0-change-0'


    from collections import defaultdict

    # -------- AUTHOR KEYWORDS ----------
    author_keywords_dict = defaultdict(list)
    for index, row in df_concatenated_sin_duplicados.iterrows():
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
        indices_str = ';'.join(map(str, indices))
        posiciones_str = ';'.join(map(str, posiciones))
        author_indices_list.append(indices_str)
        author_posiciones_list.append(posiciones_str)
        author_conteo_list.append(len(apariciones))

    df_author_keywords = pd.DataFrame({
        'Author Keyword': author_keywords_list,
        'Indices': author_indices_list,
        'Posiciones': author_posiciones_list,
        'Conteo': author_conteo_list
    })
    df_author_keywords['New Keyword'] = '0-change-0'

    # -------- INDEX KEYWORDS ----------
    index_keywords_dict = defaultdict(list)
    for index, row in df_concatenated_sin_duplicados.iterrows():
        index_keywords = row['Index Keywords'].split(';')
        for position, keyword in enumerate(index_keywords):
            if keyword.strip():
                index_keywords_dict[keyword.strip()].append((index, position))

    index_keywords_list = []
    index_indices_list = []
    index_posiciones_list = []
    index_conteo_list = []

    for keyword, apariciones in index_keywords_dict.items():
        index_keywords_list.append(keyword)
        indices, posiciones = zip(*apariciones)
        index_indices_list.append(';'.join(map(str, indices)))
        index_posiciones_list.append(';'.join(map(str, posiciones)))
        index_conteo_list.append(len(apariciones))

    df_index_keywords = pd.DataFrame({
        'Index Keywords': index_keywords_list,
        'Indices': index_indices_list,
        'Posiciones': index_posiciones_list,
        'Conteo': index_conteo_list
    })
    df_index_keywords['New Keyword'] = '0-change-0'

    # -------- CITED REFERENCES ----------
    references_dict = defaultdict(list)
    for index, row in df_concatenated_sin_duplicados.iterrows():
        references = row['References'].split(';')
        for position, reference in enumerate(references):
            if reference.strip():
                references_dict[reference.strip()].append((index, position))

    reference_list = []
    indices_list = []
    positions_list = []
    count_list = []

    for reference, apariciones in references_dict.items():
        reference_list.append(reference)
        indices, posiciones = zip(*apariciones)
        indices_list.append(';'.join(map(str, indices)))
        positions_list.append(';'.join(map(str, posiciones)))
        count_list.append(len(apariciones))

    df_references_info = pd.DataFrame({
        'References': reference_list,
        'Indices': indices_list,
        'Posiciones': positions_list,
        'Count': count_list
    })
    df_references_info['New Reference'] = '0-change-0'


    df_final = df_concatenated_sin_duplicados.copy()

    # Convertir campos numéricos y rellenar vacíos
    df_final[['Volume', 'Cited by', 'Page count', 'Year']] = df_final[['Volume', 'Cited by', 'Page count', 'Year']].apply(pd.to_numeric, errors='coerce')
    df_final[['Volume', 'Cited by', 'Page count', 'Year']] = df_final[['Volume', 'Cited by', 'Page count', 'Year']].fillna(0)
    df_final[['Volume', 'Cited by', 'Page count', 'Year']] = df_final[['Volume', 'Cited by', 'Page count', 'Year']].astype(int)

    # Guardar en session_state para uso en informes/pestañas
    st.session_state["df_final"] = df_final
    st.session_state["duplicados_final"] = duplicados_final
    st.session_state["duplicados_sin_doi_final"] = duplicados_sin_doi_final

    # Señalamos que la fusión ya terminó
    st.session_state["fusion_en_proceso"] = False
    st.rerun()
        
    # Generación de archivos Excel para descarga
    import io

    output_fusion = io.BytesIO()
    output_duplicados = io.BytesIO()
    output_tablas = io.BytesIO()

    # Fichero Scopus+WOS
    with pd.ExcelWriter(output_fusion, engine='xlsxwriter') as writer:
        df_final.to_excel(writer, index=False)

    # Fichero de duplicados
    with pd.ExcelWriter(output_duplicados, engine='xlsxwriter') as writer:
        duplicados_final.to_excel(writer, index=False)

    # Fichero de tablas para depuración
    with pd.ExcelWriter(output_tablas, engine='xlsxwriter') as writer:
        autores.to_excel(writer, sheet_name='Authors', index=False)
        df_author_keywords.to_excel(writer, sheet_name='Author Keywords', index=False)
        df_index_keywords.to_excel(writer, sheet_name='Index Keywords', index=False)
        df_references_info.to_excel(writer, sheet_name='Cited References', index=False)

    # # Streamlit download buttons
    # st.download_button("📥 Descargar Scopus+WOS.xlsx", output_fusion.getvalue(), "Scopus+WOS.xlsx")
    # st.download_button("📥 Descargar duplicados eliminados", output_duplicados.getvalue(), "Scopus+WOS(duplicados).xlsx")
    # st.download_button("📥 Descargar Tablas_para_depuraciones.xlsx", output_tablas.getvalue(), "Tablas_para_depuraciones.xlsx")


    # # -------- INFORMES Y VISUALIZACIONES --------
    # st.subheader("📊 Información de la fusión")

    # st.markdown(f"- Registros Scopus: **{dfsco.shape[0]}**")
    # st.markdown(f"- Registros WoS: **{dfwos.shape[0]}**")
    # st.markdown(f"- Registros duplicados eliminados: **{duplicados_final.shape[0]}**")
    # st.markdown(f"- De ellos, sin DOI: **{duplicados_sin_doi_final.shape[0]}**")
    # st.markdown(f"- Registros finales Scopus + WoS: **{df_final.shape[0]}**")

    # # HISTOGRAMA: AUTORES
    # st.subheader("👥 Top 20 autores con más artículos")
    # autores_sorted = autores.sort_values(by='Articles', ascending=False).head(20)
    # fig1, ax1 = plt.subplots(figsize=(8, 4))
    # ax1.bar(autores_sorted['Authors'], autores_sorted['Articles'])
    # ax1.set_xlabel('Autores')
    # ax1.set_ylabel('Número de Artículos')
    # ax1.set_title('Top 20 Autores')
    # plt.xticks(rotation=90)
    # st.pyplot(fig1)

    # # HISTOGRAMA: AUTHOR KEYWORDS
    # st.subheader("🔑 Top 25 Author Keywords")
    # df_sorted_authkw = df_author_keywords.sort_values(by='Conteo', ascending=False).head(25)
    # fig2, ax2 = plt.subplots(figsize=(8, 4))
    # ax2.bar(df_sorted_authkw['Author Keyword'], df_sorted_authkw['Conteo'])
    # ax2.set_xlabel('Author Keywords')
    # ax2.set_ylabel('Frecuencia')
    # ax2.set_title('Top 25 Author Keywords')
    # plt.xticks(rotation=90)
    # st.pyplot(fig2)

    # # HISTOGRAMA: INDEX KEYWORDS
    # st.subheader("🔍 Top 25 Index Keywords")
    # df_sorted_indkw = df_index_keywords.sort_values(by='Conteo', ascending=False).head(25)
    # fig3, ax3 = plt.subplots(figsize=(8, 4))
    # ax3.bar(df_sorted_indkw['Index Keywords'], df_sorted_indkw['Conteo'])
    # ax3.set_xlabel('Index Keywords')
    # ax3.set_ylabel('Frecuencia')
    # ax3.set_title('Top 25 Index Keywords')
    # plt.xticks(rotation=90)
    # st.pyplot(fig3)

    # ✅ Tabs: Informes + Gráficos

# ✅ Solo mostrar pestañas si todos los datos están disponibles
if all(k in st.session_state for k in ["dfsco", "dfwos", "df_final", "duplicados_final", "duplicados_sin_doi_final"]):
    dfsco = st.session_state["dfsco"]
    dfwos = st.session_state["dfwos"]
    df_final = st.session_state["df_final"]
    duplicados_final = st.session_state["duplicados_final"]
    duplicados_sin_doi_final = st.session_state["duplicados_sin_doi_final"]

    tab1, tab2 = st.tabs(["📄 Informes y descargas", "📈 Gráficos"])

    # --- INFORMES Y DESCARGAS ---
    with tab1:
        st.subheader("📊 Información de la fusión")

        st.markdown(f"- Registros Scopus: **{dfsco.shape[0]}**")
        st.markdown(f"- Registros WoS: **{dfwos.shape[0]}**")
        st.markdown(f"- Registros duplicados eliminados: **{duplicados_final.shape[0]}**")
        st.markdown(f"- De ellos, sin DOI: **{duplicados_sin_doi_final.shape[0]}**")
        st.markdown(f"- Registros finales Scopus + WoS: **{df_final.shape[0]}**")

        st.subheader("📥 Descargar archivos Excel")
        st.download_button("📥 Scopus+WoS.xlsx", output_fusion.getvalue(), "Scopus+WOS.xlsx")
        st.download_button("📥 Duplicados eliminados", output_duplicados.getvalue(), "Scopus+WOS(duplicados).xlsx")
        st.download_button("📥 Tablas para depuración", output_tablas.getvalue(), "Tablas_para_depuraciones.xlsx")

    # --- GRÁFICOS ---
    with tab2:
        st.subheader("👥 Top 20 autores con más artículos")
        autores_sorted = autores.sort_values(by='Articles', ascending=False).head(20)
        fig1, ax1 = plt.subplots(figsize=(8, 4))
        ax1.bar(autores_sorted['Authors'], autores_sorted['Articles'])
        ax1.set_xlabel('Autores')
        ax1.set_ylabel('Número de Artículos')
        ax1.set_title('Top 20 Autores')
        plt.xticks(rotation=90)
        st.pyplot(fig1)

        st.subheader("🔑 Top 25 Author Keywords")
        df_sorted_authkw = df_author_keywords.sort_values(by='Conteo', ascending=False).head(25)
        fig2, ax2 = plt.subplots(figsize=(8, 4))
        ax2.bar(df_sorted_authkw['Author Keyword'], df_sorted_authkw['Conteo'])
        ax2.set_xlabel('Author Keywords')
        ax2.set_ylabel('Frecuencia')
        ax2.set_title('Top 25 Author Keywords')
        plt.xticks(rotation=90)
        st.pyplot(fig2)

        st.subheader("🔍 Top 25 Index Keywords")
        df_sorted_indkw = df_index_keywords.sort_values(by='Conteo', ascending=False).head(25)
        fig3, ax3 = plt.subplots(figsize=(8, 4))
        ax3.bar(df_sorted_indkw['Index Keywords'], df_sorted_indkw['Conteo'])
        ax3.set_xlabel('Index Keywords')
        ax3.set_ylabel('Frecuencia')
        ax3.set_title('Top 25 Index Keywords')
        plt.xticks(rotation=90)
        st.pyplot(fig3)

        st.success("✅ Fusión completada con éxito. Puedes continuar con los informes.")

else:
    st.info("ℹ️ Aún no hay datos procesados para mostrar informes o gráficos.")

# -------------------- PARTE 3: DEPURACIÓN OPCIONAL ------------------------------
# Parte 3: Depuración opcional del usuario
st.markdown("### 🧪 Parte 3: Depuración opcional del usuario (4 campos de `df_final`)")
activar_depuracion = st.checkbox("🔍 Realizar depuración manual de autores/keywords/referencias")

if activar_depuracion:
    depuracion_file = st.file_uploader("📥 Sube el archivo Excel con las tablas de conversión", type=["xlsx", "xls"])
    
    if depuracion_file is not None and st.button("✅ Aplicar depuración"):
        
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
                tmp.write(depuracion_file.read())
                tmp_path = tmp.name
            filename = tmp_path

           
      
            # -------------------- DEPURACIÓN DE AUTHORS ------------------------------
            sheet_name = 'Authors'
            try:
                df_authors_table = pd.read_excel(filename, sheet_name=sheet_name)
                if df_authors_table.empty or df_authors_table.loc[0, 'New Author'] == '0-change-0':
                    st.warning(f"La hoja '{sheet_name}' no ha sido completada. No se aplicaron cambios.")
                else:
                    for _, fila in df_authors_table.iterrows():
                        author = fila['Authors']
                        nueva_author = fila['New Author']
                        fila_encontrada = autores[autores['Authors'] == author]
                        if not fila_encontrada.empty:
                            indices = [int(i) for i in fila_encontrada['Indices'].iloc[0].split(';')]
                            posiciones = [int(p) for p in fila_encontrada['Posiciones'].iloc[0].split(';')]
                            for idx, pos in zip(indices, posiciones):
                                if idx in df_final.index:
                                    current = df_final.at[idx, 'Authors'].split(';')
                                    if pos < len(current):
                                        current[pos] = nueva_author
                                        df_final.at[idx, 'Authors'] = '; '.join(current)
                    df_final['Authors'] = df_final['Authors'].apply(lambda x: '; '.join([a.strip() for a in x.split(';')]))
                    df_final['Author full names'] = df_final['Authors']
                    st.success("Depuración de Authors completada correctamente.")
            except Exception as e:
                st.warning(f"Depuración de Authors no posible: {str(e)}")

            # -------------------- DEPURACIÓN DE AUTHOR KEYWORDS ------------------------------
            sheet_name = 'Author Keywords'
            try:
                df_authors_keywords_table = pd.read_excel(filename, sheet_name=sheet_name)
                if df_authors_keywords_table.empty or df_authors_keywords_table.loc[0, 'New Keyword'] == '0-change-0':
                    st.warning(f"La hoja '{sheet_name}' no ha sido completada. No se aplicaron cambios.")
                else:
                    for _, fila in df_authors_keywords_table.iterrows():
                        keyword = fila['Author Keyword']
                        new_keyword = fila['New Keyword']
                        fila_encontrada = df_author_keywords[df_author_keywords['Author Keyword'] == keyword]
                        if not fila_encontrada.empty:
                            indices = [int(i) for i in fila_encontrada['Indices'].iloc[0].split(';')]
                            posiciones = [int(p) for p in fila_encontrada['Posiciones'].iloc[0].split(';')]
                            for idx, pos in zip(indices, posiciones):
                                if idx in df_final.index:
                                    current = df_final.at[idx, 'Author Keywords'].split(';')
                                    if pos < len(current):
                                        current[pos] = new_keyword
                                        df_final.at[idx, 'Author Keywords'] = '; '.join(current)
                    df_final['Author Keywords'] = df_final['Author Keywords'].apply(lambda x: '; '.join([a.strip() for a in x.split(';')]))
                    st.success("Depuración de Author Keywords completada correctamente.")
            except Exception as e:
                st.warning(f"Depuración de Author Keywords no posible: {str(e)}")

            # -------------------- DEPURACIÓN DE INDEX KEYWORDS ------------------------------
            sheet_name = 'Index Keywords'
            try:
                df_index_keywords_table = pd.read_excel(filename, sheet_name=sheet_name)
                if df_index_keywords_table.empty or df_index_keywords_table.loc[0, 'New Keyword'] == '0-change-0':
                    st.warning(f"La hoja '{sheet_name}' no ha sido completada. No se aplicaron cambios.")
                else:
                    for _, fila in df_index_keywords_table.iterrows():
                        keyword = fila['Index Keywords']
                        new_keyword = fila['New Keyword']
                        fila_encontrada = df_index_keywords[df_index_keywords['Index Keywords'] == keyword]
                        if not fila_encontrada.empty:
                            indices = [int(i) for i in fila_encontrada['Indices'].iloc[0].split(';')]
                            posiciones = [int(p) for p in fila_encontrada['Posiciones'].iloc[0].split(';')]
                            for idx, pos in zip(indices, posiciones):
                                if idx in df_final.index:
                                    current = df_final.at[idx, 'Index Keywords'].split(';')
                                    if pos < len(current):
                                        current[pos] = new_keyword
                                        df_final.at[idx, 'Index Keywords'] = '; '.join(current)
                    df_final['Index Keywords'] = df_final['Index Keywords'].apply(lambda x: '; '.join([a.strip() for a in x.split(';')]))
                    st.success("Depuración de Index Keywords completada correctamente.")
            except Exception as e:
                st.warning(f"Depuración de Index Keywords no posible: {str(e)}")

            # -------------------- DEPURACIÓN DE CITED REFERENCES ------------------------------
            sheet_name = 'Cited References'
            try:
                df_references_table = pd.read_excel(filename, sheet_name=sheet_name)
                if df_references_table.empty or df_references_table.loc[0, 'New Reference'] == '0-change-0':
                    st.warning(f"La hoja '{sheet_name}' no ha sido completada. No se aplicaron cambios.")
                else:
                    df_references_table.fillna('', inplace=True)
                    for _, fila in df_references_table.iterrows():
                        ref = fila['References']
                        new_ref = fila['New Reference']
                        fila_encontrada = df_references_info[df_references_info['References'] == ref]
                        if not fila_encontrada.empty:
                            indices = [int(i) for i in fila_encontrada['Indices'].iloc[0].split(';')]
                            posiciones = [int(p) for p in fila_encontrada['Posiciones'].iloc[0].split(';')]
                            for idx, pos in zip(indices, posiciones):
                                if idx in df_final.index:
                                    current = df_final.at[idx, 'References'].split(';')
                                    if pos < len(current):
                                        current[pos] = new_ref
                                        df_final.at[idx, 'References'] = '; '.join(current)
                    df_final['References'] = df_final['References'].apply(lambda x: '; '.join([a.strip() for a in x.split(';')]))
                    df_final['References'] = df_final['References'].str.replace(" ;", "")
                    st.success("Depuración de Cited References completada correctamente.")
            except Exception as e:
                st.warning(f"Depuración de Cited References no posible: {str(e)}")

            # Aseguramos se guardan los cambios realizados después de todas las depuraciones para ser utilizados en la Parte 4
            st.session_state['df_final'] = df_final
        except Exception as e:
            st.error(f"Error general durante la depuración: {str(e)}")



# -------------------- PARTE 4: GENERAR FICHEROS FINALES --------------------

st.markdown("## 📁 Generación de ficheros finales e informes")
if st.button("📁 Generar ficheros finales"):
    # Asegurar que df_final esté disponible (viene de la Parte 3 o la Parte 2)
    if 'df_final' in st.session_state:
        df_final = st.session_state['df_final']
    else:
        try:
            df_final  # verificar si está definido
        except NameError:
            st.error("❌ No se ha encontrado df_final. Asegúrate de haber cargado y fusionado las bases de datos.")
            st.stop()

    
    import io
    import base64
    from datetime import datetime

    
    # Guardar Excel
    output_excel = io.BytesIO()
    df_final.to_excel(output_excel, index=False)
    st.download_button("⬇️ Descargar Excel depurado", data=output_excel.getvalue(),
                       file_name="Scopus+WOS(Depurado).xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    # Guardar CSV
    output_csv = io.StringIO()
    df_final.to_csv(output_csv, index=False)
    st.download_button("⬇️ Descargar CSV depurado", data=output_csv.getvalue(),
                       file_name="Scopus+WOS(Depurado).csv", mime="text/csv")

    # Generar RIS
    def df_to_ris(df):
        ris_entries = []
        for _, row in df.iterrows():
            authors = str(row['Authors']).split(';')
            affiliations = str(row['Affiliations']).split(';')
            keywords = str(row['Author Keywords']).split(';')
            cited_by = f"Cited By: {row['Cited by']}" if not pd.isnull(row['Cited by']) else ''
            export_date = datetime.today().strftime('%d %B %Y')
            entry = "TY  - JOUR\n"
            entry += ''.join([f"AU  - {a.strip()}\n" for a in authors if a.strip()])
            entry += f"TI  - {row['Title']}\n"
            entry += f"PY  - {row['Year']}\n"
            entry += f"T2  - {row['Source title']}\n"
            entry += f"VL  - {row['Volume']}\n"
            entry += f"IS  - {row['Issue']}\n"
            entry += f"C7  - {row.get('Art. No.', '')}\n"
            entry += f"SP  - {row['Page start']}\n"
            entry += f"EP  - {row['Page end']}\n"
            entry += f"DO  - {row['DOI']}\n"
            entry += f"UR  - {row.get('Link', '')}\n"
            entry += ''.join([f"AD  - {aff.strip()}\n" for aff in affiliations if aff.strip()])
            entry += f"AB  - {row['Abstract']}\n"
            entry += ''.join([f"KW  - {kw.strip()}\n" for kw in keywords if kw.strip()])
            entry += f"PB  - {row['Publisher']}\n"
            entry += f"SN  - {row['ISSN']}\n"
            entry += f"LA  - {row['Language of Original Document']}\n"
            entry += f"J2  - {row['Abbreviated Source Title']}\n"
            entry += f"M3  - {row['Document Type']}\n"
            entry += f"DB  - {row['Source']}\n"
            entry += f"N1  - Export Date: {export_date}; {cited_by}\n"
            entry += "ER  -\n"
            ris_entries.append(entry)
        return "\n".join(ris_entries)

    ris_content = df_to_ris(df_final)
    output_ris = io.StringIO(ris_content)
    st.download_button("⬇️ Descargar RIS", data=output_ris.getvalue(),
                       file_name="Scopus+WOS(Depurado).ris", mime="application/x-research-info-systems")

    

    # --------- Generar TXT global y por lotes (formato WoS) ---------
    import zipfile

    def generar_texto(df, campos_seleccionados, mapeo_campos_a_codigos):
        texto = "VR 1.0\n"
        for _, row in df.iterrows():
            texto_registro = "PT J\n"
            campos_agregados = False
            for campo_df, campo_txt in mapeo_campos_a_codigos.items():
                if campo_df in campos_seleccionados:
                    valor_campo = row[campo_df]
                    if valor_campo and str(valor_campo).strip():
                        if campo_df in ['Authors', 'Author full names', 'References']:
                            elementos = str(valor_campo).split('; ')
                            texto_registro += f"{campo_txt} {elementos[0]}\n"
                            texto_registro += ''.join([f"   {elem}\n" for elem in elementos[1:] if elem.strip()])
                        else:
                            valor_formateado = str(valor_campo).replace('\n', '\n   ')
                            texto_registro += f"{campo_txt} {valor_formateado}\n"
                        campos_agregados = True
            if campos_agregados:
                texto_registro += "ER\n\n"
                texto += texto_registro
        texto += "EF\n"
        return texto

    mapeo_codigos = {
        'Authors': 'AU',
        'Author full names': 'AF',
        'Title': 'TI',
        'Source title': 'SO',
        'Language of Original Document': 'LA',
        'Document Type': 'DT',
        'Author Keywords': 'DE',
        'Index Keywords': 'ID',
        'Abstract': 'AB',
        'Correspondence Address': 'C1',
        'Affiliations': 'C3',
        'References': 'CR',
        'Cited by': 'TC',
        'Publisher': 'PU',
        'ISSN': 'SN',
        'Abbreviated Source Title': 'J9',
        'Year': 'PY',
        'Volume': 'VL',
        'Issue': 'IS',
        'Page start': 'BP',
        'Page end': 'EP',
        'DOI': 'DI',
        'Page count': 'PG',
        'Source': 'UT',
        'Funding Texts': 'FX'
    }
    campos_txt = list(mapeo_codigos.keys())

    # TXT global
    texto_global = generar_texto(df_final, campos_txt, mapeo_codigos)
    buffer_txt = io.StringIO(texto_global)
    st.download_button("⬇️ Descargar TXT completo (formato WoS)", data=buffer_txt.getvalue(),
                       file_name="Scopus+WOS(Depurado).txt", mime="text/plain")

    # TXT por lotes (ZIP)
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        inicio = 0
        numero_archivo = 1
        while inicio < len(df_final):
            fin = min(inicio + 500, len(df_final))
            texto_lote = generar_texto(df_final.iloc[inicio:fin], campos_txt, mapeo_codigos)
            nombre_archivo = f"Scopus+WOS(Dep {inicio+1} a {fin}).txt"
            zipf.writestr(nombre_archivo, texto_lote)
            inicio = fin

    st.download_button("⬇️ Descargar TXT por lotes (ZIP)", data=zip_buffer.getvalue(),
                       file_name="Scopus+WOS_lotes.zip", mime="application/zip")


    # Informe final
    st.markdown("### 📊 Información final de la fusión")
    st.write(f"**Registros Scopus:** {dfsco.shape[0]}")
    st.write(f"**Registros WoS:** {dfwos.shape[0]}")
    st.write(f"**Duplicados eliminados:** {duplicados_final.shape[0]}")
    st.write(f"**Duplicados sin DOI:** {duplicados_sin_doi.shape[0]}")
    st.write(f"**Registros finales:** {df_final.shape[0]}")

    # Histogramas
    import matplotlib.pyplot as plt
    st.markdown("### 👤 Top 25 autores")
    top_authors = df_final['Authors'].str.split(';').explode().str.strip().value_counts().head(25)
    fig, ax = plt.subplots(figsize=(8,5))
    top_authors.plot(kind='bar', ax=ax, color='green')
    plt.xticks(rotation=90)
    st.pyplot(fig)

    st.markdown("### 🔑 Top 25 Author Keywords")
    top_keywords = df_final['Author Keywords'].str.split(';').explode().str.strip().value_counts().head(25)
    fig2, ax2 = plt.subplots(figsize=(8,5))
    top_keywords.plot(kind='bar', ax=ax2, color='skyblue')
    plt.xticks(rotation=90)
    st.pyplot(fig2)

    st.markdown("### 🏷️ Top 25 Index Keywords")
    top_index_kw = df_final['Index Keywords'].str.split(';').explode().str.strip().value_counts().head(25)
    fig3, ax3 = plt.subplots(figsize=(8,5))
    top_index_kw.plot(kind='bar', ax=ax3, color='salmon')
    plt.xticks(rotation=90)
    st.pyplot(fig3)

    st.markdown("### 📚 Top 20 Cited References")
    top_refs = df_final['References'].str.split(';').explode().str.strip().value_counts().head(20)
    fig4, ax4 = plt.subplots(figsize=(8,5))
    top_refs.plot(kind='bar', ax=ax4, color='orange')
    plt.xticks(rotation=90)
    st.pyplot(fig4)


