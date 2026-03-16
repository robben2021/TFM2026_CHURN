import streamlit as st #Importar libreria principal
import pandas as pd #Importar libreria pandas
import os #Importar modulo sistema
import glob #Importar modulo busqueda archivos

st.set_page_config(page_title="Predicción de la Deserción de Abonados", layout="wide") #Establecer configuracion responsiva

# --- RUTAS FIJAS 2025 ---
RUTA_GOLD = "ETL/datalake/gold/clean/dataset_master_gold.parquet" #Definir ruta gold
RUTA_MODELADO = "MODELADO/data/dataset_modelado_churn.parquet" #Definir ruta modelado
RUTA_RESUMEN_CSV = "EDA/data/resumen_estadistico_completo.csv" #Definir ruta csv

st.title("📊 Predicción de la Deserción de Abonados") #Crear titulo aplicacion

# --- MENU LATERAL ---
st.sidebar.header("MENÚ PRINCIPAL") #Configurar encabezado lateral
#Usar radio buttons para una navegacion mas solida entre las dos grandes areas
menu_principal = st.sidebar.radio(
    "Selecciona un entorno:", 
    ["1️⃣ Predicciones Mensuales (Producción)", "2️⃣ Análisis Histórico y Modelo (2025)"]
) #Crear menu navegacion principal

st.sidebar.markdown("---") #Agregar separador visual
if st.sidebar.button("ACTUALIZAR DATOS"): #Agregar boton actualizacion (limpia cache)
    st.cache_data.clear() #Limpiar memoria
    st.sidebar.success("Datos actualizados correctamente.") #Mostrar exito

# =====================================================================
# SECCIÓN 1: PREDICCIONES MENSUALES DINÁMICAS (EL PRESENTE)
# =====================================================================
if menu_principal == "1️⃣ Predicciones Mensuales (Producción)": #Validar seccion mensual
    st.header("Monitoreo Mensual de Riesgo de Abandono (Churn)") #Crear encabezado
    
    # --- LOGICA DINAMICA PARA ENCONTRAR MESES ---
    ruta_scored = "ETL/datalake/gold/scored/" #Definir carpeta de busqueda
    if os.path.exists(ruta_scored): #Verificar que exista la carpeta
        #Buscar todos los archivos csv que empiecen con predicciones_churn_
        archivos_pred = glob.glob(f"{ruta_scored}predicciones_churn_*.csv") #Listar archivos
        #Extraer solo los 4 digitos del mes (AAMM) del nombre del archivo
        meses_disponibles = sorted([f.split('_')[-1].replace('.csv', '') for f in archivos_pred], reverse=True) #Extraer y ordenar meses
    else:
        meses_disponibles = [] #Lista vacia si no hay carpeta
        
    if meses_disponibles: #Si hay meses con datos
        mes_seleccionado = st.selectbox("📅 Selecciona el periodo a analizar (AAMM):", meses_disponibles) #Crear selector dinamico
        
        #Cargar datos del mes seleccionado
        df_mes = pd.read_csv(f"{ruta_scored}predicciones_churn_{mes_seleccionado}.csv") #Cargar predicciones
        
        # --- KPIs DEL MES ---
        clientes_riesgo = len(df_mes[df_mes['PREDICCION_ABANDONO'] == 1]) #Contar clientes clase 1
        riesgo_alto = len(df_mes[df_mes['PROBABILIDAD_RIESGO'] >= 0.15]) #Contar clientes con probabilidad > 15%
        
        k1, k2, k3 = st.columns(3) #Crear columnas
        k1.metric("Total Clientes Evaluados", f"{len(df_mes):,}") #Metrica total
        k2.metric("Clientes Predicción Churn (Clase 1)", f"{clientes_riesgo:,}") #Metrica clase 1
        k3.metric("Clientes en Riesgo Alto (>15%)", f"{riesgo_alto:,}") #Metrica umbral 15
        
        st.markdown("---") #Separador
        
        # --- VISTA DIVIDIDA: SHAP GLOBAL VS BUSCADOR INDIVIDUAL ---
        col_grafico, col_buscador = st.columns([1.5, 1]) #Crear proporciones columnas
        
        with col_grafico: #Columna grafico SHAP
            st.subheader("Disparadores de Riesgo del Mes") #Subencabezado
            ruta_shap = f"MODELADO/graficos_modelado_{mes_seleccionado}/01_shap_summary_{mes_seleccionado}.png" #Ruta imagen
            if os.path.exists(ruta_shap): #Verificar si imagen existe
                st.image(ruta_shap, use_column_width=True) #Mostrar SHAP del mes
            else:
                st.warning("El gráfico SHAP para este mes aún no ha sido generado.") #Aviso
                
        with col_buscador: #Columna buscador cliente
            st.subheader("Buscador Individual") #Subencabezado
            st.info("Busca un contrato específico para ver su probabilidad de cancelación en este mes.") #Instruccion
            contrato_input = st.text_input("🔍 Ingresa el Número de Contrato:") #Caja de texto
            
            if contrato_input: #Si el usuario teclea algo
                resultado = df_mes[df_mes['CONTRATO'].astype(str) == contrato_input] #Buscar contrato
                if not resultado.empty: #Si lo encuentra
                    score_cliente = resultado['PROBABILIDAD_RIESGO'].values[0] * 100 #Extraer probabilidad
                    st.metric(label="Probabilidad de Abandono", value=f"{score_cliente:.2f} %") #Mostrar porcentaje
                    #Aqui despues se generaria la cascada de shap
                else:
                    st.error("Contrato no encontrado en este periodo.") #Error no existe

    else: #Si no hay archivos en la carpeta
        st.warning("No se encontraron predicciones mensuales en el Datalake. Ejecuta el pipeline.") #Aviso


# =====================================================================
# SECCIÓN 2: HISTÓRICO Y MODELADO 2025 (EL PASADO)
# =====================================================================
elif menu_principal == "2️⃣ Análisis Histórico y Modelo (2025)": #Validar seccion historico
    st.header("Análisis Histórico y Entrenamiento del Modelo (Año Base 2025)") #Crear encabezado seccion
    
    # NUEVO ORDEN DE PESTAÑAS: 1. Modelado, 2. Resumen, 3. EDA
    tab_modelado, tab_resumen, tab_eda = st.tabs(["⚙️ Desempeño del Modelo", "📋 Resumen Ejecutivo", "📈 Exploración de Datos (EDA)"]) #Crear pestañas
    
    # --- PESTAÑA 1: MODELADO ---
    with tab_modelado: 
        st.subheader("Principales Hallazgos: Influencia de Variables en el Riesgo de Cancelación") #Crear subencabezado
        st.image("MODELADO/graficos_modelado/03_shap_xgboost.png", caption="Interpretación de impacto mediante valores SHAP") #Exhibir grafico shap 2025
        st.info("El gráfico superior identifica los disparadores críticos del abandono de clientes.") #Mostrar nota informativa
        
        st.markdown("---") #Separador
        st.subheader("Evaluación y Desempeño del Modelo Campeón") #Subencabezado
        col_roc, col_mat = st.columns(2) #Columnas desempeño
        with col_roc:
            st.image("MODELADO/graficos_modelado/02_curva_roc_combinada.png", caption="Comparativa de Capacidad Predictiva (Curva ROC)") #Exhibir curva roc
        with col_mat:
            st.image("MODELADO/graficos_modelado/01_matrices_confusion_comparativa.png", caption="Comparativa de Matrices de Confusión") #Exhibir matrices comparativas

    # --- PESTAÑA 2: RESUMEN EJECUTIVO ---
    with tab_resumen: 
        st.subheader("Resumen Datos Clave") #Crear encabezado seccion
        try:
            df_churn = pd.read_parquet(RUTA_MODELADO) #Cargar datos modelado
            df_resumen = pd.read_csv(RUTA_RESUMEN_CSV) #Cargar resumen estadistico
            
            # Fila uno de metricas generales
            m1, m2, m3 = st.columns(3) #Crear columnas primera fila
            m1.metric("Total Registros 2025", f"{len(df_churn):,}") #Exhibir metrica total
            m2.metric("Nivel Optico Promedio", f"{df_churn['RX_AVG_PROMEDIO'].mean():.2f} dBm") #Exhibir metrica potencia
            m3.metric("Días Atención Promedio", f"{df_churn['DIAS_ATENCION_PROMEDIO'].mean():.1f}") #Exhibir metrica dias
            
            st.markdown("<br>", unsafe_allow_html=True) #Salto de linea para diseño
            
            # Fila dos de metricas extraidas del resumen estadistico detallado (Ahora apiladas verticalmente)
            st.metric("Top Paquete", f"{df_resumen.loc[df_resumen['Columna'] == 'PAQUETE_x', 'Top_Valor'].iloc[0]}", f"{df_resumen.loc[df_resumen['Columna'] == 'PAQUETE_x', 'Valores_Unicos'].iloc[0]} ÚNICOS") #Exhibir metrica paquete
            st.metric("Top Motivo", f"{df_resumen.loc[df_resumen['Columna'] == 'MOTIVO_PEDIDO', 'Top_Valor'].iloc[0]}", f"{df_resumen.loc[df_resumen['Columna'] == 'MOTIVO_PEDIDO', 'Valores_Unicos'].iloc[0]} ÚNICOS") #Exhibir metrica motivo
            st.metric("Top Detalle", f"{df_resumen.loc[df_resumen['Columna'] == 'DETALLE_PEDIDO1', 'Top_Valor'].iloc[0]}", f"{df_resumen.loc[df_resumen['Columna'] == 'DETALLE_PEDIDO1', 'Valores_Unicos'].iloc[0]} ÚNICOS") #Exhibir metrica detalle
            st.metric("Top Modelo ONT", f"{df_resumen.loc[df_resumen['Columna'] == 'ONT_MODEL', 'Top_Valor'].iloc[0]}", f"{df_resumen.loc[df_resumen['Columna'] == 'ONT_MODEL', 'Valores_Unicos'].iloc[0]} ÚNICOS") #Exhibir metrica modelo
            
            st.markdown("---") #Agregar separador visual
            col_left, col_right = st.columns([1, 1]) #Crear columnas tablas
            with col_left: #Configurar columna izquierda
                st.subheader("Vista Previa de Datos Preparados") #Crear subencabezado datos
                st.dataframe(df_churn.head(10), use_container_width=True) #Mostrar dataframe resumido
            with col_right: #Configurar columna derecha
                st.subheader("Descripción Estadística Base") #Crear subencabezado estadistica
                st.dataframe(df_resumen, use_container_width=True) #Mostrar tabla resumen completa
        except Exception as e:
            st.error(f"Error al cargar los datos históricos: {e}") #Manejo de errores
            
    # --- PESTAÑA 3: EDA (CON TODOS LOS GRÁFICOS) ---
    with tab_eda: 
        st.subheader("Comportamiento de las Variables Principales") #Subencabezado
        col1, col2 = st.columns(2) #Crear columnas graficos
        with col1: #Configurar columna uno
            st.image("EDA/graficos_eda/01_histograma_rx_avg.png", caption="Distribución de Potencia") #Exhibir histograma
            st.image("EDA/graficos_eda/02_barras_motivo_pedido.png", caption="Frecuencia de Motivos de Fallas") #Exhibir barras motivos
            st.image("EDA/graficos_eda/01_ont_vs_tasa_reincidencia.png", caption="Tasa de Reincidencia por Modelo de ONT") #Exhibir grafico ont reincidencia 
        with col2: #Configurar columna dos
            st.image("EDA/graficos_eda/03_churn_vs_potencia.png", caption="Relación Nivel Óptico y Deserción") #Exhibir dispersion churn
            st.image("EDA/graficos_eda/03_donut_ont_model.png", caption="Distribución de modelos ONTs") #Exhibir grafico dona
            st.image("EDA/graficos_eda/02_zona_vs_tiempo.png", caption="Top Zonas con Mayor Demora (SLA)") #Exhibir grafico zona vs tiempo