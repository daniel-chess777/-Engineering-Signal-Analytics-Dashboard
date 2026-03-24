import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import time

# ==========================================================
# PAGE CONFIGURATION
# ==========================================================
st.set_page_config(
    page_title="Engineering Signal Analytics Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================================
# SESSION STATE INITIALIZATION
# ==========================================================
if "df" not in st.session_state:
    st.session_state.df = None

if "using_demo_data" not in st.session_state:
    st.session_state.using_demo_data = True

# ==========================================================
# STYLING
# ==========================================================
st.markdown("""
<style>
body { background-color: #0e1117; color: white; font-family: Arial, sans-serif; }
.stButton>button {
    background-color: #0078d7;
    color: white;
    border-radius: 8px;
    height: 40px;
    font-weight: bold;
}
.kpi-card {
    background: rgba(255,255,255,0.05);
    backdrop-filter: blur(10px);
    border-radius: 15px;
    padding: 15px;
    text-align: center;
    margin-bottom: 15px;
}
</style>
""", unsafe_allow_html=True)

# ==========================================================
# HEADER
# ==========================================================
st.title("⚡ Engineering Signal Analytics Dashboard")
st.markdown(
    "Electrical & systems engineering–focused analysis of voltage and frequency signals."
)
st.markdown("---")

# ==========================================================
# SIDEBAR
# ==========================================================
st.sidebar.header("Dashboard Controls")

mode = st.sidebar.radio(
    "Operating Mode",
    ["Single Signal", "Multiple Signals", "Upload Your Own Data"]
)

live_update = st.sidebar.checkbox("Enable Live Update (Simulation)", value=False)

threshold = st.sidebar.slider(
    "Anomaly Sensitivity (σ)",
    1.0, 3.0, 2.0, 0.1
)

# ==========================================================
# DATA LOADING
# ==========================================================
@st.cache_data
def load_demo_data():
    return pd.read_csv("data/demo_signal_data.csv")

if mode == "Upload Your Own Data":
    uploaded_file = st.sidebar.file_uploader(
        "Upload CSV (time, voltage, frequency)",
        type=["csv"]
    )

    if uploaded_file:
        df = pd.read_csv(uploaded_file)

        required_cols = {"time", "voltage", "frequency"}
        if not required_cols.issubset(df.columns):
            st.error("❌ CSV must contain columns: time, voltage, frequency")
            st.stop()

        st.session_state.df = df
        st.session_state.using_demo_data = False
        st.sidebar.success("✅ Custom data loaded")

        st.subheader("📄 Uploaded Data Preview")
        st.dataframe(df.head())
    else:
        st.warning("Upload a CSV to continue.")
        st.stop()
else:
    if st.session_state.df is None:
        st.session_state.df = load_demo_data()
        st.session_state.using_demo_data = True

df = st.session_state.df

# ==========================================================
# CONTEXT MESSAGE (FIXED)
# ==========================================================
if st.session_state.using_demo_data:
    st.info(
        "ℹ️ You are viewing **simulated demo signal data**. "
        "Upload your own CSV from the sidebar for real‑world analysis."
    )
else:
    st.success(
        "✅ You are now viewing **your uploaded real‑world dataset**. "
        "All metrics and visualizations reflect your data."
    )

# ==========================================================
# DATASET METADATA
# ==========================================================
with st.expander("📋 Dataset Overview"):
    st.write(f"**Samples:** {len(df):,}")
    st.write(f"**Signals:** {list(df.columns)}")
    st.write(f"**Time Range:** {df['time'].iloc[0]} → {df['time'].iloc[-1]}")

# ==========================================================
# ENGINEERING THEORY
# ==========================================================
with st.expander("📘 Engineering & Mathematical Background"):
    st.markdown(r"""
    ### 1️⃣ Time‑Domain Signal Analysis
    This dashboard analyzes electrical signals in the **time domain**, a common approach
    in power systems, control systems, and instrumentation monitoring.

    ### 2️⃣ Statistical Descriptors
    **Mean (Average):**
    $$
    \mu = \frac{1}{N} \sum_{i=1}^{N} x_i
    $$

    **Standard Deviation (Noise / Variability):**
    $$
    \sigma = \sqrt{\frac{1}{N} \sum_{i=1}^{N} (x_i - \mu)^2}
    $$

    These values describe steady‑state behavior and random noise in sensor readings.

    ### 3️⃣ Anomaly Detection (Fault Indication)
    A data point is flagged as anomalous if:
    $$
    x > \mu + k\sigma \quad \text{or} \quad x < \mu - k\sigma
    $$
    where:
    - \( k \) is the user‑selected sensitivity
    - Typical engineering values: **2σ – 3σ**

    This method is widely used for **fault detection, quality control, and system monitoring**.
    """)


# ==========================================================
# TIME WINDOW
# ==========================================================
window = st.slider(
    "Analysis Window (Most Recent Samples)",
    50, len(df), len(df)
)

df_view = df.tail(window)

# ==========================================================
# SIGNAL SELECTION
# ==========================================================
if mode == "Single Signal":
    signals = [st.sidebar.selectbox("Select Signal", ["voltage", "frequency"])]
elif mode == "Multiple Signals":
    signals = st.sidebar.multiselect(
        "Select Signals", ["voltage", "frequency"], default=["voltage", "frequency"]
    )
else:
    signals = df_view.select_dtypes(include=np.number).columns.tolist()
    signals.remove("time")

# ==========================================================
# KPI METRICS
# ==========================================================
st.subheader("📊 Signal Metrics & Fault Indicators")

cols = st.columns(len(signals))

for i, sig in enumerate(signals):
    mean = df_view[sig].mean()
    std = df_view[sig].std()
    upper = mean + threshold * std
    lower = mean - threshold * std
    anomaly_count = ((df_view[sig] > upper) | (df_view[sig] < lower)).sum()

    with cols[i]:
        st.markdown(
            f"<div class='kpi-card'><h4>{sig.capitalize()} Mean (μ)</h4>"
            f"<h2>{mean:.2f}</h2></div>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<div class='kpi-card'><h4>Anomalies</h4>"
            f"<h2>{anomaly_count}</h2></div>",
            unsafe_allow_html=True
        )

# ==========================================================
# PLOT
# ==========================================================
st.subheader("📈 Time‑Domain Signal Visualization")

fig = go.Figure()

for sig in signals:
    mean = df_view[sig].mean()
    std = df_view[sig].std()
    upper = mean + threshold * std
    lower = mean - threshold * std
    anomalies = df_view[(df_view[sig] > upper) | (df_view[sig] < lower)]

    fig.add_trace(go.Scatter(
        x=df_view["time"],
        y=df_view[sig],
        mode="lines",
        name=sig.capitalize()
    ))

    fig.add_trace(go.Scatter(
        x=anomalies["time"],
        y=anomalies[sig],
        mode="markers",
        name=f"{sig.capitalize()} Anomaly",
        marker=dict(color="red", size=8)
    ))

fig.update_layout(
    template="plotly_dark",
    hovermode="x unified",
    xaxis_title="Time",
    yaxis_title="Signal Magnitude",
    height=600
)

st.plotly_chart(fig, use_container_width=True)

# ==========================================================
# LIVE UPDATE SIMULATION (FIXED VARIABLE NAME)
# ==========================================================
if live_update:
    st.info(
        "🔴 Live simulation enabled — injecting noise to emulate "
        "real‑time sensor variation."
    )

    placeholder = st.empty()

    for _ in range(3):
        time.sleep(5)

        df_view["voltage"] += np.random.normal(0, 0.1, len(df_view))
        df_view["frequency"] += np.random.normal(0, 0.05, len(df_view))

        with placeholder.container():
            fig_live = go.Figure()
            for signal in signals:   # ✅ FIXED
                fig_live.add_trace(go.Scatter(
                    x=df_view["time"],
                    y=df_view[signal],
                    mode="lines",
                    name=signal.capitalize()
                ))

            fig_live.update_layout(
                template="plotly_dark",
                title="Live Signal Behavior Under Noise",
                height=600
            )

            st.plotly_chart(fig_live, use_container_width=True)