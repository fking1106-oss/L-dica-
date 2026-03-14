import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import time

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Gestión de Inventario - Manual & Realtime",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILOS CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { font-size: 2rem; color: #00d4ff; }
    h1, h2, h3 { color: #ffffff !important; font-family: 'Segoe UI', sans-serif; }
    .block-container { padding-top: 1.5rem; padding-bottom: 0rem; }
    /* Estilo para los inputs de número */
    input { background-color: #1e2130 !important; color: #00d4ff !important; border: 1px solid #3d4466 !important; }
    </style>
    """, unsafe_allow_html=True)

def load_data(sheet_id):
    """Carga datos en tiempo real (solo para el stock actual)."""
    ts = int(time.time())
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&cb={ts}"
    try:
        df = pd.read_csv(url)
        return df
    except Exception as e:
        return None

def draw_gauge(current_val, safety_stock, title, max_val=100):
    """Genera un velocímetro basado en el Stock de Seguridad manual."""
    # Lógica de color basada en el cálculo manual
    if current_val <= safety_stock:
        bar_color = "#FF4B4B" # Crítico
    elif current_val <= safety_stock * 1.5:
        bar_color = "#FFAA00" # Advertencia
    else:
        bar_color = "#00CC96" # Óptimo

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=current_val,
        title={'text': f"<b>{title}</b>", 'font': {'size': 18, 'color': 'white'}},
        number={'font': {'color': 'white', 'size': 35}},
        gauge={
            'axis': {'range': [0, max(max_val, current_val + 10)], 'tickcolor': "white"},
            'bar': {'color': bar_color, 'thickness': 0.6},
            'bgcolor': "rgba(255, 255, 255, 0.1)",
            'steps': [
                {'range': [0, safety_stock], 'color': 'rgba(255, 75, 75, 0.3)'}
            ],
            'threshold': {
                'line': {'color': "white", 'width': 4},
                'value': safety_stock
            }
        }
    ))
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=20, r=20, t=50, b=10), height=250)
    return fig

def main():
    # --- BARRA LATERAL: ENTRADA MANUAL DE DATOS ---
    with st.sidebar:
        st.title("🎛️ Parámetros Manuales")
        st.markdown("Ingresa los datos para calcular el **Stock de Seguridad**.")
        
        with st.container():
            st.subheader("👥 Demanda por Cliente")
            c1 = st.number_input("Cliente A (uds/día)", min_value=0, value=12)
            c2 = st.number_input("Cliente B (uds/día)", min_value=0, value=8)
            c3 = st.number_input("Cliente C (uds/día)", min_value=0, value=10)
            
            st.subheader("⏳ Logística")
            lt = st.number_input("Tiempo de Reposición (días)", min_value=1, value=5)
            
            # CÁLCULO MANUAL (Independiente del histórico)
            demanda_total = c1 + c2 + c3
            ss_manual = demanda_total * lt
            
            st.success(f"**Stock de Seguridad: {ss_manual} uds**")
        
        st.divider()
        refresh_rate = st.select_slider("Frecuencia de refresco (seg)", options=[2, 5, 10, 30], value=5)
        st.caption("Los medidores se ajustan automáticamente a estos valores.")

    # --- LÓGICA DE VISUALIZACIÓN ---
    SHEET_ID = "1dCOy5iFQNx63fpARx-Ztx1ISy81Es0K4_2ZCyQ1lq0w"
    df = load_data(SHEET_ID)

    if df is not None and not df.empty:
        # Solo tomamos la última fila para el stock "actual"
        latest = df.iloc[-1]
        num_cols = df.select_dtypes(include=['number']).columns.tolist()

        # Encabezado
        t1, t2 = st.columns([3, 1])
        t1.title("📊 Monitor de Inventario Crítico")
        t2.markdown(f"<p style='text-align:right; color:#777; padding-top:25px;'>Sincronizado: {datetime.now().strftime('%H:%M:%S')}</p>", unsafe_allow_html=True)

        # Velocímetros basados en ss_manual
        if num_cols:
            cols = st.columns(min(len(num_cols), 4))
            for i, col_name in enumerate(num_cols[:4]):
                with cols[i]:
                    val_actual = latest[col_name]
                    st.plotly_chart(draw_gauge(val_actual, ss_manual, col_name, 200), use_container_width=True)

        st.divider()
        
        # Resumen de Métricas
        m1, m2, m3 = st.columns(3)
        m1.metric("Demanda Diaria (Manual)", f"{demanda_total} uds")
        m2.metric("Tiempo Espera", f"{lt} días")
        m3.metric("Límite de Reorden", f"{ss_manual} uds")

        # Gráfico de tendencia (solo visual)
        st.subheader("📈 Histórico de Movimientos")
        st.line_chart(df[num_cols].tail(30))

    else:
        st.info("Cargando niveles actuales de stock...")

    # Refresco automático
    time.sleep(refresh_rate)
    st.rerun()

if __name__ == "__main__":
    main()
