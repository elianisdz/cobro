from datetime import date, datetime
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
      input_pass = st.text_input(
          "Ingrese la contraseña de Administrador:", type="password"
      )
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
    /* Centrado de datos en tablas */
    [data-testid="stDataFrame"] div[role="columnheader"],
    [data-testid="stDataFrame"] div[role="gridcell"],
    [data-testid="stDataFrame"] div[role="columnheader"] *,
    [data-testid="stDataFrame"] div[role="gridcell"] * {
        text-align: center !important;
        justify-content: center !important;
        align-items: center !important;
    }
    
    /* Botones principales en tono verde financiero */
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
# BASE DE DATOS (RUTAS, CRÉDITOS E HISTORIAL DE PAGOS)
# -------------------------------------------------------------------


def conectar_db():
  conn = sqlite3.connect("sistema_creditos.db")
  cursor = conn.cursor()

  # Tabla de Rutas
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

  # Tabla de Créditos
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

  # Tabla para el Historial de Pagos (Fechas y montos abonados)
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

st.markdown(
    "💵 ## Control de Préstamos - <span"
    ' style="color: #27ae60;">Sistema de Crédito</span>',
    unsafe_allow_html=True,
)

# -------------------------------------------------------------------
# BARRA LATERAL: GESTIÓN DE RUTAS Y NUEVOS PRÉSTAMOS
# -------------------------------------------------------------------
st.sidebar.header("🗺️ Gestión de Rutas y Claves")

# Crear Ruta
with st.sidebar.form("form_crear_ruta", clear_on_submit=True):
  st.markdown("**Crear Nueva Ruta**")
  nueva_ruta = st.text_input("Nombre de la Ruta", key="input_nueva_ruta")
  password_ruta = st.text_input(
      "Clave Personal", type="password", max_chars=20, key="input_pass_ruta"
  )
  btn_crear_ruta = st.form_submit_button("➕ Crear Ruta Protegida")

if btn_crear_ruta:
  if not nueva_ruta.strip():
    st.sidebar.error("⚠️ Ingrese un nombre válido para la ruta.")
  elif not password_ruta.strip():
    st.sidebar.error("⚠️ Debe asignar una contraseña para proteger esta ruta.")
  else:
    try:
      cursor = conn.cursor()
      cursor.execute(
          "INSERT INTO rutas (nombre_ruta, password_ruta) VALUES (?, ?)",
          (nueva_ruta.strip(), password_ruta.strip()),
      )
      conn.commit()
      st.sidebar.success(
          f"✅ Ruta '{nueva_ruta.strip()}' creada y protegida con éxito."
      )
      st.rerun()
    except sqlite3.IntegrityError:
      st.sidebar.warning(
          "⚠️ Esta ruta ya se encuentra registrada en el sistema."
      )

st.sidebar.markdown("---")

# Obtener rutas registradas
cursor_r = conn.cursor()
cursor_r.execute(
    "SELECT nombre_ruta, password_ruta FROM rutas ORDER BY nombre_ruta ASC"
)
rutas_info = cursor_r.fetchall()
rutas_disponibles = [r[0] for r in rutas_info]
dic_passwords_rutas = {r[0]: (r[1] if r[1] is not None else "") for r in rutas_info}

# Eliminar Ruta por retiro de personal
if rutas_disponibles:
  with st.sidebar.form("form_eliminar_ruta", clear_on_submit=True):
    st.markdown("**Eliminar Ruta (Retiro de Personal)**")
    ruta_a_eliminar = st.selectbox(
        "Seleccionar Ruta a Retirar", rutas_disponibles, key="sel_ruta_eliminar"
    )
    pass_retiro = st.text_input(
        "Clave de la Ruta para Confirmar", type="password", key="input_pass_retiro"
    )
    btn_eliminar_ruta = st.form_submit_button("🗑️ Eliminar Ruta")

  if btn_eliminar_ruta:
    clave_real = dic_passwords_rutas.get(ruta_a_eliminar, "")
    if pass_retiro == clave_real:
      cursor = conn.cursor()
      cursor.execute("DELETE FROM rutas WHERE nombre_ruta = ?", (ruta_a_eliminar,))
      conn.commit()
      st.sidebar.success(
          f"✅ La ruta '{ruta_a_eliminar}' ha sido eliminada del sistema."
      )
      st.rerun()
    else:
      st.sidebar.error(
          "❌ Contraseña incorrecta. No se puede eliminar la ruta sin su"
          " clave."
      )

  st.sidebar.markdown("---")

st.sidebar.header("📝 Registrar Nuevo Crédito")

if not rutas_disponibles:
  st.sidebar.warning(
      "⚠️ Primero debes registrar al menos una ruta con su contraseña en la"
      " sección superior."
  )
else:
  # Campos interactivos con puntos visibles en tiempo real
  fecha_credito = st.sidebar.date_input("Fecha del Préstamo", value=date.today())
  nombre_cliente = st.sidebar.text_input("Nombre y Apellido del Cliente")
  cobrador_seleccionado = st.sidebar.selectbox("Asignar a Ruta", rutas_disponibles)

  capital_prestado = st.sidebar.number_input(
      "Capital Prestado ($)", min_value=0, value=100000, step=10000, format="%d"
  )
  capital_fmt = f"${capital_prestado:,.0f}".replace(",", ".")
  st.sidebar.caption(f"👁️ Capital: **{capital_fmt}**")

  interes_porcentaje = st.sidebar.number_input(
      "Interés (%)", min_value=0.0, value=20.0, step=5.0
  )
  
  dias_plazo = st.sidebar.number_input(
      "Plazo en Cuotas (Días)", min_value=1, value=24, step=1
  )

  # Cálculo previo en vivo de la cuota diaria para que sepas exactamente de cuánto queda
  total_prev = capital_prestado + (capital_prestado * (interes_porcentaje / 100))
  cuota_prev = int(total_prev / dias_plazo) if dias_plazo > 0 else 0
  cuota_fmt = f"${cuota_prev:,.0f}".replace(",", ".")
  st.sidebar.info(f"💡 **Cuota Diaria estimada:** {cuota_fmt}")

  if st.sidebar.button("💾 Guardar Préstamo", type="primary"):
    if not nombre_cliente.strip():
      st.sidebar.error("⚠️ Debes ingresar el nombre del cliente.")
    else:
      total_calculado = int(
          capital_prestado + (capital_prestado * (interes_porcentaje / 100))
      )
      cuota_diaria_calculada = (
          int(total_calculado / dias_plazo) if dias_plazo > 0 else 0
      )
      fecha_str = fecha_credito.strftime("%Y-%m-%d")
      
      cursor = conn.cursor()
      cursor.execute(
          """
                INSERT INTO creditos (fecha_prestamo, nombre_cliente, cobrador, capital_prestado, interes_porcentaje, total_a_pagar, dias_plazo, cuota_diaria, saldo_pendiente, estado)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
          (
              fecha_str,
              nombre_cliente.strip(),
              cobrador_seleccionado,
              int(capital_prestado),
              float(interes_porcentaje),
              int(total_calculado),
              int(dias_plazo),
              int(cuota_diaria_calculada),
              int(total_calculado),
              "Activo",
          ),
      )
      conn.commit()
      st.sidebar.success(f"✅ Préstamo registrado para {nombre_cliente}")
      st.rerun()

# -------------------------------------------------------------------
# PANEL DE CARTERA Y GESTIÓN DE COBROS POR RUTA PROTEGIDA
# -------------------------------------------------------------------
st.header("📊 Cartera de Cobros por Ruta")

if not rutas_disponibles:
  st.info(
      "ℹ️ Comienza creando una ruta con clave en la barra lateral para"
      " visualizar las tablas."
  )
else:
  tabs = st.tabs([f"📍 {r}" for r in rutas_disponibles])

  for idx, ruta in enumerate(rutas_disponibles):
    with tabs[idx]:
      st.subheader(f"Control de Cobros - {ruta}")

      clave_esperada = dic_passwords_rutas.get(ruta, "")
      session_key = f"ruta_desbloqueada_{ruta}"

      if clave_esperada and not st.session_state.get(session_key, False):
        st.warning(
            f"🔒 Esta ruta está protegida. Ingresa la contraseña de '{ruta}'"
            " para ver los créditos y registrar abonos."
        )
        col_c1, col_c2 = st.columns([2, 1])
        with col_c1:
          pass_ingresada = st.text_input(
              f"Contraseña para {ruta}:",
              type="password",
              key=f"input_pass_{ruta}",
          )
        with col_c2:
          st.markdown("<br>", unsafe_allow_html=True)
          btn_desbloquear = st.button(
              "Desbloquear Ruta", key=f"btn_unlock_{ruta}"
          )

        if btn_desbloquear:
          if pass_ingresada == clave_esperada:
            st.session_state[session_key] = True
            st.rerun()
          else:
            st.error("❌ Contraseña de ruta incorrecta.")
      else:
        if clave_esperada:
          if st.button(
              f"🔒 Bloquear / Cerrar Sesión de {ruta}", key=f"lock_{ruta}"
          ):
            st.session_state[session_key] = False
            st.rerun()

        st.markdown("---")
        
        tab_activos, tab_historial = st.tabs(["📋 Créditos Activos", "📅 Historial de Pagos Realizados"])

        with tab_activos:
          query = (
              "SELECT * FROM creditos WHERE cobrador = ? AND estado = 'Activo' ORDER"
              " BY id DESC"
          )
          df = pd.read_sql_query(query, conn, params=(ruta,))

          if not df.empty:
            total_cartera = df["total_a_pagar"].sum()
            total_pendiente = df["saldo_pendiente"].sum()
            total_prestado_global = df["capital_prestado"].sum()

            m1, m2, m3 = st.columns(3)
            m1.metric(
                "💵 Capital Prestado",
                f"${total_prestado_global:,.0f}".replace(",", "."),
            )
            m2.metric(
                "📋 Total a Recaudar", f"${total_cartera:,.0f}".replace(",", ".")
            )
            m3.metric(
                "⚠️ Saldo Pendiente", f"${total_pendiente:,.0f}".replace(",", ".")
            )

            st.markdown("---")
            st.caption(
                "Marca la casilla **Pago Hoy** en los clientes que hayan abonado su"
                " cuota diaria y haz clic en el botón inferior para registrar"
                " el cobro con su fecha actual."
            )

            df_mostrar = df.copy()

            df_mostrar["capital_prestado"] = df_mostrar["capital_prestado"].apply(
                lambda x: f"${x:,.0f}".replace(",", ".")
            )
            df_mostrar["total_a_pagar"] = df_mostrar["total_a_pagar"].apply(
                lambda x: f"${x:,.0f}".replace(",", ".")
            )
            df_mostrar["cuota_diaria_fmt"] = df_mostrar["cuota_diaria"].apply(
                lambda x: f"${x:,.0f}".replace(",", ".")
            )
            df_mostrar["saldo_pendiente"] = df_mostrar["saldo_pendiente"].apply(
                lambda x: f"${x:,.0f}".replace(",", ".")
            )

            df_mostrar.insert(0, "Abonar_Cuota", False)

            columnas_visibles = [
                "Abonar_Cuota",
                "fecha_prestamo",
                "nombre_cliente",
                "capital_prestado",
                "total_a_pagar",
                "cuota_diaria_fmt",
                "saldo_pendiente",
                "estado",
            ]

            df_editado = st.data_editor(
                df_mostrar[columnas_visibles + ["id"]],
                column_config={
                    "Abonar_Cuota": st.column_config.CheckboxColumn(
                        "Pago Hoy", default=False
                    ),
                    "id": None,
                    "fecha_prestamo": st.column_config.TextColumn(
                        "Fecha", disabled=True
                    ),
                    "nombre_cliente": st.column_config.TextColumn(
                        "Cliente", disabled=True
                    ),
                    "capital_prestado": st.column_config.TextColumn(
                        "Capital ($)", disabled=True
                    ),
                    "total_a_pagar": st.column_config.TextColumn(
                        "Total Crédito ($)", disabled=True
                    ),
                    "cuota_diaria_fmt": st.column_config.TextColumn(
                        "Cuota Diaria ($)", disabled=True
                    ),
                    "saldo_pendiente": st.column_config.TextColumn(
                        "Saldo Deuda ($)", disabled=True
                    ),
                    "estado": st.column_config.TextColumn("Estado", disabled=True),
                },
                disabled=[
                    "fecha_prestamo",
                    "nombre_cliente",
                    "capital_prestado",
                    "total_a_pagar",
                    "cuota_diaria_fmt",
                    "saldo_pendiente",
                    "estado",
                ],
                hide_index=True,
                use_container_width=True,
                key=f"editor_{ruta}",
            )

            filas_abonadas = df_editado[df_editado["Abonar_Cuota"] == True]
            if not filas_abonadas.empty:
              if st.button(
                  f"💰 Registrar Abonos Diarios - {ruta}",
                  key=f"btn_abono_{ruta}",
                  type="primary",
              ):
                cursor = conn.cursor()
                fecha_hoy = date.today().strftime("%Y-%m-%d")
                
                for index, row in filas_abonadas.iterrows():
                  credito_id = row["id"]
                  nombre_cli = row["nombre_cliente"]
                  
                  cursor.execute(
                      "SELECT saldo_pendiente, cuota_diaria FROM creditos WHERE id = ?",
                      (credito_id,),
                  )
                  res = cursor.fetchone()
                  if res:
                    saldo_actual, cuota = res
                    nuevo_saldo = max(0, saldo_actual - cuota)
                    nuevo_estado = "Cancelado" if nuevo_saldo == 0 else "Activo"

                    cursor.execute(
                        "UPDATE creditos SET saldo_pendiente = ?, estado = ? WHERE id = ?",
                        (nuevo_saldo, nuevo_estado, credito_id),
                    )

                    cursor.execute(
                        """
                        INSERT INTO historial_pagos (credito_id, nombre_cliente, cobrador, monto_pagado, fecha_pago)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (credito_id, nombre_cli, ruta, cuota, fecha_hoy)
                    )

                conn.commit()
                st.success(
                    f"✅ ¡Abonos registrados con fecha de hoy correctamente para la ruta {ruta}!"
                )
                st.rerun()
          else:
            st.info(
                f"No hay créditos activos registrados actualmente para la ruta"
                f" '{ruta}'."
            )

        with tab_historial:
          st.markdown(f"### 📅 Registro Histórico de Abonos - {ruta}")
          st.caption("Los pagos de cada cliente se muestran en bloques separados y organizados.")

          query_historial = """
              SELECT fecha_pago, nombre_cliente, monto_pagado 
              FROM historial_pagos 
              WHERE cobrador = ? 
              ORDER BY nombre_cliente ASC, id DESC
          """
          df_hist = pd.read_sql_query(query_historial, conn, params=(ruta,))

          if not df_hist.empty:
            clientes_unicos = df_hist["nombre_cliente"].unique()

            for cliente in clientes_unicos:
              st.markdown(f"#### 👤 Cliente: `{cliente.upper()}`")
              df_cliente = df_hist[df_hist["nombre_cliente"] == cliente].copy()
              
              df_cliente["monto_pagado_fmt"] = df_cliente["monto_pagado"].apply(
                  lambda x: f"${x:,.0f}".replace(",", ".")
              )
              
              df_cliente_mostrar = df_cliente[["fecha_pago", "monto_pagado_fmt"]].rename(
                  columns={
                      "fecha_pago": "Fecha del Pago",
                      "monto_pagado_fmt": "Monto Abonado ($)"
                  }
              )

              st.dataframe(df_cliente_mostrar, use_container_width=True, hide_index=True)
              st.markdown("<br>", unsafe_allow_html=True)
          else:
            st.info("ℹ️ Aún no hay registros de pagos históricos en esta ruta.")