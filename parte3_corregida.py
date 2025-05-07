
# -------------------- PARTE 3: DEPURACIÓN OPCIONAL ------------------------------
# Parte 3: Depuración opcional del usuario
st.markdown("### 🧪 Parte 3: Depuración opcional del usuario (4 campos de `df_final`)")
activar_depuracion = st.checkbox("🔍 Realizar depuración manual de autores/keywords/referencias")

if activar_depuracion:
    depuracion_file = st.file_uploader("📥 Sube el archivo Excel con las tablas de conversión", type=["xlsx", "xls"])

    if depuracion_file is not None and st.button("✅ Aplicar depuración"):
        try:
            # Guardar el archivo subido temporalmente
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

            # (El resto de bloques de depuración continuarían aquí...)

        except Exception as e:
            st.error(f"Error general durante la depuración: {str(e)}")
