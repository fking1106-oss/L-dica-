import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import time

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Dashboard de Inventario Inteligente",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILOS CSS PARA ESTÉTICA PREMIUM ---
st.markdown("""
    <style>
    /* Fondo general */
    .stApp {
        background-color: #0e1117;
    }
    /* Contenedores de métricas */
    div[data-testid="stMetricValue"] {
        font-size: 2rem;
        color: #00d4ff;
    }
    /* Estilo para los títulos */
    h1, h2, h3 {
        color: #ffffff !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    /* Quitar padding innecesario */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 0rem;
    }
    /* Estilo para inputs de barra lateral */
    .stNumberInput input {
        background-color: #1e2130 !important;
        color: #00d4ff !important;
    }
    </style>
    """, unsafe_allow_html=True)

def load_data(sheet_id):
    """Carga datos desde Google Sheets sin cache para velocidad máxima."""
    ts = int(time.time())
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&cb={ts}"
    try:
        df = pd.read_csv(url)
        return df
    except Exception as e:
        st.error(f"Error al conectar con la fuente de datos: {e}")
        return None

def draw_gauge(current_val, reorder_val, title, max_val=100):
    """Genera un velocímetro estilizado con zonas de color basadas en stock de seguridad."""
    
    # Definir colores dinámicos basados en el estado
    if current_val <= reorder_val:
        bar_color = "#FF4B4B"  # Rojo
    elif current_val <= reorder_val * 1.3:
        bar_color = "#FFAA00"  # Naranja/Amarillo
    else:
        bar_color = "#00CC96"  # Verde

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=current_val,
        title={'text': f"<b>{title}</b>", 'font': {'size': 20, 'color': 'white'}},
        number={'font': {'color': 'white', 'size': 40}, 'suffix': ""},
        gauge={
            'axis': {'range': [0, max(max_val, current_val + 20)], 'tickwidth': 1, 'tickcolor': "white"},
            'bar': {'color': bar_color, 'thickness': 0.6},
            'bgcolor': "rgba(255, 255, 255, 0.1)",
            'borderwidth': 0,
            'steps': [
                {'range': [0, reorder_val], 'color': 'rgba(255, 75, 75, 0.3)'}
            ],
            'threshold': {
                'line': {'color': "white", 'width': 4},
                'thickness': 0.8,
                'value': reorder_val
            }
        }
    ))

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=30, r=30, t=50, b=20),
        height=280
    )
    return fig

def main():
    # --- BARRA LATERAL ---
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/2897/2897832.png", width=80)
        st.title("Configuración")
        
        # Módulo de cálculo manual (no interfiere con la gráfica principal)
        st.subheader("📊 Cálculo de Seguridad")
        with st.expander("Demanda y Logística", expanded=True):
            dem_c1 = st.number_input("Cliente A (uds/día)", value=10)
            dem_c2 = st.number_input("Cliente B (uds/día)", value=10)
            dem_c3 = st.number_input("Cliente C (uds/día)", value=10)
            l_time = st.number_input("Tiempo Reposición (días)", value=5)
            
            # El reorder_point se calcula internamente
            reorder_point = (dem_c1 + dem_c2 + dem_c3) * l_time
            st.info(f"Punto de Seguridad: {reorder_point} uds")

        refresh_rate = st.select_slider(
            "Velocidad de actualización",
            options=[2, 5, 10, 30, 60],
            value=5
        )
        
        st.divider()
        st.caption("Los datos se sincronizan con la última fila del historial.")

    # --- LÓGICA DE DATOS ---
    SHEET_ID = "1dCOy5iFQNx63fpARx-Ztx1ISy81Es0K4_2ZCyQ1lq0w"
    df_raw = load_data(SHEET_ID)

    if df_raw is not None and not df_raw.empty:
        # Extraer el ÚLTIMO dato
        latest_data = df_raw.iloc[-1]
        numeric_cols = df_raw.select_dtypes(include=['number']).columns.tolist()

        # --- ENCABEZADO ---
        col_t1, col_t2 = st.columns([3, 1])
        with col_t1:
            st.title("🚀 Monitor de Inventario en Tiempo Real")
        with col_t2:
            st.markdown(f"<p style='text-align:right; color:#888; padding-top:20px;'>Actualizado: {datetime.now().strftime('%H:%M:%S')}</p>", unsafe_allow_html=True)

        st.divider()

        # --- VISUALIZACIÓN DE VELOCÍMETROS ---
        if len(numeric_cols) > 0:
            cols_gauges = st.columns(min(len(numeric_cols), 4))
            for i, col_name in enumerate(numeric_cols[:4]):
                current_value = latest_data[col_name]
                # Dinamismo en el máximo del gauge
                max_g = max(200, reorder_point * 1.5, current_value + 10)
                with cols_gauges[i]:
                    st.plotly_chart(draw_gauge(current_value, reorder_point, col_name, max_g), use_container_width=True)

        # --- SECCIÓN INFERIOR: ESTADO Y TENDENCIA ---
        st.divider()
        col_list, col_graph = st.columns([1, 2])

        with col_list:
            st.subheader("📋 Estado Actual")
            for col_name in numeric_cols[:5]:
                val = latest_data[col_name]
                # El estado depende del cálculo manual de la barra lateral
                is_critical = val <= reorder_point
                status = "🔴 Crítico" if is_critical else "🟢 Normal"
                st.metric(label=col_name, value=val, delta=status, delta_color="normal" if not is_critical else "inverse")

        with col_graph:
            st.subheader("📈 Tendencia Reciente")
            st.line_chart(df_raw[numeric_cols].tail(20))

        # --- TABLA DE DATOS ---
        with st.expander("Ver historial completo"):
            st.dataframe(df_raw.sort_index(ascending=False), use_container_width=True)

    else:
        st.warning("Esperando conexión con Google Sheets...")

    # --- REFRESH ---
    time.sleep(refresh_rate)
    st.rerun()

if __name__ == "__main__":
    main()
