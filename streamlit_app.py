import streamlit as st
from pathlib import Path
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title='Finanzas App', layout='centered')
st.title('Mi Finanzas - Streamlit')

BASE_DIR = Path(__file__).parent

CATEGORIES_FILE = "/workspaces/gdp-dashboard/origen/desplegables.xlsx"
OUTPUT_FILE =  "/workspaces/gdp-dashboard/destino/cuentas.xlsx"
# Archivos

     

# Cargar categorias
@st.cache_data
def load_categories(path):
    if not os.path.exists(path):
        st.error(f"No se encontró el archivo '{path}'. Sube el archivo y recarga la app.")
        return pd.DataFrame(columns=['categoria_tipo_finanza', 'subcategoria_tipo_finanza', 'tipo_finanza'])
    return pd.read_excel(path)

categorias_df = load_categories(CATEGORIES_FILE)

# Asegurar archivo de salida
if not os.path.exists(OUTPUT_FILE):
    df_init = pd.DataFrame(columns=[
        'categoria_tipo_finanza',
        'subcategoria_tipo_finanza',
        'tipo_finanza',
        'valor',
        'observacion',
        'fecha'
    ])
    df_init.to_excel(OUTPUT_FILE, index=False)

# Inicializar session state
if 'categoria' not in st.session_state:
    st.session_state['categoria'] = None
if 'subcategoria' not in st.session_state:
    st.session_state['subcategoria'] = None
if 'tipo' not in st.session_state:
    st.session_state['tipo'] = None

# --- Paso 1: Mostrar botones de categorias ---
st.subheader('Selecciona el tipo de movimiento')
unique_cats = categorias_df['categoria_tipo_finanza'].dropna().unique().tolist()

# Mostrar botones en una fila (máx 5 por fila)
cols = st.columns(min(len(unique_cats), 5))
for i, cat in enumerate(unique_cats):
    with cols[i % len(cols)]:
        if st.button(cat):
            st.session_state['categoria'] = cat
            st.session_state['subcategoria'] = None
            st.session_state['tipo'] = None
            st.rerun()

# Botón para limpiar selección
if st.session_state['categoria']:
    if st.button('Volver al inicio'):
        st.session_state['categoria'] = None
        st.session_state['subcategoria'] = None
        st.session_state['tipo'] = None
        st.rerun()

# --- Paso 2: Si seleccionó categoria, mostrar subcategorías ---
if st.session_state['categoria']:
    st.markdown('---')
    st.subheader(f"Subcategorías para: {st.session_state['categoria']}")
    df_sub = categorias_df[categorias_df['categoria_tipo_finanza'] == st.session_state['categoria']]
    unique_subs = df_sub['subcategoria_tipo_finanza'].dropna().unique().tolist()

    if not unique_subs:
        st.info('No hay subcategorías definidas para esta categoría.')
    else:
        sub_cols = st.columns(min(len(unique_subs), 5))
        for i, sub in enumerate(unique_subs):
            with sub_cols[i % len(sub_cols)]:
                if st.button(sub):
                    st.session_state['subcategoria'] = sub
                    st.session_state['tipo'] = None
                    st.rerun()

# --- Paso 3: Si seleccionó subcategoria, mostrar formulario ---
if st.session_state['categoria'] and st.session_state.get('subcategoria'):
    st.markdown('---')
    st.subheader(f"Registrar: {st.session_state['categoria']} → {st.session_state['subcategoria']}")

    # tipos filtrados
    df_tipo = categorias_df[
        (categorias_df['categoria_tipo_finanza'] == st.session_state['categoria']) &
        (categorias_df['subcategoria_tipo_finanza'] == st.session_state['subcategoria'])
    ]
    unique_tipos = df_tipo['tipo_finanza'].dropna().unique().tolist()

    tipo_seleccionado = st.selectbox('Tipo', options=unique_tipos if unique_tipos else ['No definido'])
    valor = st.number_input('Valor', min_value=0.0, format='%f')
    descripcion = st.text_input('Descripcion')

    if st.button('Guardar'):
        # Preparar registro
        fecha = datetime.now().strftime('%d-%m-%Y')
        nuevo = {
            'categoria_tipo_finanza': st.session_state['categoria'],
            'subcategoria_tipo_finanza': st.session_state['subcategoria'],
            'tipo_finanza': tipo_seleccionado,
            'valor': valor,
            'observacion': descripcion,
            'fecha': fecha
        }

        # Leer archivo existente y anexar
        try:
            df_exist = pd.read_excel(OUTPUT_FILE)
        except Exception:
            df_exist = pd.DataFrame(columns=['categoria_tipo_finanza','subcategoria_tipo_finanza','tipo_finanza','valor','observacion','fecha'])

        df_exist = pd.concat([df_exist, pd.DataFrame([nuevo])], ignore_index=True)
        df_exist.to_excel(OUTPUT_FILE, index=False)

        st.success('Registro guardado correctamente.')

        # Opción A: volver al inicio (limpiar todo)
        st.session_state['categoria'] = None
        st.session_state['subcategoria'] = None
        st.session_state['tipo'] = None
        st.rerun()

# --- Resumen rápido del estado actual ---
st.markdown('---')
st.subheader('Resumen rápido')
try:
    df_cuentas = pd.read_excel(OUTPUT_FILE)
    if not df_cuentas.empty:
        total_ingresos = df_cuentas[df_cuentas['categoria_tipo_finanza'].str.lower() == 'ingreso']['valor'].sum()
        total_gastos = df_cuentas[df_cuentas['categoria_tipo_finanza'].str.lower() == 'gasto']['valor'].sum()
        saldo = total_ingresos - total_gastos

        st.metric('Total Ingresos', f"{total_ingresos:,.2f}")
        st.metric('Total Gastos', f"{total_gastos:,.2f}")
        st.metric('Saldo', f"{saldo:,.2f}")

        with st.expander('Ver movimientos (últimos 10)'):
            st.dataframe(df_cuentas.tail(10))
    else:
        st.info('No hay registros aún en cuentas.xlsx')
except Exception as e:
    st.error(f'Error leyendo {OUTPUT_FILE}: {e}')

# Nota: coloca los archivos desplegables.xlsx y cuentas.xlsx en el mismo directorio de la app para que funcione correctamente.
