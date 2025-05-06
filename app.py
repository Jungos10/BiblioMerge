
# Versión completa de la app: incluye partes 1, 2, 3 (depuración opcional) y 4 (exportación final)
# Requiere: streamlit, pandas, matplotlib, seaborn, openpyxl

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import zipfile
import io
from collections import defaultdict
from datetime import datetime

st.set_page_config(page_title="Fusionador Scopus + WoS", layout="wide")
st.title("Fusionador de archivos bibliográficos: Scopus + WoS")
st.markdown("Sube tus archivos CSV de Scopus y TXT de WoS para fusionarlos y depurarlos.")

# Parte 1: CARGA DE ARCHIVOS
scopus_files = st.file_uploader("Archivos Scopus (CSV)", type="csv", accept_multiple_files=True, key="scopus")
wos_files = st.file_uploader("Archivos WoS (TXT)", type="txt", accept_multiple_files=True, key="wos")

df_final = None
autores = None
df_author_keywords = None
df_index_keywords = None
df_references_info = None
dfwos = None
dfsco = None

if scopus_files and wos_files:
    if st.button("Fusionar"):
        with st.spinner("Fusionando y procesando..."):
            # --- PARTE 2: Fusión y limpieza ---
            from fusionador_partes.partes_1_y_2 import procesar_datos
            resultado = procesar_datos(scopus_files, wos_files)
            dfsco, dfwos, df_final, autores, df_author_keywords, df_index_keywords, df_references_info, duplicados_final, duplicados_sin_doi, df_concatenated_sin_duplicados = resultado

            st.success("Fusión completada correctamente.")
            st.session_state['df_final'] = df_final
            st.session_state['autores'] = autores
            st.session_state['df_author_keywords'] = df_author_keywords
            st.session_state['df_index_keywords'] = df_index_keywords
            st.session_state['df_references_info'] = df_references_info
            st.session_state['dfsco'] = dfsco
            st.session_state['dfwos'] = dfwos
            st.session_state['duplicados_final'] = duplicados_final
            st.session_state['duplicados_sin_doi'] = duplicados_sin_doi
            st.session_state['df_concatenated_sin_duplicados'] = df_concatenated_sin_duplicados

# Parte 3: DEPURACIÓN OPCIONAL
if st.session_state.get('df_final') is not None:
    st.markdown("### (Opcional) Depuración avanzada de campos")

    if st.checkbox("Quiero aplicar depuración desde Excel externo"):
        depuracion_file = st.file_uploader("Selecciona el archivo Excel con las tablas de conversión", type="xlsx", key="depuracion")
        if depuracion_file and st.button("Aplicar depuración"):
            with st.spinner("Aplicando depuración..."):
                from fusionador_partes.parte_3_depuracion import aplicar_depuracion
                df_final = aplicar_depuracion(depuracion_file, st.session_state['df_final'],
                                              st.session_state['autores'],
                                              st.session_state['df_author_keywords'],
                                              st.session_state['df_index_keywords'],
                                              st.session_state['df_references_info'])
                st.session_state['df_final'] = df_final
                st.success("Depuración aplicada correctamente.")

# Parte 4: EXPORTACIÓN
if st.session_state.get('df_final') is not None:
    st.markdown("### Generación de ficheros finales")
    if st.button("Generar ficheros finales"):
        with st.spinner("Generando ficheros e informes..."):
            from fusionador_partes.parte_4_exportacion import generar_informes_y_ficheros
            generar_informes_y_ficheros(
                st.session_state['df_final'],
                st.session_state['dfsco'],
                st.session_state['dfwos'],
                st.session_state['duplicados_final'],
                st.session_state['duplicados_sin_doi'],
                st.session_state['df_concatenated_sin_duplicados']
            )
