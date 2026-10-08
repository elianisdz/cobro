from datetime import date
import sqlite3
import pandas as pd
import streamlit as st

PASSWORD_ADMIN = "1234"

def verificar_password_admin():
    if st.session_state.get("admin_autenticado", False):
        return True
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 2, 1])
    with col2:
        st.markdown("### 🔐 Acceso Administrador - Sistema de Crédito")
        with st.form("form_login_admin"):
            input_pass = st.text_input("Ingrese la contraseña de Administrador:", type="password")
            if st.form_submit_button("Entrar", type="primary"):
                if input_pass == PASSWORD_ADMIN:
                    st.session_state["admin_autenticado"] = True
                    st.rerun()
                else:
                    st.error("❌ Contraseña incorrecta.")
    return False

if not verificar_password_admin():
    st.stop()

st.set_page_config(page_title="Gestión de Créditos", page_icon="💵", layout="wide")

st.markdown("""
    <style>
    [data-testid="stDataFrame"] div[role="columnheader"], [data-testid="stDataFrame"] div[role="gridcell"] {
        text-align: center !important; justify-content: center !important;
    }
    div.stButton > button:first-child, div.stFormSubmitButton > button:first-child {
        background-color: #27ae60 !important; color: white !important; border-color: #27ae60 !important;
    }
    </style>
""", unsafe_allow_html=True)

def conectar_db():
    conn = sqlite3.connect("sistema_creditos.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS rutas (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre_ruta TEXT UNIQUE NOT NULL)")
    try:
        cursor.execute("ALTER TABLE rutas ADD COLUMN password_ruta TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass
    cursor.execute("""CREATE TABLE IF NOT EXISTS creditos (
        id INTEGER PRIMARY KEY AUTOINCREMENT, fecha_prestamo TEXT NOT NULL, nombre_cliente TEXT NOT NULL, 
        cobrador TEXT NOT NULL, capital_prestado INTEGER NOT NULL, interes_porcentaje REAL NOT NULL, 
        total_a_pagar INTEGER NOT NULL, dias_plazo INTEGER NOT NULL, cuota_diaria INTEGER NOT NULL, 
        saldo_pendiente INTEGER NOT NULL, estado TEXT NOT NULL)""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS historial_pagos (
        id INTEGER PRIMARY KEY AUTOINCREMENT, credito_id INTEGER NOT NULL, nombre_cliente TEXT NOT NULL, 
        cobrador TEXT NOT NULL, monto_pagado INTEGER NOT NULL, fecha_pago TEXT NOT NULL)""")
    conn.commit()
    return conn

conn = conectar_db()
st.markdown("💵 <h3>Control de Préstamos - <span style='color: #27ae60;'>Sistema de Crédito</span></h3>", unsafe_allow_html=True)

cursor_r = conn.cursor()
cursor_r.execute("SELECT nombre_ruta, password_ruta FROM rutas ORDER BY nombre_ruta ASC")
rutas_info = cursor_r.fetchall()
rutas_disponibles = [r[0] for r in rutas_info]
dic_passwords_rutas = {r[0]: (r[1] if r[1] is not None else "") for r in rutas_info}

st.sidebar.header("🗺️ Gestión de Rutas y Claves")
with st.sidebar.form("form_crear_ruta", clear_on_submit=True):
    nueva_ruta = st.text_input("Nombre de la Ruta")
    password_ruta = st.text_input("Clave Personal", type="password", max_chars=20)
    if st.form_submit_button("➕ Crear Ruta Protegida"):
        if nueva_ruta.strip() and password_ruta.strip():
            try:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO rutas (nombre_ruta, password_ruta) VALUES (?, ?)", (nueva_ruta.strip(), password_ruta.strip()))
                conn.commit()
                st.sidebar.success("✅ Ruta creada.")
                st.rerun()
            except sqlite3.IntegrityError:
                st.sidebar.warning("⚠️ La ruta ya existe.")
        else:
            st.sidebar.error("⚠️ Complete los campos.")

st.sidebar.markdown("---")
st.sidebar.header("📝 Registrar Nuevo Crédito")
if rutas_disponibles:
    with st.sidebar.form("form_registrar_credito", clear_on_submit=True):
        fecha_credito = st.date_input("Fecha del Préstamo", value=date.today())
        nombre_cliente = st.text_input("Nombre y Apellido del Cliente")
        cobrador_seleccionado = st.selectbox("Asignar a Ruta", rutas_disponibles)
        capital_prestado = st.number_input("Capital Prestado ($)", min_value=0, value=100000, step=10000, format="%d")
        st.caption(f"💡 Monto a Prestar: **${capital_prestado:,.0f}**".replace(",", "."))
        interes_porcentaje = st.number_input("Interés (%)", min_value=0.0, value=20.0, step=5.0)
        dias_plazo = st.number_input("Plazo en Cuotas (Días)", min_value=1, value=24, step=1)
        
        if st.form_submit_button("💾 Guardar Préstamo", type="primary"):
            if nombre_cliente.strip():
                total_calculado = int(capital_prestado + (capital_prestado * (interes_porcentaje / 100)))
                cuota_diaria_calculada = int(total_calculado / dias_plazo) if dias_plazo > 0 else 0
                cursor = conn.cursor()
                cursor.execute("""INSERT INTO creditos (fecha_prestamo, nombre_cliente, cobrador, capital_prestado, interes_porcentaje, total_a_pagar, dias_plazo, cuota_diaria, saldo_pendiente, estado)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (fecha_credito.strftime("%Y-%m-%d"), nombre_cliente.strip(), cobrador_seleccionado, int(capital_prestado), float(interes_porcentaje), int(total_calculado), int(dias_plazo), int(cuota_diaria_calculada), int(total_calculado), "Activo"))
                conn.commit()
                st.sidebar.success("✅ Préstamo registrado.")
                st.rerun()
            else:
                st.sidebar.error("⚠️ Ingrese el cliente.")

st.sidebar.markdown("---")
st.sidebar.header("🗑️ Eliminar Ruta")
if rutas_disponibles:
    with st.sidebar.form("form_eliminar_ruta", clear_on_submit=True):
        ruta_a_eliminar = st.selectbox("Seleccionar Ruta", rutas_disponibles)
        pass_retiro = st.text_input("Clave de la Ruta", type="password")
        if st.form_submit_button("🗑️ Eliminar Ruta"):
            if pass_retiro == dic_passwords_rutas.get(ruta_a_eliminar, ""):
                cursor = conn.cursor()
                cursor.execute("DELETE FROM rutas WHERE nombre_ruta = ?", (ruta_a_eliminar,))
                conn.commit()
                st.sidebar.success("✅ Ruta eliminada.")
                st.rerun()
            else:
                st.sidebar.error("❌ Contraseña incorrecta.")

st.header("📊 Cartera de Cobros por Ruta")
if not rutas_disponibles:
    st.info("ℹ️ Crea una ruta en la barra lateral para comenzar.")
else:
    tabs = st.tabs([f"📍 {r}" for r in rutas_disponibles])
    for idx, ruta in enumerate(rutas_disponibles):
        with tabs[idx]:
            st.subheader(f"Control de Cobros - {ruta}")
            clave_esperada = dic_passwords_rutas.get(ruta, "")
            session_key = f"ruta_desbloqueada_{ruta}"

            if clave_esperada and not st.session_state.get(session_key, False):
                st.warning(f"🔒 Ruta protegida. Ingrese contraseña de '{ruta}':")
                col_c1, col_c2 = st.columns([2, 1])
                with col_c1:
                    pass_ingresada = st.text_input(f"Contraseña {ruta}:", type="password", key=f"p_{ruta}")
                with col_c2:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("Desbloquear", key=f"u_{ruta}"):
                        if pass_ingresada == clave_esperada:
                            st.session_state[session_key] = True
                            st.rerun()
                        else:
                            st.error("❌ Contraseña incorrecta.")
            else:
                if clave_esperada and st.button(f"🔒 Bloquear {ruta}", key=f"l_{ruta}"):
                    st.session_state[session_key] = False
                    st.rerun()

                st.markdown("---")
                tab_activos, tab_inactivos, tab_historial = st.tabs(["📋 Activos", "📁 Inactivos", "📅 Historial"])

                with tab_activos:
                    df = pd.read_sql_query("SELECT * FROM creditos WHERE cobrador = ? AND estado = 'Activo' ORDER BY id DESC", conn, params=(ruta,))
                    if not df.empty:
                        m1, m2, m3, m4 = st.columns(4)
                        m1.metric("💵 Capital", f"${df['capital_prestado'].sum():,.0f}".replace(",", "."))
                        m2.metric("📋 Recaudar", f"${df['total_a_pagar'].sum():,.0f}".replace(",", "."))
                        m3.metric("⚠️ Pendiente", f"${df['saldo_pendiente'].sum():,.0f}".replace(",", "."))
                        m4.metric("🎯 Diario", f"${df['cuota_diaria'].sum():,.0f}".replace(",", "."))

                        st.markdown("---")
                        df_mostrar = df.copy()
                        df_mostrar.insert(0, "Abonar_Cuota", False)
                        df_mostrar.insert(1, "Monto_Ingresado", df_mostrar["cuota_diaria"])

                        counter_key = f"counter_{ruta}"
                        if counter_key not in st.session_state:
                            st.session_state[counter_key] = 0

                        df_editado = st.data_editor(
                            df_mostrar[["Abonar_Cuota", "Monto_Ingresado", "fecha_prestamo", "nombre_cliente", "cuota_diaria", "estado", "id"]],
                            column_config={
                                "Abonar_Cuota": st.column_config.CheckboxColumn("Pago Hoy", default=False),
                                "Monto_Ingresado": st.column_config.NumberColumn("Monto a Abonar ($)", min_value=0, step=1000, format="$%d"),
                                "id": None,
                            },
                            disabled=["fecha_prestamo", "nombre_cliente", "cuota_diaria", "estado"],
                            hide_index=True, use_container_width=True, key=f"editor_{ruta}_{st.session_state[counter_key]}"
                        )

                        if not df_editado[df_editado["Abonar_Cuota"] == True].empty:
                            if st.button(f"💰 Registrar Abonos - {ruta}", key=f"btn_abono_{ruta}", type="primary"):
                                cursor = conn.cursor()
                                fecha_hoy = date.today().strftime("%Y-%m-%d")
                                for _, row in df_editado[df_editado["Abonar_Cuota"] == True].iterrows():
                                    credito_id, nombre_cli, monto_real = row["id"], row["nombre_cliente"], int(row["Monto_Ingresado"])
                                    if monto_real > 0:
                                        cursor.execute("SELECT saldo_pendiente FROM creditos WHERE id = ?", (credito_id,))
                                        res = cursor.fetchone()
                                        if res:
                                            nuevo_saldo = max(0, res[0] - monto_real)
                                            nuevo_estado = "Inactivo" if nuevo_saldo == 0 else "Activo"
                                            cursor.execute("UPDATE creditos SET saldo_pendiente = ?, estado = ? WHERE id = ?", (nuevo_saldo, nuevo_estado, credito_id))
                                            cursor.execute("INSERT INTO historial_pagos (credito_id, nombre_cliente, cobrador, monto_pagado, fecha_pago) VALUES (?, ?, ?, ?, ?)", (credito_id, nombre_cli, ruta, monto_real, fecha_hoy))
                                conn.commit()
                                st.session_state[counter_key] += 1
                                st.success("✅ ¡Abonos registrados con éxito!")
                                st.rerun()
                    else:
                        st.info("ℹ️ No hay créditos activos.")

                with tab_inactivos:
                    df_inactivos = pd.read_sql_query("SELECT id, fecha_prestamo, nombre_cliente, total_a_pagar FROM creditos WHERE cobrador = ? AND estado = 'Inactivo' ORDER BY id DESC", conn, params=(ruta,))
                    if not df_inactivos.empty:
                        for _, row in df_inactivos.iterrows():
                            col_info, col_btn = st.columns([4, 1])
                            col_info.write(f"👤 **{row['nombre_cliente'].upper()}** | Fecha: {row['fecha_prestamo']} | Total: ${row['total_a_pagar']:,.0f}".replace(",", "."))
                            if col_btn.button("🗑️ Eliminar", key=f"del_{row['id']}"):
                                cursor = conn.cursor()
                                cursor.execute("DELETE FROM creditos WHERE id = ?", (row['id'],))
                                cursor.execute("DELETE FROM historial_pagos WHERE credito_id = ?", (row['id'],))
                                conn.commit()
                                st.rerun()
                    else:
                        st.info("ℹ️ No hay créditos inactivos.")

                with tab_historial:
                    df_hist = pd.read_sql_query("SELECT fecha_pago, nombre_cliente, monto_pagado FROM historial_pagos WHERE cobrador = ? ORDER BY nombre_cliente ASC, id DESC", conn, params=(ruta,))
                    if not df_hist.empty:
                        for cliente in df_hist["nombre_cliente"].unique():
                            st.markdown(f"#### 👤 Cliente: `{cliente.upper()}`")
                            df_c = df_hist[df_hist["nombre_cliente"] == cliente].copy()
                            df_c["Monto Abonado ($)"] = df_c["monto_pagado"].apply(lambda x: f"${x:,.0f}".replace(",", "."))
                            st.dataframe(df_c[["fecha_pago", "Monto Abonado ($)"]].rename(columns={"fecha_pago": "Fecha del Pago"}), use_container_width=True, hide_index=True)
                    else:
                        st.info("ℹ️ Aún no hay pagos registrados.")