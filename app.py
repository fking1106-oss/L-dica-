import streamlit as st
import pandas as pd

# Configuración de la página
st.set_page_config(
    page_title="Visualizador de Google Sheets",
    page_icon="📊",
    layout="wide"
)

def load_data(sheet_id):
    """
    Función para cargar datos desde un Google Sheet público.
    """
    # Construir la URL de exportación a CSV
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    try:
        df = pd.read_csv(url)
        return df
    except Exception as e:
        st.error(f"Error al conectar con Google Sheets: {e}")
        return None

def main():
    st.title("📊 Panel de Visualización de Datos")
    st.markdown("""
    Esta aplicación extrae información en tiempo real desde un **Google Sheet**.
    """)

    # ID de tu documento proporcionado
    SHEET_ID = "1dCOy5iFQNx63fpARx-Ztx1ISy81Es0K4_2ZCyQ1lq0w"
    
    # Botón para refrescar datos
    if st.button('🔄 Actualizar Datos'):
        st.cache_data.clear()

    # Carga de datos
    with st.spinner('Cargando información desde la nube...'):
        df = load_data(SHEET_ID)

    if df is not None:
        # Métricas principales (Ejemplo: conteo de filas)
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Registros", len(df))
        
        # Buscador / Filtro
        search = st.text_input("🔍 Buscar en los datos:")
        if search:
            df_display = df[df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)]
        else:
            df_display = df

        # Mostrar tabla interactiva
        st.subheader("Vista Previa de la Información")
        st.dataframe(df_display, use_container_width=True)

        # Gráfico simple de ejemplo (ajustar según columnas del Excel)
        st.subheader("Análisis Rápido")
        if len(df.columns) >= 2:
            st.info("Puedes expandir el análisis seleccionando columnas específicas en el código.")
            # Ejemplo de visualización de barras si hay datos numéricos
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            if numeric_cols:
                selected_col = st.selectbox("Selecciona una columna numérica para graficar:", numeric_cols)
                st.bar_chart(df[selected_col])
        
        # Opción de descarga
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar datos como CSV",
            data=csv,
            file_name='datos_google_sheets.csv',
            mime='text/csv',
        )
    else:
        st.warning("No se pudieron cargar los datos. Verifica que el enlace del Google Sheet sea público.")

if __name__ == "__main__":
    main()
