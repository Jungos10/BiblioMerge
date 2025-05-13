# -------------------- PARTE 1: CARGAR FICHEROS --------------------

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from collections import defaultdict
import io
import time  # <- necesario para el spinner
import tempfile
import gc

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
if "fusion_completada" not in st.session_state:
    st.session_state["fusion_completada"] = False
    #st.session_state["fusion_completada"] = True

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
if st.session_state.get("procesado", False):
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

    # Guardar en session_state una vez procesados todos los archivos
    st.session_state["dfsco"] = dfsco
    st.session_state["dfwos"] = dfwos
    st.session_state["num_dfsco"] = dfsco.shape[0]
    st.session_state["num_dfwos"] = dfwos.shape[0]
                                       




# -------------------- PARTE 2: FUSIÓN, INFORMES PRELIMINARES Y TABLAS DEPURACIÓN --------------------
# -------------------- PARTE 2: PROCESAMIENTO Y FUSIÓN --------------------
# BLOQUE 3 – Proceso de fusión real
if st.session_state.get("fusion_en_proceso", False):

    mensaje_proceso = st.empty()
    st.session_state["mensaje_proceso"] = mensaje_proceso

    with st.spinner("🔄 Fusionando archivos y limpiando registros..."):
        mensaje_proceso.markdown("✅ **Fusión iniciada correctamente. Procesando datos...**")
           
    
    # ---------IMPORTAMOS AMBOS ARCHIVOS, MAPEAMOS, Y LOS UNIMOS. ADECUAMOS UN CAMPO DE IDENTIFICACIÓN Y LIMPIAMOS CAMPOS CON 'NaN'-----

            # Mapeamos el archivo WOS(dfwos) con el archivo Scopus (dfsco)
            mapping = {'AU': 'Authors' ,'AF': 'Author full names','TI': 'Title', 'PY': 'Year',
                       'SO': 'Source title', 'VL': 'Volume', 'IS': 'Issue', 'CR': 'References', 'BP': 'Page start',
                       'EP': 'Page end', 'PG': 'Page count', 'TC': 'Cited by', 'DI': 'DOI',
                       'C3': 'Affiliations', 'AB': 'Abstract', 'DE': 'Author Keywords', 'ID': 'Index Keywords',
                       'FX': 'Funding Texts', 'RP': 'Correspondence Address',
                       'PU': 'Publisher', 'SN': 'ISSN', 'LA': 'Language of Original Document',
                       'J9': 'Abbreviated Source Title', 'DT': 'Document Type', 'UT': 'EID', 'C1': 'Authors with affiliations'}
        
            dfwos = st.session_state.get("dfwos")
            dfsco = st.session_state.get("dfsco")
            
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

             # Guardar para usar luego
            st.session_state["df_final"] = df_final
            
            # Guardar conteos clave para informes
            st.session_state["num_duplicados_final"] = duplicados_final.shape[0]
            st.session_state["num_duplicados_sin_doi"] = duplicados_sin_doi_final.shape[0]
            st.session_state["num_df_final"] = df_final.shape[0]

            # Guardar los dataframes necesarios para informes y exportación
            st.session_state["duplicados_final"] = duplicados_final
            st.session_state["duplicados_sin_doi_final"] = duplicados_sin_doi_final
            st.session_state["autores"] = autores
            st.session_state["df_author_keywords"] = df_author_keywords
            st.session_state["df_index_keywords"] = df_index_keywords
            st.session_state["df_references_info"] = df_references_info

            # Guardar top valores para histogramas (no guardar los DataFrames enteros)
            st.session_state["top_autores"] = autores.nlargest(20, 'Articles')[['Authors', 'Articles']].values.tolist()
            st.session_state["top_authkw"] = df_author_keywords.nlargest(25, 'Conteo')[['Author Keyword', 'Conteo']].values.tolist()
            st.session_state["top_indexkw"] = df_index_keywords.nlargest(25, 'Conteo')[['Index Keywords', 'Conteo']].values.tolist()

            # ---- Liberar memoria innecesaria tras guardar en session_state ----
            del dfsco_list
            del dfwos_selected
            del df_concatenated
            del df_concatenated_sin_duplicados
            del df_sin_vacios
            
            del duplicados_doi
            del duplicados_sin_doi
            del duplicados_doi_final
            del duplicados_sin_doi_final
            del indices_a_eliminar_doi
            del indices_a_eliminar_sin_doi
            
            del df_autores_sin_cod
            del df_conversion
            
            del author_keywords_dict
            del index_keywords_dict
            del references_dict

            # Librería que fuerza la limpieaza de lo borrado
            gc.collect()

            # Generación de archivos Excel para descarga
            import io
        
            output_fusion = io.BytesIO()
            output_duplicados = io.BytesIO()
            output_tablas = io.BytesIO()
        
            # Recuperar los DataFrames necesarios
            df_final = st.session_state.get("df_final")
            duplicados_final = st.session_state.get("duplicados_final")
            autores = st.session_state.get("autores")
            df_author_keywords = st.session_state.get("df_author_keywords")
            df_index_keywords = st.session_state.get("df_index_keywords")
            df_references_info = st.session_state.get("df_references_info")
            
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

            # Guardar archivos en session_state
            st.session_state["output_fusion_bytes"] = output_fusion.getvalue()
            st.session_state["output_duplicados_bytes"] = output_duplicados.getvalue()
            st.session_state["output_tablas_bytes"] = output_tablas.getvalue()

            # Finalizar estado
            #mensaje_proceso.empty()
            st.success("✅ Fusión completada con éxito. Puedes continuar con los informes.")
            st.session_state["fusion_en_proceso"] = False
            st.session_state["fusion_completada"] = True

            # Limpiar mensaje mostrado al inicio
            if "mensaje_proceso" in st.session_state:
                st.session_state["mensaje_proceso"].empty()
                st.session_state.pop("mensaje_proceso")

# -------------------- PARTE 2B: BOTONES DE DESCARGA + REPORTING PERSISTENTE --------------------

if (
    st.session_state.get("fusion_completada", False)
    and not st.session_state.get("depuracion_activada", False)
    and not st.session_state.get("parte4_generada", False)
):
    st.markdown("### 📥 Descarga tus archivos:")
    st.download_button("📥 Descargar Scopus+WOS.xlsx", st.session_state["output_fusion_bytes"], "Scopus+WOS.xlsx")
    st.download_button("📥 Descargar duplicados eliminados", st.session_state["output_duplicados_bytes"], "Scopus+WOS(duplicados).xlsx")
    st.download_button("📥 Descargar Tablas_para_depuraciones.xlsx", st.session_state["output_tablas_bytes"], "Tablas_para_depuraciones.xlsx")

    # ----------- REPORTING FINAL DE FUSIÓN -----------
    st.markdown("### 📊 Informe resumen de la fusión")
    st.write(f"**Registros Scopus:** {st.session_state.get('num_dfsco', 0)}")
    st.write(f"**Registros WoS:** {st.session_state.get('num_dfwos', 0)}")
    st.write(f"**Duplicados eliminados:** {st.session_state.get('num_duplicados_final', 0)}")
    st.write(f"**Duplicados sin DOI:** {st.session_state.get('num_duplicados_sin_doi', 0)}")
    st.write(f"**Registros finales:** {st.session_state.get('num_df_final', 0)}")
    
    # Mostrar histogramas desde session_state
    def mostrar_histograma_top(lista_datos, titulo, xlabel, ylabel):
        if not lista_datos:
            st.warning(f"No hay datos para {titulo}.")
            return
        etiquetas, valores = zip(*lista_datos)
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.bar(etiquetas, valores)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(titulo)
        plt.xticks(rotation=90)
        st.pyplot(fig)

    st.subheader("👥 Top 20 autores con más artículos")
    mostrar_histograma_top(
        st.session_state["top_autores"],
        "Top 20 Autores",
        "Autores",
        "Número de Artículos"
    )

    st.subheader("🔑 Top 25 Author Keywords")
    mostrar_histograma_top(
        st.session_state["top_authkw"],
        "Top 25 Author Keywords",
        "Author Keywords",
        "Frecuencia"
    )

    st.subheader("🔍 Top 25 Index Keywords")
    mostrar_histograma_top(
        st.session_state["top_indexkw"],
        "Top 25 Index Keywords",
        "Index Keywords",
        "Frecuencia"
    )


            # mensaje_proceso.empty()  # Oculta el mensaje anterior
            # st.success("✅ Fusión completada con éxito. Puedes continuar con los informes.")
            # st.session_state["fusion_en_proceso"] = False
            # st.session_state["fusion_completada"] = True
                

if not st.session_state.get("parte4_generada", False):

    # -------------------- PARTE 3: DEPURACIÓN OPCIONAL ------------------------------
   
    st.markdown("## 🧪 Parte 3: Depuración manual de autores/keywords/referencias")
    
    # Mostrar solo si la fusión está finalizada o no se ha activado la Parte 4
    #if st.session_state.get("fusion_en_proceso") is False:
    #if st.session_state.get("procesado") and not st.session_state.get("fusion_en_proceso", True):
    if (
        st.session_state.get("procesado") and 
        not st.session_state.get("fusion_en_proceso", True) and 
        not st.session_state.get("parte4_generada", False)
    ):    
        if "depuracion_activada" not in st.session_state:
            st.session_state["depuracion_activada"] = False
        if "depuracion_realizada" not in st.session_state:
            st.session_state["depuracion_realizada"] = False
    
        # Mostrar checkbox solo si aún no se ha activado
        if not st.session_state["depuracion_activada"] and not st.session_state["depuracion_realizada"]:
            if st.checkbox("🔍 Activar depuración manual", key="activar_depuracion"):
                st.session_state["depuracion_activada"] = True
                st.rerun()
    
        # Si activado, mostrar uploader y botón
        if st.session_state["depuracion_activada"] and not st.session_state["depuracion_realizada"]:
            st.markdown("Carga el archivo Excel con las tablas de conversión:")
            depuracion_file = st.file_uploader("📥 Archivo de depuración", type=["xlsx"])
    
            if depuracion_file and st.button("✅ Aplicar depuración"):
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
                        tmp.write(depuracion_file.read())
                        tmp_path = tmp.name
    
                    # Recuperar DataFrames de session_state
                    df_final = st.session_state.get("df_final")
                    autores = st.session_state.get("autores")
                    df_author_keywords = st.session_state.get("df_author_keywords")
                    df_index_keywords = st.session_state.get("df_index_keywords")
                    df_references_info = st.session_state.get("df_references_info")
    
                    # ---- DEPURACIÓN: Authors ----
                    try:
                        df_authors_table = pd.read_excel(tmp_path, sheet_name="Authors")
                        for _, fila in df_authors_table.iterrows():
                            if fila["New Author"] != "0-change-0":
                                author = fila["Authors"]
                                new_author = fila["New Author"]
                                fila_encontrada = autores[autores["Authors"] == author]
                                if not fila_encontrada.empty:
                                    indices = [int(i) for i in fila_encontrada["Indices"].iloc[0].split(';')]
                                    posiciones = [int(p) for p in fila_encontrada["Posiciones"].iloc[0].split(';')]
                                    for idx, pos in zip(indices, posiciones):
                                        autores_actuales = df_final.at[idx, "Authors"].split(";")
                                        if pos < len(autores_actuales):
                                            autores_actuales[pos] = new_author
                                            df_final.at[idx, "Authors"] = "; ".join(autores_actuales)
                        st.success("✅ Depuración de autores completada.")
                    except Exception as e:
                        st.warning(f"No se pudo aplicar depuración en Authors: {str(e)}")
    
                    # ---- DEPURACIÓN: Author Keywords ----
                    try:
                        df_ak = pd.read_excel(tmp_path, sheet_name="Author Keywords")
                        for _, fila in df_ak.iterrows():
                            if fila["New Keyword"] != "0-change-0":
                                old_kw = fila["Author Keyword"]
                                new_kw = fila["New Keyword"]
                                fila_encontrada = df_author_keywords[df_author_keywords["Author Keyword"] == old_kw]
                                if not fila_encontrada.empty:
                                    indices = [int(i) for i in fila_encontrada["Indices"].iloc[0].split(';')]
                                    posiciones = [int(p) for p in fila_encontrada["Posiciones"].iloc[0].split(';')]
                                    for idx, pos in zip(indices, posiciones):
                                        kws = df_final.at[idx, "Author Keywords"].split(";")
                                        if pos < len(kws):
                                            kws[pos] = new_kw
                                            df_final.at[idx, "Author Keywords"] = "; ".join(kws)
                        st.success("✅ Depuración de Author Keywords completada.")
                    except Exception as e:
                        st.warning(f"No se pudo aplicar depuración en Author Keywords: {str(e)}")
    
                    # ---- DEPURACIÓN: Index Keywords ----
                    try:
                        df_ik = pd.read_excel(tmp_path, sheet_name="Index Keywords")
                        for _, fila in df_ik.iterrows():
                            if fila["New Keyword"] != "0-change-0":
                                old_kw = fila["Index Keywords"]
                                new_kw = fila["New Keyword"]
                                fila_encontrada = df_index_keywords[df_index_keywords["Index Keywords"] == old_kw]
                                if not fila_encontrada.empty:
                                    indices = [int(i) for i in fila_encontrada["Indices"].iloc[0].split(';')]
                                    posiciones = [int(p) for p in fila_encontrada["Posiciones"].iloc[0].split(';')]
                                    for idx, pos in zip(indices, posiciones):
                                        kws = df_final.at[idx, "Index Keywords"].split(";")
                                        if pos < len(kws):
                                            kws[pos] = new_kw
                                            df_final.at[idx, "Index Keywords"] = "; ".join(kws)
                        st.success("✅ Depuración de Index Keywords completada.")
                    except Exception as e:
                        st.warning(f"No se pudo aplicar depuración en Index Keywords: {str(e)}")
    
                    # ---- DEPURACIÓN: References ----
                    try:
                        df_refs = pd.read_excel(tmp_path, sheet_name="Cited References")
                        for _, fila in df_refs.iterrows():
                            if fila["New Reference"] != "0-change-0":
                                old_ref = fila["References"]
                                new_ref = fila["New Reference"]
                                fila_encontrada = df_references_info[df_references_info["References"] == old_ref]
                                if not fila_encontrada.empty:
                                    indices = [int(i) for i in fila_encontrada["Indices"].iloc[0].split(';')]
                                    posiciones = [int(p) for p in fila_encontrada["Posiciones"].iloc[0].split(';')]
                                    for idx, pos in zip(indices, posiciones):
                                        refs = df_final.at[idx, "References"].split(";")
                                        if pos < len(refs):
                                            refs[pos] = new_ref
                                            df_final.at[idx, "References"] = "; ".join(refs)
                        st.success("✅ Depuración de Referencias completada.")
                    except Exception as e:
                        st.warning(f"No se pudo aplicar depuración en Referencias: {str(e)}")
    
                    # Guardar el nuevo df_final actualizado
                    st.session_state["df_final"] = df_final
                    st.session_state["depuracion_realizada"] = True
                    st.success("🎉 Todas las depuraciones aplicadas correctamente.")
    
                except Exception as e:
                    st.error(f"❌ Error general al procesar la depuración: {str(e)}")
    
    
#     # -------------------- PARTE 4: GENERAR FICHEROS FINALES --------------------
    
#     # --- Función para mostrar el botón desactivado con estilo gris ---
#     def mostrar_boton_finales_bloqueado():
#         st.markdown(
#             "<span style='color: grey;'>Puedes generar los ficheros finales a partir del resultado de la fusión y/o la depuración.</span>",
#             unsafe_allow_html=True
#         )
#         st.button("📁 Generar ficheros finales", key="btn_generar_finales_disabled", type="primary", disabled=True, use_container_width=True)
    
#     st.markdown("## 📁 Parte 4: Generar archivos finales e informes")
    
#     fusion_completada = st.session_state.get("fusion_completada", False)
#     depuracion_realizada = st.session_state.get("depuracion_realizada", False)
#     depuracion_en_proceso = st.session_state.get("depuracion_en_proceso", False)
    
  
#     habilitar_parte4 = (fusion_completada or depuracion_realizada) #and not depuracion_en_proceso

#     # --- Si marcamos el rerun en la ejecución anterior, ahora lo ejecutamos y limpiamos el flag ---
#     if "parte4_generada" not in st.session_state:
#         st.session_state["parte4_generada"] = False
           
#     if habilitar_parte4:
#         st.markdown("Puedes generar los ficheros finales a partir del resultado de la fusión y/o la depuración.")

#         if "parte4_generada" not in st.session_state:
#             st.session_state["parte4_generada"] = False

#         if not st.session_state["parte4_generada"]:
#             boton = st.button("📁 Generar ficheros finales", key="btn_generar_finales", type="primary", use_container_width=True)
#             if boton:
#                 st.session_state["parte4_generada"] = True
#                 st.query_params["refresh"] = "1"  # fuerza un cambio de estado para recargar
#                 st.stop()  # detiene, la siguiente ejecución entrará al bloque else
                  
        
#         else:
#             df_final = st.session_state.get("df_final")
    
         
#             import io
#             import base64
#             from datetime import datetime
#             import zipfile
    
#             # Guardar Excel
#             output_excel = io.BytesIO()
#             df_final.to_excel(output_excel, index=False)
#             st.download_button("⬇️ Descargar Excel depurado", data=output_excel.getvalue(),
#                                file_name="Scopus+WOS(Depurado).xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    
#             # Guardar CSV
#             output_csv = io.StringIO()
#             df_final.to_csv(output_csv, index=False)
#             st.download_button("⬇️ Descargar CSV depurado", data=output_csv.getvalue(),
#                                file_name="Scopus+WOS(Depurado).csv", mime="text/csv")
    
#             # Generar RIS
#             def df_to_ris(df):
#                 ris_entries = []
#                 for _, row in df.iterrows():
#                     authors = str(row['Authors']).split(';')
#                     affiliations = str(row['Affiliations']).split(';')
#                     keywords = str(row['Author Keywords']).split(';')
#                     cited_by = f"Cited By: {row['Cited by']}" if not pd.isnull(row['Cited by']) else ''
#                     export_date = datetime.today().strftime('%d %B %Y')
#                     entry = "TY  - JOUR\n"
#                     entry += ''.join([f"AU  - {a.strip()}\n" for a in authors if a.strip()])
#                     entry += f"TI  - {row['Title']}\n"
#                     entry += f"PY  - {row['Year']}\n"
#                     entry += f"T2  - {row['Source title']}\n"
#                     entry += f"VL  - {row['Volume']}\n"
#                     entry += f"IS  - {row['Issue']}\n"
#                     entry += f"C7  - {row.get('Art. No.', '')}\n"
#                     entry += f"SP  - {row['Page start']}\n"
#                     entry += f"EP  - {row['Page end']}\n"
#                     entry += f"DO  - {row['DOI']}\n"
#                     entry += f"UR  - {row.get('Link', '')}\n"
#                     entry += ''.join([f"AD  - {aff.strip()}\n" for aff in affiliations if aff.strip()])
#                     entry += f"AB  - {row['Abstract']}\n"
#                     entry += ''.join([f"KW  - {kw.strip()}\n" for kw in keywords if kw.strip()])
#                     entry += f"PB  - {row['Publisher']}\n"
#                     entry += f"SN  - {row['ISSN']}\n"
#                     entry += f"LA  - {row['Language of Original Document']}\n"
#                     entry += f"J2  - {row['Abbreviated Source Title']}\n"
#                     entry += f"M3  - {row['Document Type']}\n"
#                     entry += f"DB  - {row['Source']}\n"
#                     entry += f"N1  - Export Date: {export_date}; {cited_by}\n"
#                     entry += "ER  -\n"
#                     ris_entries.append(entry)
#                 return "\n".join(ris_entries)
    
#             ris_content = df_to_ris(df_final)
#             output_ris = io.StringIO(ris_content)
#             st.download_button("⬇️ Descargar RIS", data=output_ris.getvalue(),
#                                file_name="Scopus+WOS(Depurado).ris", mime="application/x-research-info-systems")
    
#             # TXT formato WoS global
#             def generar_texto(df, campos_seleccionados, mapeo):
#                 texto = "VR 1.0\n"
#                 for _, row in df.iterrows():
#                     texto_registro = "PT J\n"
#                     campos_agregados = False
#                     for campo_df, campo_txt in mapeo.items():
#                         if campo_df in campos_seleccionados:
#                             valor = row[campo_df]
#                             if valor and str(valor).strip():
#                                 if campo_df in ['Authors', 'Author full names', 'References']:
#                                     elementos = str(valor).split('; ')
#                                     texto_registro += f"{campo_txt} {elementos[0]}\n"
#                                     texto_registro += ''.join([f"   {e}\n" for e in elementos[1:] if e.strip()])
#                                 else:
#                                     texto_registro += f"{campo_txt} {str(valor).replace('\n', '\n   ')}\n"
#                                 campos_agregados = True
#                     if campos_agregados:
#                         texto_registro += "ER\n\n"
#                         texto += texto_registro
#                 texto += "EF\n"
#                 return texto
    
#             mapeo_codigos = {
#                 'Authors': 'AU', 'Author full names': 'AF', 'Title': 'TI', 'Source title': 'SO',
#                 'Language of Original Document': 'LA', 'Document Type': 'DT', 'Author Keywords': 'DE',
#                 'Index Keywords': 'ID', 'Abstract': 'AB', 'Correspondence Address': 'C1', 'Affiliations': 'C3',
#                 'References': 'CR', 'Cited by': 'TC', 'Publisher': 'PU', 'ISSN': 'SN',
#                 'Abbreviated Source Title': 'J9', 'Year': 'PY', 'Volume': 'VL', 'Issue': 'IS',
#                 'Page start': 'BP', 'Page end': 'EP', 'DOI': 'DI', 'Page count': 'PG',
#                 'Source': 'UT', 'Funding Texts': 'FX'
#             }
    
#             texto_global = generar_texto(df_final, list(mapeo_codigos.keys()), mapeo_codigos)
#             st.download_button("⬇️ Descargar TXT completo (formato WoS)", data=texto_global,
#                                file_name="Scopus+WOS(Depurado).txt", mime="text/plain")
    
#             # TXT por lotes ZIP
#             zip_buffer = io.BytesIO()
#             with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
#                 inicio = 0
#                 numero = 1
#                 while inicio < len(df_final):
#                     fin = min(inicio + 500, len(df_final))
#                     texto_lote = generar_texto(df_final.iloc[inicio:fin], list(mapeo_codigos.keys()), mapeo_codigos)
#                     zipf.writestr(f"Scopus+WOS(Dep {inicio+1}-{fin}).txt", texto_lote)
#                     inicio = fin
    
#             st.download_button("⬇️ Descargar TXT por lotes (ZIP)", data=zip_buffer.getvalue(),
#                                file_name="Scopus+WOS_lotes.zip", mime="application/zip")
    
#             # Informes finales
#             st.markdown("### 📊 Informes de resumen final")
#             st.write(f"**Registros finales:** {df_final.shape[0]}")
    
#             # Histogramas
#             def mostrar_top(df, columna, titulo, color):
#                 top_vals = df[columna].str.split(';').explode().str.strip().value_counts().head(25)
#                 fig, ax = plt.subplots(figsize=(8, 4))
#                 top_vals.plot(kind='bar', ax=ax, color=color)
#                 ax.set_title(titulo)
#                 plt.xticks(rotation=90)
#                 st.pyplot(fig)
    
#             mostrar_top(df_final, 'Authors', "👤 Top 25 autores", 'green')
#             mostrar_top(df_final, 'Author Keywords', "🔑 Top 25 Author Keywords", 'skyblue')
#             mostrar_top(df_final, 'Index Keywords', "🏷️ Top 25 Index Keywords", 'salmon')
#             mostrar_top(df_final, 'References', "📚 Top 20 Cited References", 'orange')
    
#             st.success("✅ Archivos finales generados correctamente.")


# if not habilitar_parte4:
#     if st.session_state.get("procesado") or st.session_state.get("depuracion_realizada"):
#         mostrar_boton_finales_bloqueado()


import io
import base64
from datetime import datetime
import zipfile
import matplotlib.pyplot as plt
# --- Función para mostrar el botón desactivado con estilo gris ---
def mostrar_boton_finales_bloqueado():
    st.markdown(
        "<span style='color: grey;'>Puedes generar los ficheros finales a partir del resultado de la fusión y/o la depuración.</span>",
        unsafe_allow_html=True
    )
    st.button("📁 Generar ficheros finales", key="btn_generar_finales_disabled", type="primary", disabled=True, use_container_width=True)

st.markdown("## 📁 Parte 4: Generar archivos finales e informes")

fusion_completada = st.session_state.get("fusion_completada", False)
depuracion_realizada = st.session_state.get("depuracion_realizada", False)
depuracion_en_proceso = st.session_state.get("depuracion_en_proceso", False)

df_final = st.session_state.get("df_final")
habilitar_parte4 = (fusion_completada or depuracion_realizada)

if habilitar_parte4:
    st.markdown("Puedes generar los ficheros finales a partir del resultado de la fusión y/o la depuración.")

    if "parte4_generada" not in st.session_state:
        st.session_state["parte4_generada"] = False

    if not st.session_state["parte4_generada"]:
        if st.button("📁 Generar ficheros finales", key="btn_generar_finales", type="primary", use_container_width=True):
            # --- Generar y guardar outputs como bytes en session_state ---
            output_excel = io.BytesIO()
            df_final.to_excel(output_excel, index=False)
            st.session_state["parte4_excel_bytes"] = output_excel.getvalue()

            output_csv = io.StringIO()
            df_final.to_csv(output_csv, index=False)
            st.session_state["parte4_csv_bytes"] = output_csv.getvalue()

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
            st.session_state["parte4_ris_bytes"] = ris_content

            def generar_texto(df, campos_seleccionados, mapeo):
                texto = "VR 1.0\n"
                for _, row in df.iterrows():
                    texto_registro = "PT J\n"
                    campos_agregados = False
                    for campo_df, campo_txt in mapeo.items():
                        if campo_df in campos_seleccionados:
                            valor = row[campo_df]
                            if valor and str(valor).strip():
                                if campo_df in ['Authors', 'Author full names', 'References']:
                                    elementos = str(valor).split('; ')
                                    texto_registro += f"{campo_txt} {elementos[0]}\n"
                                    texto_registro += ''.join([f"   {e}\n" for e in elementos[1:] if e.strip()])
                                else:
                                    texto_registro += f"{campo_txt} {str(valor).replace('\n', '\n   ')}\n"
                                campos_agregados = True
                    if campos_agregados:
                        texto_registro += "ER\n\n"
                        texto += texto_registro
                texto += "EF\n"
                return texto

            mapeo_codigos = {
                'Authors': 'AU', 'Author full names': 'AF', 'Title': 'TI', 'Source title': 'SO',
                'Language of Original Document': 'LA', 'Document Type': 'DT', 'Author Keywords': 'DE',
                'Index Keywords': 'ID', 'Abstract': 'AB', 'Correspondence Address': 'C1', 'Affiliations': 'C3',
                'References': 'CR', 'Cited by': 'TC', 'Publisher': 'PU', 'ISSN': 'SN',
                'Abbreviated Source Title': 'J9', 'Year': 'PY', 'Volume': 'VL', 'Issue': 'IS',
                'Page start': 'BP', 'Page end': 'EP', 'DOI': 'DI', 'Page count': 'PG',
                'Source': 'UT', 'Funding Texts': 'FX'
            }

            texto_global = generar_texto(df_final, list(mapeo_codigos.keys()), mapeo_codigos)
            st.session_state["parte4_txt_bytes"] = texto_global.encode()

            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
                inicio = 0
                while inicio < len(df_final):
                    fin = min(inicio + 500, len(df_final))
                    texto_lote = generar_texto(df_final.iloc[inicio:fin], list(mapeo_codigos.keys()), mapeo_codigos)
                    zipf.writestr(f"Scopus+WOS(Dep {inicio+1}-{fin}).txt", texto_lote)
                    inicio = fin
            st.session_state["parte4_zip_bytes"] = zip_buffer.getvalue()

            st.session_state["parte4_generada"] = True
            st.rerun()

# ----------- SECCIÓN PERSISTENTE (muestra mientras parte4_generada == True) -----------
if st.session_state.get("parte4_generada"):
    st.markdown("### 📥 Descarga tus archivos finales:")
    st.download_button("📥 Excel", st.session_state["parte4_excel_bytes"], "Scopus+WOS(Depurado).xlsx")
    st.download_button("📥 CSV", st.session_state["parte4_csv_bytes"], "Scopus+WOS(Depurado).csv")
    st.download_button("📥 RIS", st.session_state["parte4_ris_bytes"], "Scopus+WOS(Depurado).ris")
    st.download_button("📥 TXT completo", st.session_state["parte4_txt_bytes"], "Scopus+WOS(Depurado).txt")
    st.download_button("📥 TXT por lotes (ZIP)", st.session_state["parte4_zip_bytes"], "Scopus+WOS_lotes.zip")

    # Histogramas
    def mostrar_top(df, columna, titulo, color):
        top_vals = df[columna].str.split(';').explode().str.strip().value_counts().head(25)
        fig, ax = plt.subplots(figsize=(8, 4))
        top_vals.plot(kind='bar', ax=ax, color=color)
        ax.set_title(titulo)
        plt.xticks(rotation=90)
        st.pyplot(fig)

    st.markdown("### 📊 Informes de resumen final")
    st.write(f"**Registros finales:** {df_final.shape[0]}")
    mostrar_top(df_final, 'Authors', "👤 Top 25 autores", 'green')
    mostrar_top(df_final, 'Author Keywords', "🔑 Top 25 Author Keywords", 'skyblue')
    mostrar_top(df_final, 'Index Keywords', "🏷️ Top 25 Index Keywords", 'salmon')
    mostrar_top(df_final, 'References', "📚 Top 20 Cited References", 'orange')
    st.success("✅ Archivos finales generados correctamente.")

# Si la parte 4 no está habilitada pero ya se hizo algo, mostrar el botón gris
if not habilitar_parte4:
    if st.session_state.get("procesado") or st.session_state.get("depuracion_realizada"):
        mostrar_boton_finales_bloqueado()
