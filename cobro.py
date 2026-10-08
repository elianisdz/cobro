from datetime import date
import sqlite3
import pandas as pd
import streamlit as st

# -------------------------------------------------------------------
# CONFIGURACIÓN DE CONTRASEÑA GENERAL DEL SISTEMA (ADMINISTRADOR)
# -------------------------------------------------------------------
PASSWORD_ADMIN = "1234"  # Contraseña maestra del administrador

def verificar_password_admin():
    if st.session_state.get("admin_autenticado", False):
        return True

    st.markdown("<br><br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("### 🔐 Acceso Administrador - Sistema de Crédito")
        with st.form("form_login_admin"):
            input_pass = st.text_input("Ingrese la contraseña de Administrador:", type="password")
            btn_login = st.form_submit_button("Entrar", type="primary")

            if btn_login:
                if input_pass == PASSWORD_ADMIN:
                    st.session_state["admin_autenticado"] = True
                    st.rerun()
                else:
                    st.error("❌ Contraseña de administrador incorrecta.")

    return False

if not verificar_password_admin():
    st.stop()

# -------------------------------------------------------------------
# CONFIGURACIÓN DE LA PÁGINA WEB & ESTILOS VERDES
# -------------------------------------------------------------------
st.set_page_config(
    page_title="Gestión de Créditos - Sistema de Crédito",
    page_icon="💵",
    layout="wide",
)

st.markdown(
    """
    <style>
    [data-testid="stDataFrame"] div[role="columnheader"],
    [data-testid="stDataFrame"] div[role="gridcell"],
    [data-testid="stDataFrame"] div[role="columnheader"] *,
    [data-testid="stDataFrame"] div[role="gridcell"] * {
        text-align: center !important;
        justify-content: center !important;
        align-items: center !important;
    }
    div.stButton > button:first-child, div.stFormSubmitButton > button:first-child {
        background-color: #27ae60 !important;
        color: white !important;
        border-color: #27ae60 !important;
    }
    div.stButton > button:first-child:hover, div.stFormSubmitButton > button:first-child:hover {
        background-color: #219653 !important;
        border-color: #219653 !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# -------------------------------------------------------------------
# BASE DE DATOS
# -------------------------------------------------------------------
def conectar_db():
    conn = sqlite3.connect("sistema_creditos.db", check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rutas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_ruta TEXT UNIQUE NOT NULL
        )
    """)

    try:
        cursor.execute("ALTER TABLE rutas ADD COLUMN password_ruta TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS creditos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_prestamo TEXT NOT NULL,
            nombre_cliente TEXT NOT NULL,
            cobrador TEXT NOT NULL,
            capital_prestado INTEGER NOT NULL,
            interes_porcentaje REAL NOT NULL,
            total_a_pagar INTEGER NOT NULL,
            dias_plazo INTEGER NOT NULL,
            cuota_diaria INTEGER NOT NULL,
            saldo_pendiente INTEGER NOT NULL,
            estado TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historial_pagos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            credito_id INTEGER NOT NULL,
            nombre_cliente TEXT NOT NULL,
            cobrador TEXT NOT NULL,
            monto_pagado INTEGER NOT NULL,
            fecha_pago TEXT NOT NULL
        )
    """)

    conn.commit()
    return conn

conn = conectar_db()

st.markdown("💵 <h3>Control de Préstamos - <span style='color: #27ae60;'>Sistema de Crédito</span></h3>", unsafe_allow_html=True)

cursor_r = conn.cursor()
cursor_r.execute("SELECT nombre_ruta, password_ruta FROM rutas ORDER BY nombre_ruta ASC")
rutas_info = cursor_r.fetchall()
rutas_disponibles = [r[0] for r in rutas_info]
dic_passwords_rutas = {r[0]: (r[1] if r[1] is not None else "") for r in rutas_info}

# -------------------------------------------------------------------
# BARRA LATERAL
# -------------------------------------------------------------------
st.sidebar.header("🗺️ Gestión de Rutas y Claves")

with st.sidebar.form("form_crear_ruta", clear_on_submit=True):
    st.markdown("**Crear Nueva Ruta**")
    nueva_ruta = st.text_input("Nombre de la Ruta", key="input_nueva_ruta")
    password_ruta = st.text_input("Clave Personal", type="password", max_chars=20, key="input_pass_ruta")
    btn_crear_ruta = st.form_submit_button("➕ Crear Ruta Protegida")

if btn_crear_ruta:
    if not nueva_ruta.strip():
        st.sidebar.error("⚠️ Ingrese un nombre válido para la ruta.")
    elif not password_ruta.strip():
        st.sidebar.error("⚠️ Debe asignar una contraseña.")
    else:
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO rutas (nombre_ruta, password_ruta) VALUES (?, ?)", (nueva_ruta.strip(), password_ruta.strip()))
            conn.commit()
            st.sidebar.success(f"✅ Ruta '{nueva_ruta.strip()}' creada.")
            st.rerun()
        except sqlite3.IntegrityError:
            st.sidebar.warning("⚠️ Esta ruta ya existe.")

st.sidebar.markdown("---")
st.sidebar.header("📝 Registrar Nuevo Crédito")

if not rutas_disponibles:
    st.sidebar.warning("⚠️ Primero crea una ruta.")
else:
    with st.sidebar.form("form_registrar_credito", clear_on_submit=True):
        fecha_credito = st.date_input("Fecha del Préstamo", value=date.today())
        nombre_cliente = st.text_input("Nombre y Apellido del Cliente")
        cobrador_seleccionado = st.selectbox("Asignar a Ruta", rutas_disponibles)

        capital_prestado = st.number_input("Capital Prestado ($)", min_value=0, value=100000, step=10000, format="%d")
        st.caption(f"💡 Monto a Prestar: **${capital_prestado:,.0f}**".replace(",", "."))

        interes_porcentaje = st.number_input("Interés (%)", min_value=0.0, value=20.0, step=5.0)
        dias_plazo = st.number_input("Plazo en Cuotas (Días)", min_value=1, value=24, step=1)

        btn_guardar_prestamo = st.form_submit_button("💾 Guardar Préstamo", type="primary")

    if btn_guardar_prestamo:
        if not nombre_cliente.strip():
            st.sidebar.error("⚠️ Ingresa el nombre del cliente.")
        else:
            total_calculado = int(capital_prestado + (capital_prestado * (interes_porcentaje / 100)))
            cuota_diaria_calculada = int(total_calculado / dias_plazo) if dias_plazo > 0 else 0
            fecha_str = fecha_credito.strftime("%Y-%m-%d")

            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO creditos (fecha_prestamo, nombre_cliente, cobrador, capital_prestado, interes_porcentaje, total_a_pagar, dias_plazo, cuota_diaria, saldo_pendiente, estado)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (fecha_str, nombre_cliente.strip(), cobrador_seleccionado, int(capital_prestado), float(interes_porcentaje), int(total_calculado), int(dias_plazo), int(cuota_diaria_calculada), int(total_calculado), "Activo"))
            conn.commit()
            st.sidebar.success(f"✅ Préstamo registrado para {nombre_cliente}")
            st.rerun()

st.sidebar.markdown("---")
st.sidebar.header("🗑️ Eliminar Ruta")
if rutas_disponibles:
    with st.sidebar.form("form_eliminar_ruta", clear_on_submit=True):
        ruta_a_eliminar = st.selectbox("Seleccionar Ruta a Retirar", rutas_disponibles, key="sel_ruta_eliminar")
        pass_retiro = st.text_input("Clave de la Ruta para Confirmar", type="password", key="input_pass_retiro")
        btn_eliminar_ruta = st.form_submit_button("🗑️ Eliminar Ruta Definitivamente")

    if btn_eliminar_ruta:
        clave_real = dic_passwords_rutas.get(ruta_a_eliminar, "")
        if pass_retiro == clave_real:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM rutas WHERE nombre_ruta = ?", (ruta_a_eliminar,))
            conn.commit()
            st.sidebar.success(f"✅ Ruta '{ruta_a_eliminar}' eliminada.")
            st.rerun()
        else:
            st.sidebar.error("❌ Contraseña incorrecta.")

# -------------------------------------------------------------------
# PANEL PRINCIPAL
# -------------------------------------------------------------------
st.header("📊 Cartera de Cobros por Ruta")

if not rutas_disponibles:
    st.info("ℹ️ Crea una ruta con clave en la barra lateral para comenzar.")
else:
    tabs = st.tabs([f"📍 {r}" for r in rutas_disponibles])

    for idx, ruta in enumerate(rutas_disponibles):
        with tabs[idx]:
            st.subheader(f"Control de Cobros - {ruta}")
            clave_esperada = dic_passwords_rutas.get(ruta, "")
            session_key = f"ruta_desbloqueada_{ruta}"

            if clave_esperada and not st.session_state.get(session_key, False):
                st.warning(f"🔒 Ruta protegida. Ingresa la contraseña de '{ruta}':")
                col_c1, col_c2 = st.columns([2, 1])
                with col_c1:
                    pass_ingresada = st.text_input(f"Contraseña para {ruta}:", type="password", key=f"input_pass_{ruta}")
                with col_c2:
                    st.markdown("<br>", unsafe_allow_html=True)
                    btn_desbloquear = st.button("Desbloquear Ruta", key=f"btn_unlock_{ruta}")

                if btn_desbloquear:
                    if pass_ingresada == clave_esperada:
                        st.session_state[session_key] = True
                        st.rerun()
                    else:
                        st.error("❌ Contraseña incorrecta.")
            else:
                if clave_esperada:
                    if st.button(f"🔒 Bloquear / Cerrar Sesión de {ruta}", key=f"lock_{ruta}"):
                        st.session_state[session_key] = False
                        st.rerun()

                st.markdown("---")
                tab_activos, tab_inactivos, tab_historial = st.tabs([
                    "📋 Créditos Activos", 
                    "📁 Créditos Finalizados / Inactivos", 
                    "📅 Historial de Pagos Realizados"
                ])

                with tab_activos:
                    query = "SELECT * FROM creditos WHERE cobrador = ? AND estado = 'Activo' ORDER BY id DESC"
                    df = pd.read_sql_query(query, conn, params=(ruta,))

                    if not df.empty:
                        total_cartera = df["total_a_pagar"].sum()
                        total_pendiente = df["saldo_pendiente"].sum()
                        total_prestado_global = df["capital_prestado"].sum()
                        total_cuota_diaria_global = df["cuota_diaria"].sum()

                        m1, m2, m3, m4 = st.columns(4)
                        m1.metric("💵 Capital Prestado", f"${total_prestado_global:,.0f}".replace(",", "."))
                        m2.metric("📋 Total a Recaudar", f"${total_cartera:,.0f}".replace(",", "."))
                        m3.metric("⚠️ Saldo Pendiente