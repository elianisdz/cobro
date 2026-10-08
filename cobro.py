import sqlite3
from datetime import datetime
import streamlit as st

# --- CONFIGURACIÓN DE LA BASE DE DATOS ---
conn = sqlite3.connect("sistema_creditos.db", check_same_thread=False)
cursor = conn.cursor()

# Crear tablas si no existen
cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        telefono TEXT,
        direccion TEXT
    )
"""
)

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS creditos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_id INTEGER,
        monto_total REAL NOT NULL,
        interes REAL NOT NULL,
        monto_con_interes REAL NOT NULL,
        cuotas INTEGER NOT NULL,
        valor_cuota REAL NOT NULL,
        frecuencia TEXT NOT NULL,
        fecha_inicio TEXT NOT NULL,
        estado TEXT DEFAULT 'Activo',
        FOREIGN KEY(cliente_id) REFERENCES clientes(id)
    )
"""
)

cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS pagos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        credito_id INTEGER,
        fecha_pago TEXT NOT NULL,
        monto_pagado REAL NOT NULL,
        FOREIGN KEY(credito_id) REFERENCES creditos(id)
    )
"""
)
conn.commit()

# --- DISEÑO Y CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Sistema de Cobro y Créditos", page_icon="💰", layout="wide"
)

# Estilos CSS personalizados
st.markdown(
    """
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; font-weight: bold; }
    .metric-card { background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    </style>
""",
    unsafe_allow_html=True,
)

st.title("💸 Sistema de Gestión de Cobros y Créditos")

# --- MENÚ LATERAL ---
menu = st.sidebar.selectbox(
    "Menú de Navegación",
    [
        "📊 Inicio / Resumen",
        "👥 Clientes",
        "💳 Nuevo Crédito",
        "💵 Registrar Abono/Pago",
        "📋 Historial y Cuentas",
    ],
)


# --- 1. INICIO / RESUMEN ---
if menu == "📊 Inicio / Resumen":
  st.subheader("Resumen General del Sistema")

  # Métricas
  try:
    cursor.execute("SELECT COUNT(*) FROM clientes")
    total_clientes = cursor.fetchone()[0]

    cursor.execute(
        "SELECT SUM(monto_con_interes) FROM creditos WHERE estado = 'Activo'"
    )
    dinero_prestado = cursor.fetchone()[0] or 0.0

    cursor.execute(
        """
        SELECT SUM(p.monto_pagado) FROM pagos p 
        JOIN creditos c ON p.credito_id = c.id 
        WHERE c.estado = 'Activo'
    """
    )
    dinero_recuperado = cursor.fetchone()[0] or 0.0

    saldo_pendiente = dinero_prestado - dinero_recuperado
  except Exception as e:
    total_clientes, dinero_prestado, dinero_recuperado, saldo_pendiente = (
        0,
        0,
        0,
        0,
    )

  col1, col2, col3, col4 = st.columns(4)
  with col1:
    st.metric("Total Clientes", total_clientes)
  with col2:
    st.metric("Créditos Activos ($)", f"${dinero_prestado:,.2f}")
  with col3:
    st.metric("Dinero Recaudado ($)", f"${dinero_recuperado:,.2f}")
  with col4:
    st.metric("Saldo Pendiente ($)", f"${saldo_pendiente:,.2f}")

  st.markdown("---")
  st.info(
      "Utiliza el menú lateral para navegar entre los registros de clientes,"
      " otorgar créditos o registrar abonos."
  )


# --- 2. CLIENTES ---
elif menu == "👥 Clientes":
  st.subheader("Gestión de Clientes")

  with st.form("form_cliente"):
    st.write("Registrar Nuevo Cliente")
    nombre = st.text_input("Nombre Completo")
    telefono = st.text_input("Teléfono / Celular")
    direccion = st.text_input("Dirección")
    submit_cliente = st.form_submit_button("Guardar Cliente")

    if submit_cliente:
      if nombre.strip() != "":
        cursor.execute(
            "INSERT INTO clientes (nombre, telefono, direccion) VALUES (?, ?,"
            " ?)",
            (nombre, telefono, direccion),
        )
        conn.commit()
        st.success(f"¡Cliente '{nombre}' registrado exitosamente!")
      else:
        st.error("El nombre del cliente es obligatorio.")

  st.markdown("---")
  st.subheader("Lista de Clientes Registrados")
  cursor.execute("SELECT id, nombre, telefono, direccion FROM clientes")
  clientes = cursor.fetchall()

  if clientes:
    for c in clientes:
      st.write(
          f"**ID:** {c[0]} | **Nombre:** {c[1]} | **Tel:** {c[2]} |"
          f" **Dirección:** {c[3]}"
      )
  else:
    st.info("No hay clientes registrados todavía.")


# --- 3. NUEVO CRÉDITO ---
elif menu == "💳 Nuevo Crédito":
  st.subheader("Otorgar Nuevo Crédito")

  cursor.execute("SELECT id, nombre FROM clientes")
  clientes = cursor.fetchall()

  if not clientes:
    st.warning(
        "Primero debes registrar al menos un cliente en la sección 'Clientes'."
    )
  else:
    clientes_dict = {nombre: cid for cid, nombre in clientes}
    cliente_seleccionado = st.selectbox(
        "Seleccionar Cliente", list(clientes_dict.keys())
    )
    cliente_id = clientes_dict[cliente_seleccionado]

    col1, col2 = st.columns(2)
    with col1:
      monto_total = st.number_input(
          "Monto del Préstamo ($)", min_value=0.0, step=100.0
      )
      porcentaje_interes = st.number_input(
          "Porcentaje de Interés Total (%)", min_value=0.0, step=1.0
      )
    with col2:
      cuotas = st.number_input("Número de Cuotas", min_value=1, step=1)
      frecuencia = st.selectbox(
          "Frecuencia de Pago", ["Diario", "Semanal", "Quincenal", "Mensual"]
      )

    if monto_total > 0:
      interes_monto = monto_total * (porcentaje_interes / 100.0)
      monto_con_interes = monto_total + interes_monto
      valor_cuota = monto_con_interes / cuotas if cuotas > 0 else 0

      st.markdown("---")
      st.markdown("### Resumen del Crédito")
      st.write(f"- **Monto Base:** ${monto_total:,.2f}")
      st.write(f"- **Interés Total:** ${interes_monto:,.2f}")
      st.write(f"- **Total a Pagar:** ${monto_con_interes:,.2f}")
      st.write(f"- **Valor por Cuota ({cuotas} cuotas):** ${valor_cuota:,.2f}")

      if st.button("Aprobar y Registrar Crédito"):
        fecha_inicio = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            """
                    INSERT INTO creditos (cliente_id, monto_total, interes, monto_con_interes, cuotas, valor_cuota, frecuencia, fecha_inicio, estado)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Activo')
                """,
            (
                cliente_id,
                monto_total,
                interes_monto,
                monto_con_interes,
                cuotas,
                valor_cuota,
                frecuencia,
                fecha_inicio,
            ),
        )
        conn.commit()
        st.success("¡Crédito registrado y activado con éxito!")


# --- 4. REGISTRAR ABONO / PAGO ---
elif menu == "💵 Registrar Abono/Pago":
  st.subheader("Registrar Abono o Pago de Cuota")

  cursor.execute(
      """
        SELECT c.id, cl.nombre, c.monto_con_interes, c.valor_cuota 
        FROM creditos c 
        JOIN clientes cl ON c.cliente_id = cl.id 
        WHERE c.estado = 'Activo'
    """
  )
  creditos_activos = cursor.fetchall()

  if not creditos_activos:
    st.info("No hay créditos activos en este momento.")
  else:
    creditos_opciones = {
        f"Crédito #{c[0]} - {c[1]} (Total: ${c[2]:,.2f})": c[0]
        for c in creditos_activos
    }
    credito_seleccionado_str = st.selectbox(
        "Seleccionar Crédito", list(creditos_opciones.keys())
    )
    credito_id = creditos_opciones[credito_seleccionado_str]

    # Calcular lo que ya se ha pagado de este crédito
    cursor.execute(
        "SELECT SUM(monto_pagado) FROM pagos WHERE credito_id = ?", (credito_id,)
    )
    pagado_hasta_hoy = cursor.fetchone()[0] or 0.0

    cursor.execute(
        "SELECT monto_con_interes, valor_cuota FROM creditos WHERE id = ?",
        (credito_id,),
    )
    info_credito = cursor.fetchone()
    total_deuda = info_credito[0]
    sugerencia_pago = info_credito[1]

    pendiente = total_deuda - pagado_hasta_hoy

    st.write(f"**Deuda Total:** ${total_deuda:,.2f}")
    st.write(f"**Pagado hasta la fecha:** ${pagado_hasta_hoy:,.2f}")
    st.write(
        f"**Saldo Pendiente:** <span style='color:red;'>${pendiente:,.2f}</span>",
        unsafe_allow_html=True,
    )

    monto_abono = st.number_input(
        "Monto del Abono