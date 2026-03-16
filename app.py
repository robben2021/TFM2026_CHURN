import streamlit as st #Importar libreria principal
import pandas as pd #Importar libreria pandas
import os #Importar modulo sistema
import glob #Importar modulo busqueda archivos

st.set_page_config(page_title="Prediccion de la Desercion de Abonados 2026 CVR-MORELIA", layout="wide") # Establecer configuracion responsiva

def acceso():
    def password_entered(): #Validar contraseña ingresada
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  #Borrar contraseña por seguridad
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state: #Primera vez que entra
        st.text_input("Por favor, ingresa la clave de acceso al Dashboard:", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]: #Contraseña incorrecta
        st.text_input("Por favor, ingresa la clave de acceso al Dashboard:", type="password", on_change=password_entered, key="password")
        st.error("Clave incorrecta. Inténtalo de nuevo.")
        return False
    else: #Contraseña correcta
        return True

if acceso():
    RUTA_GOLD = "ETL/datalake/gold/clean/dataset_master_gold.parquet" #Definir ruta gold
    RUTA_MODELADO = "MODELADO/data/dataset_modelado_churn.parquet" #Definir ruta modelado
    RUTA_RESUMEN_CSV = "EDA/data/resumen_estadistico_completo.csv" #Definir ruta csv

    st.title("Predicción de la Deserción de Abonados 2026 CVR-MORELIA") #Crear titulo aplicacion

    st.sidebar.header("MENU PRINCIPAL") #Configurar encabezado lateral

    menu_principal = st.sidebar.radio(
        "Selecciona un escenario:", 
        ["Predicciones Mensuales 2026", "Analisis Historico y Modelo 2025"]
    ) #Crear menu navegacion principal

    st.sidebar.markdown("---") #Agregar separador visual

    if st.sidebar.button("ACTUALIZAR DATOS"): #Agregar boton actualizacion
        st.cache_data.clear() #Limpiar memoria
        st.sidebar.success("Datos actualizados correctamente.") #Mostrar exito

    if menu_principal == "Predicciones Mensuales 2026": # Validar seccion mensual
        st.header("Monitoreo Mensual de Riesgo de Abandono (Churn) 2026 CVR-MORELIA") #Crear encabezado
        
        ruta_scored = "ETL/datalake/gold/scored/" #Definir carpeta de busqueda
        if os.path.exists(ruta_scored): #Verificar existencia de carpeta
            archivos_pred = glob.glob(f"{ruta_scored}predicciones_churn_*.csv") #Listar archivos
            meses_disponibles = sorted([f.split('_')[-1].replace('.csv', '') for f in archivos_pred], reverse=True) #Extraer y ordenar meses
        else:
            meses_disponibles = [] #Crear lista vacia
            
        if meses_disponibles: #Validar meses con datos
            mes_seleccionado = st.selectbox("Selecciona el periodo a analizar (AAMM):", meses_disponibles) #Crear selector dinamico
            
            df_mes = pd.read_csv(f"{ruta_scored}predicciones_churn_{mes_seleccionado}.csv") #Cargar predicciones
            
            tab_predicciones, tab_resumen_mes, tab_eda_mes = st.tabs(["Predicciones y Riesgo", "Resumen Ejecutivo", "Exploracion de Datos"]) # Crear pestanas mensuales
            
            with tab_predicciones: #Configurar pestana predicciones
                if 'PREDICCION_CLASE' in df_mes.columns: #Verificar existencia de columna
                    clientes_riesgo = len(df_mes[df_mes['PREDICCION_ABONADO'] == 1]) #Contar clientes clase 1
                else:
                    clientes_riesgo = len(df_mes[df_mes['PROBABILIDAD_RIESGO'] >= 0.5]) #Calcular clase 1 basado en probabilidad
                    
                riesgo_alto = len(df_mes[df_mes['PROBABILIDAD_RIESGO'] >= 0.15]) #Contar clientes con probabilidad mayor a 15
                
                k1, k2, k3 = st.columns(3) #Crear columnas
                k1.metric("Total Clientes Evaluados", f"{len(df_mes):,}") #Mostrar metrica total
                k2.metric("Clientes Prediccion de Abandono", f"{clientes_riesgo:,}") #Mostrar metrica clase 1
                k3.metric("Clientes en Riesgo", f"{riesgo_alto:,}") #Mostrar metrica umbral 15
                
                st.markdown("---") #Agregar separador visual
                
                col_grafico, col_buscador = st.columns([1.5, 1]) #Crear proporciones columnas
                
                with col_grafico: #Configurar columna grafico SHAP
                    st.subheader("Indicadores de Riesgo del Mes") #Crear subencabezado
                    ruta_shap = f"MODELADO/graficos_modelado_{mes_seleccionado}/01_shap_summary_{mes_seleccionado}.png" #Definir ruta imagen
                    if os.path.exists(ruta_shap): #Verificar existencia de imagen
                        st.image(ruta_shap, use_column_width=True) #Mostrar SHAP del mes
                    else:
                        st.warning("El grafico SHAP para este mes aun no ha sido generado.") #Mostrar aviso
                        
                with col_buscador: #Configurar columna buscador cliente
                    st.subheader("Buscar Contrato") #Crear subencabezado
                    st.info("Busca un contrato especifico para ver su probabilidad de cancelacion en este mes.") #Mostrar instruccion
                    contrato_input = st.text_input("Ingresa el Numero de Contrato:") #Crear caja de texto
                    
                    if contrato_input: #Validar entrada de usuario
                        resultado = df_mes[df_mes['CONTRATO'].astype(str) == contrato_input] #Buscar contrato
                        if not resultado.empty: #Validar existencia de resultado
                            score_cliente = resultado['PROBABILIDAD_RIESGO'].values[0] * 100 #Extraer probabilidad
                            st.metric(label="Probabilidad de Abandono", value=f"{score_cliente:.2f} %") #Mostrar porcentaje
                        else:
                            st.error("Contrato no encontrado en este periodo.") #Mostrar error

            with tab_resumen_mes: #Configurar pestana resumen mensual
                st.subheader(f"Resumen Datos Clave - Periodo {mes_seleccionado}") #Crear encabezado seccion
                ruta_resumen_mes = f"EDA/data/resumen_estadistico_{mes_seleccionado}.csv" #Definir ruta resumen mensual
                if os.path.exists(ruta_resumen_mes): #Verificar existencia de archivo
                    try: #Manejar posibles errores
                        df_resumen_mes = pd.read_csv(ruta_resumen_mes) #Cargar resumen estadistico
                        
                        m1, m2, m3 = st.columns(3) #Crear columnas primera fila
                        m1.metric(f"Total Registros {mes_seleccionado}", f"{len(df_mes):,}") #Exhibir metrica total
                        m2.metric("Nivel Optico Promedio", f"{df_mes['RX_AVG'].mean():.2f} dBm") #Exhibir metrica potencia
                        m3.metric("Dias Atencion Promedio", f"{df_mes['DIAS_ATENCION'].mean():.1f}") #Exhibir metrica dias
                        
                        st.markdown("<br>", unsafe_allow_html=True) #Agregar salto de linea para diseno
                        
                        st.metric("Top Paquete", f"{df_resumen_mes.loc[df_resumen_mes['Columna'] == 'PAQUETE_x', 'Top_Valor'].iloc[0]}", f"{df_resumen_mes.loc[df_resumen_mes['Columna'] == 'PAQUETE_x', 'Valores_Unicos'].iloc[0]} UNICOS") #Exhibir metrica paquete
                        st.metric("Top Motivo", f"{df_resumen_mes.loc[df_resumen_mes['Columna'] == 'MOTIVO_PEDIDO', 'Top_Valor'].iloc[0]}", f"{df_resumen_mes.loc[df_resumen_mes['Columna'] == 'MOTIVO_PEDIDO', 'Valores_Unicos'].iloc[0]} UNICOS") #Exhibir metrica motivo
                        st.metric("Top Detalle", f"{df_resumen_mes.loc[df_resumen_mes['Columna'] == 'DETALLE_PEDIDO1', 'Top_Valor'].iloc[0]}", f"{df_resumen_mes.loc[df_resumen_mes['Columna'] == 'DETALLE_PEDIDO1', 'Valores_Unicos'].iloc[0]} UNICOS") #Exhibir metrica detalle
                        st.metric("Top Modelo ONT", f"{df_resumen_mes.loc[df_resumen_mes['Columna'] == 'ONT_MODEL', 'Top_Valor'].iloc[0]}", f"{df_resumen_mes.loc[df_resumen_mes['Columna'] == 'ONT_MODEL', 'Valores_Unicos'].iloc[0]} UNICOS") #Exhibir metrica modelo
                        
                        st.markdown("---") #Agregar separador visual
                        col_left, col_right = st.columns([1, 1]) #Crear columnas tablas
                        with col_left: #Configurar columna izquierda
                            st.subheader("Vista Previa de Datos Mensuales") #Crear subencabezado datos
                            st.dataframe(df_mes.head(10), use_container_width=True) #Mostrar dataframe resumido
                        with col_right: #Configurar columna derecha
                            st.subheader("Descripcion Estadistica") #Crear subencabezado estadistica
                            st.dataframe(df_resumen_mes, use_container_width=True) #Mostrar tabla resumen completa
                    except Exception as e:
                        st.error(f"Error al cargar los datos estadisticos del mes: {e}") #Mostrar error
                else:
                    st.warning("No se encontro el archivo de resumen estadistico para este mes.") #Mostrar aviso

            with tab_eda_mes: #Configurar pestana eda mensual
                st.subheader(f"Comportamiento de las Variables Principales - Periodo {mes_seleccionado}") #Crear subencabezado
                col1, col2 = st.columns(2) #Crear columnas graficos
                ruta_graficos = f"EDA/graficos_eda_{mes_seleccionado}" #Definir carpeta base
                
                with col1: #Configurar columna uno
                    if os.path.exists(f"{ruta_graficos}/01_histograma_rx_avg_{mes_seleccionado}.png"): st.image(f"{ruta_graficos}/01_histograma_rx_avg_{mes_seleccionado}.png", caption="Distribucion de Potencia", use_column_width=True) #Exhibir histograma
                    if os.path.exists(f"{ruta_graficos}/02_barras_motivo_pedido_{mes_seleccionado}.png"): st.image(f"{ruta_graficos}/02_barras_motivo_pedido_{mes_seleccionado}.png", caption="Frecuencia de Motivos de Fallas", use_column_width=True) #Exhibir barras motivos
                    if os.path.exists(f"{ruta_graficos}/01_ont_vs_tasa_reincidencia_{mes_seleccionado}.png"): st.image(f"{ruta_graficos}/01_ont_vs_tasa_reincidencia_{mes_seleccionado}.png", caption="Tasa de Reincidencia por Modelo de ONT", use_column_width=True) #Exhibir grafico ont
                with col2: #Configurar columna dos
                    if os.path.exists(f"{ruta_graficos}/03_churn_vs_potencia_{mes_seleccionado}.png"): st.image(f"{ruta_graficos}/03_churn_vs_potencia_{mes_seleccionado}.png", caption="Relacion Nivel Optico y Desercion", use_column_width=True) #Exhibir dispersion churn
                    if os.path.exists(f"{ruta_graficos}/03_donut_ont_model_{mes_seleccionado}.png"): st.image(f"{ruta_graficos}/03_donut_ont_model_{mes_seleccionado}.png", caption="Distribucion de modelos ONTs", use_column_width=True) #Exhibir grafico dona
                    if os.path.exists(f"{ruta_graficos}/02_zona_vs_tiempo_{mes_seleccionado}.png"): st.image(f"{ruta_graficos}/02_zona_vs_tiempo_{mes_seleccionado}.png", caption="Top Zonas con Mayor Demora", use_column_width=True) #Exhibir grafico zona

        else: 
            st.warning("No se encontraron predicciones mensuales en el Datalake. Ejecuta el pipeline.") #Mostrar aviso

    elif menu_principal == "Analisis Historico y Modelo 2025": #Validar seccion historico
        st.header("Analisis Historico y Entrenamiento del Modelo Año 2025") #Crear encabezado seccion
        
        tab_modelado, tab_resumen, tab_eda = st.tabs(["Desempeno del Modelo", "Resumen Ejecutivo", "Exploración de Datos"]) #Crear pestanas
        
        with tab_modelado: #Configurar pestana modelado
            st.subheader("Principales Hallazgos: Influencia de Variables en el Riesgo de Cancelacion") #Crear subencabezado
            st.image("MODELADO/graficos_modelado/03_shap_xgboost.png", caption="Interpretacion de impacto mediante valores SHAP", use_column_width=True) #Exhibir grafico shap 2025
            st.info("El grafico superior identifica los disparadores criticos del abandono de clientes.") #Mostrar nota informativa
            
            st.markdown("---") #Agregar separador visual
            st.subheader("Evaluacion y Desempeno del Modelo Campeon") #Crear subencabezado
            col_roc, col_mat = st.columns(2) #Crear columnas desempeno
            with col_roc: #Configurar columna roc
                st.image("MODELADO/graficos_modelado/02_curva_roc_combinada.png", caption="Comparativa de Capacidad Predictiva (Curva ROC)", use_column_width=True) # Exhibir curva roc
            with col_mat: #Configurar columna matriz
                st.image("MODELADO/graficos_modelado/01_matrices_confusion_comparativa.png", caption="Comparativa de Matrices de Confusion", use_column_width=True) # Exhibir matrices comparativas

        with tab_resumen: #Configurar pestana resumen
            st.subheader("Resumen Datos Clave") #Crear encabezado seccion
            try: #Manejar posibles errores
                df_churn = pd.read_parquet(RUTA_MODELADO) #Cargar datos modelado
                df_resumen = pd.read_csv(RUTA_RESUMEN_CSV) #Cargar resumen estadistico
                
                m1, m2, m3 = st.columns(3) #Crear columnas primera fila
                m1.metric("Total Registros 2025", f"{len(df_churn):,}") #Exhibir metrica total
                m2.metric("Nivel Optico Promedio", f"{df_churn['RX_AVG_PROMEDIO'].mean():.2f} dBm") #Exhibir metrica potencia
                m3.metric("Dias Atencion Promedio", f"{df_churn['DIAS_ATENCION_PROMEDIO'].mean():.1f}") #Exhibir metrica dias
                
                st.markdown("<br>", unsafe_allow_html=True) #Agregar salto de linea para diseno
                
                st.metric("Top Paquete", f"{df_resumen.loc[df_resumen['Columna'] == 'PAQUETE_x', 'Top_Valor'].iloc[0]}", f"{df_resumen.loc[df_resumen['Columna'] == 'PAQUETE_x', 'Valores_Unicos'].iloc[0]} UNICOS") #Exhibir metrica paquete
                st.metric("Top Motivo", f"{df_resumen.loc[df_resumen['Columna'] == 'MOTIVO_PEDIDO', 'Top_Valor'].iloc[0]}", f"{df_resumen.loc[df_resumen['Columna'] == 'MOTIVO_PEDIDO', 'Valores_Unicos'].iloc[0]} UNICOS") #Exhibir metrica motivo
                st.metric("Top Detalle", f"{df_resumen.loc[df_resumen['Columna'] == 'DETALLE_PEDIDO1', 'Top_Valor'].iloc[0]}", f"{df_resumen.loc[df_resumen['Columna'] == 'DETALLE_PEDIDO1', 'Valores_Unicos'].iloc[0]} UNICOS") #Exhibir metrica detalle
                st.metric("Top Modelo ONT", f"{df_resumen.loc[df_resumen['Columna'] == 'ONT_MODEL', 'Top_Valor'].iloc[0]}", f"{df_resumen.loc[df_resumen['Columna'] == 'ONT_MODEL', 'Valores_Unicos'].iloc[0]} UNICOS") #Exhibir metrica modelo
                
                st.markdown("---") #Agregar separador visual
                col_left, col_right = st.columns([1, 1]) #Crear columnas tablas
                with col_left: #Configurar columna izquierda
                    st.subheader("Vista Previa de Datos Preparados") #Crear subencabezado datos
                    st.dataframe(df_churn.head(10), use_container_width=True) #Mostrar dataframe resumido
                with col_right: #Configurar columna derecha
                    st.subheader("Descripcion Estadistica Base") #Crear subencabezado estadistica
                    st.dataframe(df_resumen, use_container_width=True) #Mostrar tabla resumen completa
            except Exception as e:
                st.error(f"Error al cargar los datos historicos: {e}") #Mostrar error
                
        with tab_eda: #Configurar pestana eda
            st.subheader("Comportamiento de las Variables Principales") #Crear subencabezado
            col1, col2 = st.columns(2) #Crear columnas graficos
            with col1: #Configurar columna uno
                st.image("EDA/graficos_eda/01_histograma_rx_avg.png", caption="Distribucion de Potencia", use_column_width=True) #Exhibir histograma
                st.image("EDA/graficos_eda/02_barras_motivo_pedido.png", caption="Frecuencia de Motivos de Fallas", use_column_width=True) #Exhibir barras motivos
                st.image("EDA/graficos_eda/01_ont_vs_tasa_reincidencia.png", caption="Tasa de Reincidencia por Modelo de ONT", use_column_width=True) #Exhibir grafico ont reincidencia 
            with col2: #Configurar columna dos
                st.image("EDA/graficos_eda/03_churn_vs_potencia.png", caption="Relacion Nivel Optico y Desercion", use_column_width=True) #Exhibir dispersion churn
                st.image("EDA/graficos_eda/03_donut_ont_model.png", caption="Distribucion de modelos ONTs", use_column_width=True) #Exhibir grafico dona
                st.image("EDA/graficos_eda/02_zona_vs_tiempo.png", caption="Top Zonas con Mayor Demora (SLA)", use_column_width=True) #Exhibir grafico zona