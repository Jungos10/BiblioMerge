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
    st.dataframe(dfsco.head())

# ----------- PROCESAMIENTO DE WOS ------------
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

# Una vez cargados ambos, mostramos botón para continuar con la fusión
if 'dfsco' in locals() and 'dfwos' in locals():
    if st.button("Fusionar y depurar registros"):
        st.info("🔧 Procesando y fusionando registros. Esto puede tardar unos segundos...")
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

        st.success("✔️ Datos fusionados y normalizados correctamente.")
        st.dataframe(df_concatenated.head())
