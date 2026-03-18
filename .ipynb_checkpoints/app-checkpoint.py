import streamlit as st #Importar libreria principal
import pandas as pd #Importar libreria pandas
import os #Importar modulo sistema

st.set_page_config(page_title="Predicción de la Deserción de Abonados", layout="wide") #Establecer configuracion responsiva

RUTA_GOLD = "ETL/datalake/gold/clean/dataset_master_gold.parquet" #Definir ruta gold
RUTA_MODELADO = "MODELADO/data/dataset_modelado_churn.parquet" #Definir ruta modelado
RUTA_RESUMEN_CSV = "EDA/data/resumen_estadistico_completo.csv" #Definir ruta csv

st.title("Predicción de la Deserción de Abonados") #Crear titulo aplicacion

st.sidebar.header("MENU") #Configurar encabezado lateral
st.sidebar.button("ACTUALIZAR DATOS") #Agregar boton actualizacion
st.sidebar.markdown("---") #Agregar separador visual

if "seccion" not in st.session_state: #Verificar estado sesion
    st.session_state.seccion = "PRINCIPAL" #Establecer seccion inicial

if st.sidebar.button("Dashboard Principal"): #Crear boton principal
    st.session_state.seccion = "PRINCIPAL" #Actualizar estado seccion

if st.sidebar.button("Resumen Datos Clave"): #Crear boton resumen
    st.session_state.seccion = "RESUMEN EJECUTIVO" #Actualizar estado seccion

if st.sidebar.button("Gráficos"): #Crear boton eda
    st.session_state.seccion = "EDA" #Actualizar estado seccion

if st.sidebar.button("Modelado"): #Crear boton modelado
    st.session_state.seccion = "MODELADO" #Actualizar estado seccion

if st.session_state.seccion == "PRINCIPAL": #Validar seccion principal
    st.header("Principales Hallazgos") #Crear encabezado seccion
    st.subheader("Influencia de Variables en el Riesgo de Cancelación") #Crear subencabezado importancia
    st.image("MODELADO/graficos_modelado/03_shap_xgboost.png", caption="Interpretacion de impacto mediante valores SHAP") #Exhibir grafico shap
    st.info("El gráfico superior identifica los disparadores criticos del abandono de clientes.") #Mostrar nota informativa

elif st.session_state.seccion == "RESUMEN EJECUTIVO": #Validar seccion resumen
    st.header("Resumen Datos Clave") #Crear encabezado seccion
    df_churn = pd.read_parquet(RUTA_MODELADO) #Cargar datos modelado
    df_resumen = pd.read_csv(RUTA_RESUMEN_CSV) #Cargar resumen estadistico
    
    #Fila uno de metricas generales
    m1, m2, m3 = st.columns(3) #Crear columnas primera fila
    m1.metric("Total Registros", f"{len(df_churn):,}") #Exhibir metrica total
    m2.metric("Nivel Optico Promedio", f"{df_churn['RX_AVG_PROMEDIO'].mean():.2f} dBm") #Exhibir metrica potencia
    m3.metric("Días Atención Promedio", f"{df_churn['DIAS_ATENCION_PROMEDIO'].mean():.1f}") #Exhibir metrica dias
    
    #Fila dos de metricas extraidas del resumen estadistico detallado
    #m4, m5, m6, m7 = st.columns(4) #Crear columnas segunda fila
    #Extraer y mostrar metricas para Paquete
    st.metric("Top Paquete", f"{df_resumen.loc[df_resumen['Columna'] == 'PAQUETE_x', 'Top_Valor'].iloc[0]}", f"{df_resumen.loc[df_resumen['Columna'] == 'PAQUETE_x', 'Valores_Unicos'].iloc[0]} UNICOS") #Exhibir metrica paquete
    #Extraer y mostrar metricas para Motivo Pedido
    st.metric("Top Motivo", f"{df_resumen.loc[df_resumen['Columna'] == 'MOTIVO_PEDIDO', 'Top_Valor'].iloc[0]}", f"{df_resumen.loc[df_resumen['Columna'] == 'MOTIVO_PEDIDO', 'Valores_Unicos'].iloc[0]} UNICOS") #Exhibir metrica motivo
    #Extraer y mostrar metricas para Detalle Pedido
    st.metric("Top Detalle", f"{df_resumen.loc[df_resumen['Columna'] == 'DETALLE_PEDIDO1', 'Top_Valor'].iloc[0]}", f"{df_resumen.loc[df_resumen['Columna'] == 'DETALLE_PEDIDO1', 'Valores_Unicos'].iloc[0]} UNICOS") #Exhibir metrica detalle
    #Extraer y mostrar metricas para Modelo ONT
    st.metric("Top Modelo ONT", f"{df_resumen.loc[df_resumen['Columna'] == 'ONT_MODEL', 'Top_Valor'].iloc[0]}", f"{df_resumen.loc[df_resumen['Columna'] == 'ONT_MODEL', 'Valores_Unicos'].iloc[0]} UNICOS") #Exhibir metrica modelo
    
    st.markdown("---") #Agregar separador visual
    col_left, col_right = st.columns([1, 1]) #Crear columnas tablas
    with col_left: #Configurar columna izquierda
        st.subheader("Vista Previa de Datos") #Crear subencabezado datos
        st.dataframe(df_churn.head(10), use_container_width=True) #Mostrar dataframe resumido
    with col_right: #Configurar columna derecha
        st.subheader("Descripcion Estadistica") #Crear subencabezado estadistica
        st.dataframe(df_resumen, use_container_width=True) #Mostrar tabla resumen completa

elif st.session_state.seccion == "EDA": #Validar seccion eda
    st.header("Gráficos con Principales Metricas") #Crear encabezado seccion
    col1, col2 = st.columns(2) #Crear columnas graficos
    with col1: #Configurar columna uno
        st.image("EDA/graficos_eda/01_histograma_rx_avg.png", caption="Distribucion de Potencia") #Exhibir histograma
        st.image("EDA/graficos_eda/02_barras_motivo_pedido.png", caption="Frecuencia de Motivos de Fallas") #Exhibir barras motivos
    with col2: #Configurar columna dos
        st.image("EDA/graficos_eda/03_churn_vs_potencia.png", caption="Relacion Nivel Optico y Deserción") #Exhibir dispersion churn
        st.image("EDA/graficos_eda/03_donut_ont_model.png", caption="Distribucion de modelos ONTs") #Exhibir grafico dona

elif st.session_state.seccion == "MODELADO": #Validar seccion modelado
    st.header("Evaluación y Desempeño del Modelo") #Crear encabezado seccion
    st.subheader("Comparativa de Matrices de Confusión") #Crear subencabezado matrices
    st.image("MODELADO/graficos_modelado/01_matrices_confusion_comparativa.png") #Exhibir matrices comparativas
    st.subheader("Comparativa de Capacidad Predictiva") #Crear subencabezado roc
    st.image("MODELADO/graficos_modelado/02_curva_roc_combinada.png") #Exhibir curva roc