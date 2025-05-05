
import streamlit as st
import pandas as pd
import io

st.title("Aplicación de Análisis Bibliométrico")

# Subida de archivos CSV de Scopus
st.subheader("Carga de archivos CSV de Scopus")
uploaded_files = st.file_uploader("Selecciona uno o varios archivos de Scopus (CSV)", type=["csv"], accept_multiple_files=True)

dfsco_list = []
if uploaded_files:
    for file in uploaded_files:
        df = pd.read_csv(file)
        dfsco_list.append(df)
    dfsco = pd.concat(dfsco_list, ignore_index=True)
    st.success("Archivos de Scopus cargados y concatenados correctamente.")


# @title EJECUCIÓN DE LA FUSIÓN Y PRIMEROS INFORMES
#---------IMPORTAMOS AMBOS ARCHIVOS, MAPEAMOS, Y LOS UNIMOS. ADECUAMOS UN CAMPO DE IDENTIFICACIÓN Y LIMPIAMOS CAMPOS CON 'NaN'-----

# Mapeamos el archivo WOS(dfwos) con el arcivo Scopus (dfsco)
mapping = {'AU' : 'Authors' ,'AF' : 'Author full names','TI': 'Title', 'PY' : 'Year',\
           'SO' : 'Source title', 'VL' : 'Volume', 'IS' : 'Issue', 'CR' : 'References', 'BP' : 'Page start',\
           'EP' : 'Page end', 'PG' : 'Page count', 'TC' : 'Cited by', 'DI' : 'DOI',\
           'C3' : 'Affiliations', 'AB' : 'Abstract', 'DE' : 'Author Keywords', 'ID' : 'Index Keywords',\
           'FX' : 'Funding Texts', 'RP' : 'Correspondence Address',\
           'PU' : 'Publisher', 'SN' : 'ISSN', 'LA' : 'Language of Original Document',\
           'J9' : 'Abbreviated Source Title', 'DT' : 'Document Type', 'UT' : 'EID', 'C1': 'Authors with affiliations'}

# Creamos un dfwos_selected igual que dfwos, y al primero le renombramos las columnas relevantes según el mapeo anterior
dfwos_selected = dfwos.rename(columns=mapping)[mapping.values()]

# Creamos en el df de WoS el campo 'Source' similar al de Scopus con 'WOS' y asi con en la fusión identifivamos el origen de cada registro
dfwos_selected['Source'] = 'WOS'

# Concatenar dfwos_selected a dfsco a lo largo del eje de las filas y tenemos un dataframe que contiene todos los registros de Scopus y de WOS
df_concatenated = pd.concat([dfsco, dfwos_selected], ignore_index=True)

# Ahora vamos a limpiar la base de datos de valores "NaN" reemplazando por vacíos
df_concatenated.fillna('', inplace=True)


#Adaptamos el valor del campo UT(WoS)=EID(Scopus) para que lo reconozca Bibliometrix(Biblioshiny) y SciebtoPy como Scopus
df_concatenated['EID'] = (
    df_concatenated['EID']
    .astype(str)  # Asegura que todos los valores sean cadenas
    .str.replace('WOS:', '2-w-')  # Realiza el reemplazo
)


# Vamos a transformar todo en minúsculas con excepciones(por alguna razón para Scopus algunos campos los considera texto...???)
# Iteramos sobre cada columna y aplicar str.lower() salvo las excepciones

excepciones = ['Year', 'Cited by', 'Volume', 'Page count', 'Issue', 'Art.No.', 'Page start', 'Page end']

for columna in df_concatenated.columns:
    if columna not in excepciones and df_concatenated[columna].dtype == 'object':
        df_concatenated[columna] = df_concatenated[columna].str.lower()

# Reemplazar ",," con "," para evitar que Bibexcel no admita los registros a partir de esa casuística
df_concatenated['References'] = df_concatenated['References'].str.replace(",,", ",")

# Sustituimos caracteres que Bibexcel y Scimat no son capaces de entender y generan simbolos raros
df_concatenated.replace("‘", "'", regex=True, inplace=True)
df_concatenated.replace("’", "'", regex=True, inplace=True)
df_concatenated.replace("–", "-", regex=True, inplace=True)
df_concatenated.replace("“", '"', regex=True, inplace=True)
df_concatenated.replace("”", '"', regex=True, inplace=True)
df_concatenated.replace("ε", "e", regex=True, inplace=True)
df_concatenated.replace("ℓ", "l", regex=True, inplace=True)
df_concatenated.replace("γ", "y", regex=True, inplace=True)
df_concatenated.replace(",,", ",", regex=True, inplace=True)
df_concatenated.replace("ï", "i", regex=True, inplace=True)
df_concatenated.replace("á", "a", regex=True, inplace=True)
df_concatenated.replace("é", "e", regex=True, inplace=True)
df_concatenated.replace("í", "i", regex=True, inplace=True)
df_concatenated.replace("ó", "o", regex=True, inplace=True)
df_concatenated.replace("ú", "u", regex=True, inplace=True)
df_concatenated.replace("ñ", "n", regex=True, inplace=True)
df_concatenated.replace("ü", "u", regex=True, inplace=True)
df_concatenated.replace("š", "s", regex=True, inplace=True)
df_concatenated.replace("ř", "r", regex=True, inplace=True)
df_concatenated.replace("ö", "o", regex=True, inplace=True)
df_concatenated.replace("ņ", "n", regex=True, inplace=True)
df_concatenated.replace("ç", "c", regex=True, inplace=True)
df_concatenated.replace("ć", "c", regex=True, inplace=True)
df_concatenated.replace("ş", "s", regex=True, inplace=True)
df_concatenated.replace("ã", "a", regex=True, inplace=True)
df_concatenated.replace("â", "a", regex=True, inplace=True)
df_concatenated.replace("ń", "n", regex=True, inplace=True)
df_concatenated.replace("ż", "z", regex=True, inplace=True)
df_concatenated.replace("ė", "e", regex=True, inplace=True)
df_concatenated.replace("č", "c", regex=True, inplace=True)
df_concatenated.replace("ß", "B", regex=True, inplace=True)
df_concatenated.replace("ä", "a", regex=True, inplace=True)
df_concatenated.replace("ê", "e", regex=True, inplace=True)
df_concatenated.replace("ł", "t", regex=True, inplace=True)
df_concatenated.replace("ı", "i", regex=True, inplace=True)
df_concatenated.replace("å", "a", regex=True, inplace=True)
df_concatenated.replace("ą", "a", regex=True, inplace=True)
df_concatenated.replace("ĭ", "i", regex=True, inplace=True)
df_concatenated.replace("ø", "o", regex=True, inplace=True)
df_concatenated.replace("ý", "y", regex=True, inplace=True)
#df_concatenated.replace("ä", "a", regex=True, inplace=True)
df_concatenated.replace("≥", ">=", regex=True, inplace=True)
df_concatenated.replace("≤", "<=", regex=True, inplace=True)
df_concatenated.replace("è", "e", regex=True, inplace=True)
df_concatenated.replace("ǐ", "i", regex=True, inplace=True)
df_concatenated.replace("—", "-", regex=True, inplace=True)
df_concatenated.replace("×", "x", regex=True, inplace=True)
df_concatenated.replace("‐", "-", regex=True, inplace=True)


# Reemplazar en 'Authors'la cadena ".-" con "." para evitar disonancias estéticas en los informes
df_concatenated['Authors'] = df_concatenated['Authors'].str.replace(".-", ".")

# Eliminar puntos y comas en la columna "Authors" del DataFrame df_concatenated para tener el mismos formato (Bibliochiny parte en dos los nombre si hay "," si el formato de datos es Scopus)
df_concatenated['Authors'] = df_concatenated['Authors'].str.replace(r'[.,]', '', regex=True)

# Hasta aquí tenemos todos los registros de Scopus y todos los registros de WOS en "estructura Scopus".
# Puede haber registros repetidos que debemos eliminar. Tenemos que localizarlos:
# El claro identificador de un registro es el 'DOI' (DNI del artículo), pero no todos los registros tienen 'DOI' (del orden del 10%)

#-----LOCALIZAMOS REGISTROS REPETIDOS POR VENIR DE LAS DOS FUENTES. PARA EL CASO DE TENER 'DOI' Y PARA EL CASO DE NO TENERLO----------
#----- LOCALIZAMOS REGISTROS REPETIDOS POR VENIR DE LAS DOS FUENTES -----

# ----- FASE 1: Eliminación de duplicados con DOI -----
df_sin_vacios = df_concatenated[df_concatenated['DOI'] != '']

# Identificamos registros duplicados según DOI
duplicados_doi = df_sin_vacios[df_sin_vacios.duplicated(subset=['DOI'], keep=False)]

# Eliminamos preferentemente los que NO son "scopus"
indices_a_eliminar_doi = set()
for doi, group in duplicados_doi.groupby('DOI'):
    if 'scopus' in group['Source'].values:
        indices_a_eliminar_doi.update(group[group['Source'] != 'scopus'].index)
    else:
        indices_a_eliminar_doi.update(group.index[1:])  # Mantenemos el primero

# Guardamos los registros eliminados ANTES de borrarlos
duplicados_doi_final = df_concatenated.loc[df_concatenated.index.isin(indices_a_eliminar_doi)].copy()

# Eliminamos los duplicados detectados con DOI
df_concatenated = df_concatenated.drop(list(indices_a_eliminar_doi), errors='ignore')

# ----- FASE 2: Eliminación de duplicados sin DOI -----
# Creamos la clave 'A_T_Y' asegurando que no haya valores nulos
df_concatenated['A_T_Y'] = (
    df_concatenated['Authors'].fillna("").str[:3] +
    df_concatenated['Title'].fillna("").str[:8] +
    df_concatenated['Abstract'].fillna("").str[:6]
).str.lower()

# Identificamos duplicados según 'A_T_Y'
duplicados_sin_doi = df_concatenated[df_concatenated.duplicated(subset=['A_T_Y'], keep=False)]

# Eliminamos preferentemente los registros sin DOI si hay una coincidencia con uno con DOI
indices_a_eliminar_sin_doi = set()
for key, group in duplicados_sin_doi.groupby('A_T_Y'):
    tiene_doi = group['DOI'] != ''
    if tiene_doi.any():  # Si hay un DOI en el grupo, eliminamos los sin DOI
        indices_a_eliminar_sin_doi.update(group[~tiene_doi].index)
    else:  # Si ninguno tiene DOI, aplicamos la lógica de "scopus"
        if 'scopus' in group['Source'].values:
            indices_a_eliminar_sin_doi.update(group[group['Source'] != 'scopus'].index)
        else:
            indices_a_eliminar_sin_doi.update(group.index[1:])  # Mantenemos el primero

# Guardamos los registros eliminados ANTES de borrarlos
duplicados_sin_doi_final = df_concatenated.loc[df_concatenated.index.isin(indices_a_eliminar_sin_doi)].copy()

# Eliminamos los duplicados detectados sin DOI
df_concatenated = df_concatenated.drop(list(indices_a_eliminar_sin_doi), errors='ignore')

# Eliminamos la columna temporal 'A_T_Y'
df_concatenated.drop(columns=['A_T_Y'], inplace=True)

# DataFrame final sin duplicados
df_concatenated_sin_duplicados = df_concatenated.copy()

# 🔹 🔹 🔹 Concatenar duplicados eliminados 🔹 🔹 🔹
duplicados_final = pd.concat([duplicados_doi_final, duplicados_sin_doi_final], ignore_index=True)


#------PROCESO DE ELIMINACIÓN DE DUPLICADOS------------------------------------------------------
# los registros de duplicados conservan en nº de registro que tenían en "df_concatenated", con lo cual recogemos esos indices
#indices_a_eliminar = duplicados_final.index.tolist()

# Creamos un "df_concatenated_sin_duplicados" donde cargamos todos los registros de "df_concatenated" eliminando los que estaban en duplicados
#df_concatenated_sin_duplicados = df_concatenated.drop(indices_a_eliminar)

# Mostrar el DataFrame resultante sin duplicados
#df_concatenated_sin_duplicados

#--------IDENTIDFICAMOS AUTORES CON DIFERENTE GRAFÍA Y UNIFICAMOS EN UNA ÚNICA GRAFÍA---------------------
import pandas as pd

# Función para crear el DataFrame de conversión, unificando autores con ID
def crear_df_conversion(df):
    codigos_autores = {}
    grafia_asignada = {}

    # Asegurar que las columnas sean de tipo string y sin valores NaN
    df['Author(s) ID'] = df['Author(s) ID'].fillna('').astype(str)
    df['Authors'] = df['Authors'].fillna('').astype(str)
    df['Author full names'] = df['Author full names'].fillna('').astype(str)

    # Iterar sobre las filas del DataFrame
    for index, row in df.iterrows():
        # Extraer y limpiar datos de autores, nombres largos e IDs
        autores = [autor.strip() for autor in row['Authors'].split(';') if autor.strip()]
        nombres_largos = [nombre.strip() for nombre in row['Author full names'].split(';') if nombre.strip()]
        codigos = [codigo.strip() for codigo in row['Author(s) ID'].split(';') if codigo.strip()]

        # Asociar autores con sus respectivos IDs
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

    # Ordenar autores por frecuencia de aparición
    autores_ordenados = {}
    for codigo, data in sorted(codigos_autores.items(), key=lambda x: x[1]['articles'], reverse=True):
        nombre_autor = data['autor']
        if nombre_autor not in autores_ordenados:
            autores_ordenados[nombre_autor] = []
        autores_ordenados[nombre_autor].append((codigo, data))

    # Asignar una grafía unificada a cada autor
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

    # Crear un DataFrame con los autores unificados
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

# Función para reemplazar autores en el DataFrame original
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

# Crear DataFrame de conversión y realizar reemplazos
df_conversion = crear_df_conversion(df_concatenated_sin_duplicados)
df_concatenated_sin_duplicados, total_reemplazos = realizar_reemplazos(df_concatenated_sin_duplicados, df_conversion)

# Procesar autores sin ID para incluirlos en la tabla unificada
df_autores_sin_cod = df_concatenated_sin_duplicados[df_concatenated_sin_duplicados['Author(s) ID'].apply(lambda x: str(x).strip()) == ''].copy()
df_autores_sin_cod['Indices'] = df_autores_sin_cod.index

df_autores_sin_cod = df_autores_sin_cod.assign(Authors=df_autores_sin_cod['Authors'].str.split(';'),
                                                 Author_full_names=df_autores_sin_cod['Author full names'].str.split(';'))
df_autores_sin_cod = df_autores_sin_cod.explode(['Authors', 'Author_full_names'])
df_autores_sin_cod['Authors'] = df_autores_sin_cod['Authors'].str.strip()
df_autores_sin_cod['Author_full_names'] = df_autores_sin_cod['Author_full_names'].str.strip()
df_autores_sin_cod['Posiciones'] = df_autores_sin_cod.groupby(['Authors', 'Author_full_names']).cumcount()
df_autores_sin_cod['Articles'] = df_autores_sin_cod.groupby(['Authors', 'Author_full_names'])['Authors'].transform('count')

df_autores_sin_cod = df_autores_sin_cod.groupby(['Authors', 'Author_full_names']).agg({'Indices': lambda x: '; '.join(map(str, x)), 'Posiciones': lambda x: '; '.join(map(str, x)), 'Articles': 'first'}).reset_index()

# Crear tabla unificada de autores
autores = df_conversion[['Authors', 'Author full names', 'Author(s) ID', 'Indices', 'Posiciones', 'Articles']].copy()
autores['Authors'] = autores['Authors'].str.strip()
autores = pd.concat([autores, df_autores_sin_cod.rename(columns={'Author_full_names': 'Author full names'})], ignore_index=True)
autores['New Author'] = '0-change-0'


#-----------CREAMOS UNA BASE DE DATOS QUE RECOJA LAS 'AUTHOR KEYWORDS' Y SU NÚMERO DE APARICIONES------------
from collections import defaultdict

# Creamos un diccionario para almacenar las palabras clave y sus apariciones
author_keywords_dict = defaultdict(list)

# Iteramos sobre el DataFrame df_concatenated_sin_duplicados
for index, row in df_concatenated_sin_duplicados.iterrows():
    author_keywords = row['Author Keywords'].split(';')
    for position, keyword in enumerate(author_keywords):
        # Agregamos una condición para evitar las palabras clave vacías
        if keyword.strip():  # Verifica si la palabra clave no está vacía
            author_keywords_dict[keyword.strip()].append((index, position))

# Creamos listas para cada columna del nuevo DataFrame
author_keywords_list = []
author_indices_list = []
author_posiciones_list = []
author_conteo_list = []

# Iteramos sobre el diccionario de palabras clave
for keyword, apariciones in author_keywords_dict.items():
    # Guardamos los datos en las listas
    author_keywords_list.append(keyword)
    indices, posiciones = zip(*apariciones)
    # Convertimos los índices y posiciones en cadenas separadas por punto y coma
    indices_str = ';'.join(map(str, indices))
    posiciones_str = ';'.join(map(str, posiciones))
    author_indices_list.append(indices_str)
    author_posiciones_list.append(posiciones_str)
    author_conteo_list.append(len(apariciones))

# Creamos el nuevo DataFrame
df_author_keywords = pd.DataFrame({
    'Author Keyword': author_keywords_list,
    'Indices': author_indices_list,
    'Posiciones': author_posiciones_list,
    'Conteo': author_conteo_list
})

# Creamos un nuevo campo en el que posteriormente el usuario podrá hacer una tabla de conversión de Keywords
df_author_keywords['New Keyword'] = '0-change-0'

#-----------CREAMOS UNA BASE DE DATOS QUE RECOJA LAS 'INDEX KEYWORDS' Y SU NÚMERO DE APARICIONES------------
# Creamos un diccionario para almacenar las palabras clave y sus apariciones
index_keywords_dict = defaultdict(list)

# Iteramos sobre el DataFrame df_concatenated_sin_duplicados
for index, row in df_concatenated_sin_duplicados.iterrows():
    index_keywords = row['Index Keywords'].split(';')
    for position, keyword in enumerate(index_keywords):
        if keyword.strip():  # Verificamos que la palabra clave no esté vacía
            index_keywords_dict[keyword.strip()].append((index, position))

# Creamos listas para cada columna del nuevo DataFrame
index_keywords_list = []
index_indices_list = []
index_posiciones_list = []
index_conteo_list = []

# Iteramos sobre el diccionario de palabras clave
for keyword, apariciones in index_keywords_dict.items():
    # Guardamos los datos en las listas
    index_keywords_list.append(keyword)
    indices, posiciones = zip(*apariciones)
    index_indices_list.append(';'.join(map(str, indices)))  # Formatear los índices correctamente
    index_posiciones_list.append(';'.join(map(str, posiciones)))  # Formatear las posiciones correctamente
    index_conteo_list.append(len(apariciones))

# Creamos el nuevo DataFrame
df_index_keywords = pd.DataFrame({
    'Index Keywords': index_keywords_list,
    'Indices': index_indices_list,
    'Posiciones': index_posiciones_list,
    'Conteo': index_conteo_list
})

# Creamos un nuevo campo en el que posteriormente el usuario podrá hacer una tabla de conversión de Keywords
df_index_keywords['New Keyword'] = '0-change-0'


#-----------CREAMOS UNA BASE DE DATOS QUE RECOJA LAS 'REFERENCES' (Cyted References) Y SU NÚMERO DE APARICIONES------------
from collections import defaultdict
import pandas as pd

# df_concatenated_sin_duplicados es el DataFrame original que contiene la columna 'References'

# Creamos un diccionario para almacenar las referencias y sus apariciones
references_dict = defaultdict(list)

# Iteramos sobre el DataFrame df_concatenated_sin_duplicados
for index, row in df_concatenated_sin_duplicados.iterrows():
    references = row['References'].split(';')
    for position, reference in enumerate(references):
        # Agregamos una condición para evitar las referencias vacías
        if reference.strip():  # Verifica si la referencia no está vacía
            references_dict[reference.strip()].append((index, position))

# Creamos listas para cada columna del nuevo DataFrame
reference_list = []
indices_list = []
positions_list = []
count_list = []

# Iteramos sobre el diccionario de referencias
for reference, apariciones in references_dict.items():
    # Guardamos los datos en las listas
    reference_list.append(reference)
    indices, posiciones = zip(*apariciones)
    # Convertimos los índices y posiciones en cadenas separadas por punto y coma
    indices_str = ';'.join(map(str, indices))
    posiciones_str = ';'.join(map(str, posiciones))
    indices_list.append(indices_str)
    positions_list.append(posiciones_str)
    count_list.append(len(apariciones))

# Creamos el nuevo DataFrame
df_references_info = pd.DataFrame({
    'References': reference_list,
    'Indices': indices_list,
    'Posiciones': positions_list,
    'Count': count_list
})

# Creamos un nuevo campo en el que posteriormente el usuario podrá hacer una tabla de conversión de Referencias
df_references_info['New Reference'] = '0-change-0'
# ------------------------------------++++++++++++++++++++++++++++++++-----------------------------

# Creamos un df_final, copia de df_concatenated_sin_duplicados, sobre el que haremos las depuraciones de Autores, Author Keywords e Idex Keywords
df_final = df_concatenated_sin_duplicados.copy()

# Convertir los campos 'Volume', 'Cited by' y 'Page count' a tipo de dato numérico, rellenando los valores no válidos con NaN
df_final[['Volume', 'Cited by', 'Page count', 'Year']] = df_final[['Volume', 'Cited by', 'Page count', 'Year']].apply(pd.to_numeric, errors='coerce')

# Rellenar los valores vacíos en las columnas 'Volume', 'Cited by' y 'Page count' con 0
df_final[['Volume', 'Cited by', 'Page count', 'Year']] = df_final[['Volume', 'Cited by', 'Page count', 'Year']].fillna(0)

# Convertir los campos 'Volume', 'Cited by' y 'Page count' a tipo de dato entero en una sola línea
df_final[['Volume', 'Cited by', 'Page count', 'Year']] = df_final[['Volume', 'Cited by', 'Page count', 'Year']].astype(int)

# Exportamos a DRIVE el resultado de la fusión (sin depurar autores y keywords), los registros duplicados,
# y Excel Autores, Author Keywords e Idex Keywordsde autores, para facilitar la depuración

# Creamos una carpeta 'Fusión Scopus+WOS - Rdo preeliminar'
import os

# Especifica el nombre de la carpeta donde deseas organizar los archivos
folder_name = 'Fusión Scopus+WOS - Rdo preeliminar'

# Ruta completa de la carpeta en Google Drive
folder_path = '/content/drive/My Drive/' + folder_name

# Verifica si la carpeta existe
if not os.path.exists(folder_path):
    # Crea la carpeta si no existe
    try:
        os.makedirs(folder_path)
        print(f'Se ha creado la carpeta "{folder_name}" en Google Drive.')
    except OSError as e:
        print(f'Error al crear la carpeta "{folder_name}": {e}')
else:
    print(f'\nUtilizando la carpeta existente "{folder_name}" en Google Drive.')

# Guardar cada DataFrame en un archivo dentro de la carpeta especificada
#df_concatenated_sin_duplicados.to_csv(os.path.join(folder_path, 'Scopus+WOS.csv'), index=False)
df_concatenated_sin_duplicados.to_excel(os.path.join(folder_path, 'Scopus+WOS.xlsx'), index=False)
duplicados_final.to_excel(os.path.join(folder_path, 'Scopus+WOS(duplicados).xlsx'), index=False)
#autores.to_excel(os.path.join(folder_path, 'autores.xlsx'), index=False)
#df_author_keywords.to_excel(os.path.join(folder_path, 'Author Keywords.xlsx'), index=False)
#df_index_keywords.to_excel(os.path.join(folder_path, 'Index Keywords.xlsx'), index=False)
#df_references_info.to_excel(os.path.join(folder_path, 'References.xlsx'), index=False)

print('Archivos guardados exitosamente en la carpeta "{}" en Google Drive.\n'.format(folder_name))

# Especificar la ruta completa del archivo de Excel en Google Drive
excel_file_path = '/content/drive/My Drive/Fusión Scopus+WOS - Rdo preeliminar/Tablas_para_depuraciones.xlsx'

# Crear un objeto ExcelWriter para escribir en el archivo Excel en Google Drive
with pd.ExcelWriter(excel_file_path, engine='openpyxl') as writer:
           # Escribir cada DataFrame en una hoja diferente
        autores.to_excel(writer, sheet_name='Authors', index=False)
        df_author_keywords.to_excel(writer, sheet_name='Author Keywords', index=False)
        df_index_keywords.to_excel(writer, sheet_name='Index Keywords', index=False)
        df_references_info.to_excel(writer, sheet_name='Cited References', index=False)

# Informes
print("*****Ficheros generados*****","\n")
print("""En Google Drive, en la carpeta Fusión Scopus+WOS - Rdo preeliminar, se han generado los ficheros:\n
- Scopus+WOS.xlsx: con el resultado de la fusión y eliminación de duplicados, sin depuración
- Scopus+WOS(duplicados).xlsx: con los registros duplicados encontrados y que han sido eliminados
- Tablas_para_depuraciones.xlsx: donde se recogen los autores, las Author Keywords, las Index Keywords
  y las Cited References, con tablas preparadas para que el analista haga sustituciones o agrupaciones
  según su criterio
""")
print("*****Información de la fusión de las bases de datos Scopus y WOS*****", "\n")
print("Registros Scopus:", dfsco.shape[0], "\t", "Columnas Scopus:", dfsco.shape[1])
print("Registros WOS:", dfwos.shape[0], "\t", "Columnas WOS:", dfwos.shape[1], "\n")
print("Registros Duplicados: ",duplicados_final.shape[0], "\t", "de los cuales sin DOI: ",duplicados_sin_doi.shape[0], "\n")
print("Registros finales Scopus + WOS: ",df_concatenated_sin_duplicados.shape[0], "\t", "Columnas finales Scopus + WOS: ",df_concatenated_sin_duplicados.shape[1], "\n")
print("*****Información sobre autores*****", "\n")
import matplotlib.pyplot as plt
# Ordenar el DataFrame por la columna 'Articles' de forma descendente
autores_sorted = autores.sort_values(by='Articles', ascending=False)
# Seleccionar los 20 autores con más artículos
top_20_autores = autores_sorted.head(20)
# Crear el histograma
plt.figure(figsize=(6, 4))
plt.bar(top_20_autores['Authors'], top_20_autores['Articles'], color='skyblue')
plt.xlabel('Autores')
plt.ylabel('Número de Artículos')
plt.title('Top 20 Autores con Más Artículos')
plt.xticks(rotation=90)
plt.tight_layout()
plt.show()
#print("Autores con diferentes grafías", num_codigos_con_reemplazos,"\t", "Número correcciones realizadas:", total_reemplazos, "\n")

print("*****Información sobre keywords*****", "\n")
# HISTOGRAMA DE AUTHOR KEYWORDS
# Ordena el DataFrame por la columna 'Conteo' de manera descendente
df_sorted = df_author_keywords.sort_values(by='Conteo', ascending=False)

# Toma los primeros 20 valores de 'Authors keywords' y 'Conteo'
top_20_keywords = df_sorted.head(25)

# Gráfica de histograma
plt.figure(figsize=(7, 6))
plt.bar(top_20_keywords['Author Keyword'], top_20_keywords['Conteo'], color='skyblue')
plt.xlabel('Authors Keywords')
plt.ylabel('Conteo')
plt.title('Top 25 Author Keywords')
plt.xticks(rotation=90)  # Rotación del eje x para mayor legibilidad
plt.tight_layout()
plt.show()

print("Nº de Author Keywords (sin depurar):", df_author_keywords.shape[0], "\n")
# HISTOGRAMA DE INDEX KEYWORDS
# Ordena el DataFrame por la columna 'Conteo' de manera descendente
df_sorted = df_index_keywords.sort_values(by='Conteo', ascending=False)

# Separa los valores de 'Indices' y 'Posiciones' por punto y coma
df_sorted['Indices'] = df_sorted['Indices'].apply(lambda x: ';'.join(str(i) for i in x))
df_sorted['Posiciones'] = df_sorted['Posiciones'].apply(lambda x: ';'.join(str(i) for i in x))

# Toma los primeros 25 valores de 'Index Keywords' y 'Conteo'
top_25_keywords = df_sorted.head(25)

# Gráfica de histograma
plt.figure(figsize=(7, 6))
plt.bar(top_25_keywords['Index Keywords'], top_25_keywords['Conteo'], color='skyblue')
plt.xlabel('Index Keywords')
plt.ylabel('Conteo')
plt.title('Top 25 Index Keywords')
plt.xticks(rotation=90)  # Rotación del eje x para mayor legibilidad
plt.tight_layout()
plt.show()

print("Nº de Index Keywords (sin depurar):", df_index_keywords.shape[0], "\n")



import streamlit as st
import pandas as pd
import io

st.title("Aplicación de Análisis Bibliométrico")

# Subida de archivos CSV de Scopus
st.subheader("Carga de archivos CSV de Scopus")
uploaded_files = st.file_uploader("Selecciona uno o varios archivos de Scopus (CSV)", type=["csv"], accept_multiple_files=True)

dfsco_list = []
if uploaded_files:
    for file in uploaded_files:
        df = pd.read_csv(file)
        dfsco_list.append(df)
    dfsco = pd.concat(dfsco_list, ignore_index=True)
    st.success("Archivos de Scopus cargados y concatenados correctamente.")


# @title GENERACIÓN DE FICHEROS E INFORMES FINALES
#-----------------------GENERACIÓN DE FICHEROS E INFORMES FINALES----------------------------------------------
# Creamos una carpeta 'Fusión Scopus+WOS - Rdo Final'
import os

# Especifica el nombre de la carpeta donde deseas organizar los archivos
folder_name = 'Fusión Scopus+WOS - Rdo Final'

# Ruta completa de la carpeta en Google Drive
folder_path = '/content/drive/My Drive/' + folder_name

# Verifica si la carpeta existe
if not os.path.exists(folder_path):
    # Crea la carpeta si no existe
    try:
        os.makedirs(folder_path)
        print(f'Se ha creado la carpeta "{folder_name}" en Google Drive.\n')
    except OSError as e:
        print(f'Error al crear la carpeta "{folder_name}": {e}\n')
else:
    print(f'Utilizando la carpeta existente "{folder_name}" en Google Drive.\n')

df_final.to_csv('/content/drive/My Drive/Fusión Scopus+WOS - Rdo Final/Scopus+WOS(Depurado).csv', index=False)
df_final.to_excel('/content/drive/My Drive/Fusión Scopus+WOS - Rdo Final/Scopus+WOS(Depurado).xlsx', index=False)

# @title GENERACIÓN DE FICHERO RIS
# A partir de los datos depurados en df_final, generamos un fichero tipo RIS formato estandarizado de etiquetas desarrollado por Research Information Systems Incorporated
def df_to_ris(df):
    ris_entries = []
    for index, row in df.iterrows():
        authors = str(row['Authors'])
        if isinstance(authors, str):
            authors = authors.split(';')
            # Concatenar todos los autores en una sola cadena con saltos de línea
            author_entry = '\n'.join(['AU  - ' + author.strip() for author in authors]) + '\n'
        else:
            author_entry = ''

        affiliations = str(row['Affiliations'])
        if isinstance(affiliations, str):
            affiliations = affiliations.split(';')
            # Concatenar todas las afiliaciones en una sola cadena con saltos de línea
            affiliation_entry = '\n'.join(['AD  - ' + affiliation.strip() for affiliation in affiliations]) + '\n'
        else:
            affiliation_entry = ''

        author_keywords = str(row['Author Keywords'])
        if isinstance(author_keywords, str):
            author_keywords = author_keywords.split(';')
            # Concatenar todas las palabras clave del autor en una sola cadena con saltos de línea
            keyword_entry = '\n'.join(['KW  - ' + keyword.strip() for keyword in author_keywords]) + '\n'
        else:
            keyword_entry = ''

        # Agregar el literal 'Cited by: ' y el valor del campo 'Cited by'
        cited_by = f"Cited By: {row['Cited by']}\n" if not pd.isnull(row['Cited by']) else ''
        # Agregar el campo 'N1' con el valor del literal 'Cited by: ' y el valor del campo 'Cited by'
        # n1_entry = f"N1  - {cited_by}" if cited_by else ''
       # Agregar el campo 'N1' con la estructura deseada
        from datetime import datetime
        export_date = datetime.today().strftime('%d %B %Y')
        n1_entry = f"N1  - Export Date: {export_date}; {cited_by.strip()}\n"

        ris_entry = "TY  - JOUR\n"
        ris_entry += author_entry
        ris_entry += f"TI  - {row['Title']}\n"
        ris_entry += f"PY  - {row['Year']}\n"
        ris_entry += f"T2  - {row['Source title']}\n"
        ris_entry += f"VL  - {row['Volume']}\n"
        ris_entry += f"IS  - {row['Issue']}\n"
        ris_entry += f"C7  - {row['Art. No.']}\n"
        ris_entry += f"SP  - {row['Page start']}\n"
        ris_entry += f"EP  - {row['Page end']}\n"
        ris_entry += f"DO  - {row['DOI']}\n"
        ris_entry += f"UR  - {row['Link']}\n"
        ris_entry += affiliation_entry
        ris_entry += f"AB  - {row['Abstract']}\n"
        ris_entry += keyword_entry
        ris_entry += f"PB  - {row['Publisher']}\n"
        ris_entry += f"SN  - {row['ISSN']}\n"
        ris_entry += f"LA  - {row['Language of Original Document']}\n"
        ris_entry += f"J2  - {row['Abbreviated Source Title']}\n"
        ris_entry += f"M3  - {row['Document Type']}\n"
        ris_entry += f"DB  - {row['Source']}\n"
        ris_entry += n1_entry  # Agregar el campo 'N1'
        ris_entry += "ER  -\n"  # Agregar la línea para cerrar el registro RIS


        # Mapear los demás campos según sea necesario
        ris_entries.append(ris_entry)
    return ris_entries

# Generar entradas RIS a partir de tu DataFrame
ris_entries = df_to_ris(df_final)

# Escribir las entradas RIS en un archivo
with open('/content/drive/My Drive/Fusión Scopus+WOS - Rdo Final/Scopus+WOS(Depurado).ris', 'w') as f:
    for entry in ris_entries:
        f.write(entry + '\n')

# @title GENERACIÓN DE FICHERO TXT GLOBAL Y PARCIALES DE 500 REGISTROS
def generar_texto(df, campos_seleccionados, mapeo_campos_a_codigos):
    texto = "VR 1.0\n"  # Incluir la línea "VR 1.0" al inicio
    for _, row in df.iterrows():
        texto_registro = "PT J\n"  # Iniciar registro
        campos_agregados = False  # Bandera para verificar si se ha agregado algún campo al registro
        for campo_df, campo_txt in mapeo_campos_a_codigos.items():
            if campo_df in campos_seleccionados:
                valor_campo = row[campo_df]
                if valor_campo and str(valor_campo).strip():  # Verificar si el campo no está vacío
                    # Procesar el campo de acuerdo al tipo
                    if campo_df in ['Authors', 'Author full names', 'References']:
                        elementos = str(valor_campo).split('; ')
                        primer_elemento = f"{campo_txt} {elementos[0]}\n"
                        resto_elementos = [f"   {elem}\n" for elem in elementos[1:] if elem.strip()]
                        texto_registro += primer_elemento + ''.join(resto_elementos)
                    else:
                        # Formatear otros campos que no requieren dividir por '; '
                        valor_formateado = str(valor_campo).replace('\n', '\n   ')
                        valor_formateado = f"{campo_txt} {valor_formateado}\n"
                        texto_registro += valor_formateado
                    campos_agregados = True  # Marcar que se ha agregado al menos un campo al registro
        if campos_agregados:
            texto_registro += "ER\n\n"  # Cerrar registro y dejar una línea vacía después
            texto += texto_registro
    texto += "EF\n"  # Cerrar archivo
    return texto

# Nuevo diccionario que mapea nombres de campos a códigos
mapeo_campos_a_codigos = {
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

# Campos seleccionados
campos_seleccionados = list(mapeo_campos_a_codigos.keys())

# Generar el texto global
texto_global = generar_texto(df_final, campos_seleccionados, mapeo_campos_a_codigos)

# Escribir el texto global en un archivo en Google Drive
ruta_global = '/content/drive/My Drive/Fusión Scopus+WOS - Rdo Final/Scopus+WOS(Depurado).txt'  # Ruta al archivo global
with open(ruta_global, 'w') as file:
    file.write(texto_global)

# Generar y escribir los textos por lotes
ruta_base = '/content/drive/My Drive/Fusión Scopus+WOS - Rdo Final/Scopus+WOS(Dep'
extension = '.txt'
inicio = 0
numero_archivo = 1

while inicio < len(df_final):
    fin = min(inicio + 500, len(df_final))
    texto_lote = generar_texto(df_final.iloc[inicio:fin], campos_seleccionados, mapeo_campos_a_codigos)
    ruta_archivo = f"{ruta_base} {inicio + 1} a {fin}){extension}"
    with open(ruta_archivo, 'w', encoding='utf-8') as file:
        file.write(texto_lote)
    inicio = fin


print("****************FICHEROS GENERADOS***************", "\n")
print("""En Google Drive, en la carpeta Fusión Scopus+WOS - Rdo Final, se han generado los ficheros:\n
- Scopus+WOS(Depurado).xlsx: Fichero depurado formato "xlsx"
- Scopus+WOS(depurado).csv: Fichero depurado formato "csv", de estructura "SCOPUS", leible por VOSviewer
- Scopus+WOS(depurado).txt: Fichero depurado formato "txt", de estructura "WOS", leible por Scimat
- Scopus+WOS(dep X a X+500).txt: Ficheros depurados formato "txt", de 500 en 500 registros de estructura "WOS",
  leibles por Bibexcel
- Scopus+WOS(depurado).ris: Fichero depurado formato "ris", de estructura "SCOPUS", leible por Scimat y Bibexcel,
  sin Cited References

""")

print("********INFORMACIÓN DE LA FUSIÓN DE LAS BASES DE DATOS Scopus y WOS**********", "\n")
print("Registros Scopus:", dfsco.shape[0], "\t", "Columnas Scopus:", dfsco.shape[1])
print("Registros WOS:", dfwos.shape[0], "\t", "Columnas WOS:", dfwos.shape[1], "\n")
print("Registros Duplicados: ",duplicados_final.shape[0], "\t", "de los cuales sin DOI: ",duplicados_sin_doi.shape[0], "\n")
print("Registros finales Scopus + WOS: ",df_concatenated_sin_duplicados.shape[0], "\t", "Columnas finales Scopus + WOS: ",df_concatenated_sin_duplicados.shape[1], "\n")

print("***********INFORMACIÓN SOBRE AUTORES**************", "\n")
import matplotlib.pyplot as plt

# Filtrar y dividir los valores de 'Authors', luego contar su frecuencia
authors_counts = df_final['Authors'].str.split(';').explode().str.strip().dropna().value_counts()

# Excluir los valores vacíos ('')
authors_counts = authors_counts[authors_counts.index != '']

# Contar el número total de valores diferentes de 'Authors'
total_authors = len(authors_counts)

# Imprimir el número total de valores diferentes de 'Authors'
print("Número total de Authors después de la depuración:", total_authors, "\n")

# Seleccionar los 25 valores más comunes en 'Authors'
top_25_authors = authors_counts.head(25)

# Graficar histograma de los 25 valores más comunes en 'Authors'
plt.figure(figsize=(7, 5))
top_25_authors.plot(kind='bar', color='green')
plt.xlabel('Authors')
plt.ylabel('Artículos')
plt.title('Top 25 Autores con más Atículos')
plt.xticks(rotation=90)
plt.tight_layout()
plt.show()
print("***********INFORMACIÓN SOBRE KEYWORDS*****", "\n")

import matplotlib.pyplot as plt

# Filtrar y dividir los valores de 'Author Keywords', luego contar su frecuencia
author_keywords_counts = df_final['Author Keywords'].str.split(';').explode().str.strip().dropna().value_counts()

# Filtrar y dividir los valores de 'Index Keywords', luego contar su frecuencia
index_keywords_counts = df_final['Index Keywords'].str.split(';').explode().str.strip().dropna().value_counts()

# Excluir los valores vacíos ('') de 'Author Keywords' y 'Index Keywords'
author_keywords_counts = author_keywords_counts[author_keywords_counts.index != '']
index_keywords_counts = index_keywords_counts[index_keywords_counts.index != '']

# Contar el número total de valores diferentes de 'Author Keywords' e 'Index Keywords'
total_author_keywords = len(author_keywords_counts)
total_index_keywords = len(index_keywords_counts)

# Imprimir el número total de valores diferentes de 'Author Keywords' e 'Index Keywords'
print("Número total de Author Keywords después de la depuración:", total_author_keywords)
print("Número total de Index Keywords después de la depuración:", total_index_keywords, "\n")

# Seleccionar los 25 valores más comunes en 'Author Keywords'
top_25_author_keywords = author_keywords_counts.head(25)

# Seleccionar los 25 valores más comunes en 'Index Keywords'
top_25_index_keywords = index_keywords_counts.head(25)

# Graficar histograma de los 25 valores más comunes en 'Author Keywords'
plt.figure(figsize=(7, 5))
top_25_author_keywords.plot(kind='bar', color='skyblue')
plt.xlabel('Author Keywords')
plt.ylabel('Frecuencia')
plt.title('Top 25 Author Keywords')
plt.xticks(rotation=90)
plt.tight_layout()
plt.show()

# Graficar histograma de los 25 valores más comunes en 'Index Keywords'
plt.figure(figsize=(7, 5))
top_25_index_keywords.plot(kind='bar', color='salmon')
plt.xlabel('Index Keywords')
plt.ylabel('Frecuencia')
plt.title('Top 25 Index Keywords')
plt.xticks(rotation=90)
plt.tight_layout()
plt.show()

print("***********INFORMACIÓN SOBRE CITED REFERENCES**************", "\n")
import matplotlib.pyplot as plt

# Filtrar y dividir los valores de 'References', luego contar su frecuencia
references_counts = df_final['References'].str.split(';').explode().str.strip().dropna().value_counts()

# Excluir los valores vacíos ('')
references_counts = references_counts[references_counts.index != '']

# Contar el número total de valores diferentes de 'References'
total_references = len(references_counts)

# Imprimir el número total de valores diferentes de 'References'
print("Número total de Cited References después de la depuración:", total_references, "\n")

# Seleccionar los 25 valores más comunes en 'References'
top_20_references = references_counts.head(20)

# Obtener los primeros 20 caracteres de cada etiqueta para el eje X
labels = top_20_references.index.map(lambda x: x[:50])

# Graficar histograma de los 20 valores más comunes en 'References' con etiquetas personalizadas
plt.figure(figsize=(10, 6))  # Ajusta el tamaño de la figura según sea necesario
top_20_references.plot(kind='bar', color='orange')
plt.xlabel('References (primeros 20 caracteres)')
plt.ylabel('Frecuencia')
plt.title('Top 20 Artículos más citados')
plt.xticks(range(len(labels)), labels, rotation=90)  # Usar las etiquetas personalizadas en el eje X
plt.tight_layout()
plt.show()