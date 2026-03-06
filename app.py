import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time

# Configuración de la página con estilo moderno
st.set_page_config(
    page_title="Gestión de Inventario Pro",
    page_icon="📦",
    layout="wide"
)

# Estilo personalizado con CSS
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

def load_data(sheet_id):
    """Carga datos desde Google Sheets."""
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    try:
        df = pd.read_csv(url)
        return df
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None

def create_gauge(current_value, reorder_point, title):
    """Crea un gráfico de velocímetro (Gauge) estético."""
    # Determinamos el color basado en el punto de reorden
    color = "red" if current_value <= reorder_point else "orange" if current_value <= reorder_point * 1.5 else "green"
    
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = current_value,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': title, 'font': {'size': 18}},
        gauge = {
            'axis': {'range': [None, max(current_value * 2, reorder_point * 2)]},
            'bar': {'color': color},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, reorder_point], 'color': 'rgba(255, 0, 0, 0.2)'},
                {'range': [reorder_point, reorder_point * 1.5], 'color': 'rgba(255, 255, 0, 0.2)'}
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': reorder_point
            }
        }
    ))
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=20))
    return fig

def main():
    # --- BARRA LATERAL (Configuración) ---
    st.sidebar.header("⚙️ Configuración")
    
    # Punto de reorden global (puede ser por producto, aquí lo hacemos ajustable)
    reorder_level = st.sidebar.slider("Punto de Reorden Sugerido", 0, 100, 20)
    
    # Intervalo de actualización automática
    auto_refresh_interval = st.sidebar.selectbox(
        "Intervalo de actualización automática",
        options=[30, 60, 300, 600],
        format_func=lambda x: f"{x} segundos" if x < 60 else f"{x//60} minutos"
    )

    # --- LÓGICA DE CARGA ---
    SHEET_ID = "1dCOy5iFQNx63fpARx-Ztx1ISy81Es0K4_2ZCyQ1lq0w"
    
    # Título y Header
    st.title("📦 Panel de Control de Inventario")
    last_update = st.empty()
    last_update.caption(f"Última actualización: {time.strftime('%H:%M:%S')}")

    # Cargar datos
    df = load_data(SHEET_ID)

    if df is not None:
        # --- MÉTRICAS Y VELOCÍMETROS ---
        st.subheader("Visualización de Niveles de Stock")
        
        # Simulamos que la primera columna es el nombre y la segunda la cantidad
        # Ajusta esto según el nombre real de tus columnas en el Google Sheet
        cols = st.columns(min(len(df), 3))
        
        for i, row in df.iterrows():
            if i < 3: # Limitamos a los primeros 3 para el ejemplo visual
                product_name = str(row.iloc[0])
                current_stock = float(row.iloc[1]) if isinstance(row.iloc[1], (int, float)) else 0
                
                with cols[i]:
                    st.plotly_chart(create_gauge(current_stock, reorder_level, product_name), use_container_width=True)
        
        # --- TABLA DETALLADA ---
        st.subheader("📋 Detalle General de Inventario")
        
        # Aplicamos formato condicional a la tabla
        def highlight_stock(s):
            return ['background-color: #ffcccc' if (isinstance(val, (int, float)) and val <= reorder_level) else '' for val in s]

        st.dataframe(df.style.apply(highlight_stock, axis=1), use_container_width=True)

        # --- AUTO-REFRESH ---
        # JavaScript para recargar la página automáticamente según el tiempo seleccionado
        time.sleep(auto_refresh_interval)
        st.rerun()

    else:
        st.error("No se pudieron cargar los datos. Verifica el enlace de Google Sheets.")

if __name__ == "__main__":
    main()
