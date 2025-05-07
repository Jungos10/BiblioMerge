
# Este es un ejemplo de cómo se debe integrar el bloque de la Parte 3 correctamente
if aplicar_depuracion and depuracion_file is not None and st.button("Ejecutar depuración"):
    try:
        # Leemos el archivo Excel cargado por el usuario
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
                        indices_str = fila_encontrada['Indices'].iloc[0]
                        posiciones_str = fila_encontrada['Posiciones'].iloc[0]
                        indices = [int(i) for i in indices_str.split(';')]
                        posiciones = [int(p) for p in posiciones_str.split(';')]
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

    except Exception as e:
        st.error(f"Error general durante la depuración: {str(e)}")
