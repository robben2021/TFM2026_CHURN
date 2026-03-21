import streamlit as st #Importar libreria principal para la interfaz grafica
import pandas as pd #Importar libreria pandas para manejo de datos tabulares
import os #Importar modulo del sistema para rutas y directorios
import glob #Importar modulo para busqueda de archivos mediante patrones
from streamlit_option_menu import option_menu #Importar libreria para el menu lateral moderno
import datetime #Importar modulo para el manejo de fechas
import plotly.express as px #Importar libreria plotly para graficos interactivos
import base64 # Importación necesaria para el truco de inyección de imágenes

st.set_page_config(
    page_title="Predicción de la Deserción de Abonados 2026 CVR-MORELIA", 
    page_icon="DASHBOARD/churn_tele.png",
    layout="wide"
) #Establecer configuracion global de la pagina web

#Aplicar metadatos de fuente y estilos css globales
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@100..900&display=swap');      
        html, body, [class*="css"], [class*="st-"], * {
            font-family: 'Inter', sans-serif !important;
        }
        
        .block-container {
            padding-top: 1rem !important;
        }

        /*Tunear las pestanas centrales*/
        button[data-baseweb="tab"] {
            padding: 0.5rem 1rem !important; 
        }
        button[data-baseweb="tab"]:not(:last-child) {
            border-right: 2px solid rgba(128, 128, 128, 0.3) !important; 
            border-radius: 0px !important; 
        }
        button[data-baseweb="tab"] * {
            font-size: 24px !important; 
            font-weight: 700 !important;
            transition: color 0.3s ease !important; 
        }
        button[data-baseweb="tab"]:hover * {
            color: #10b981 !important; 
        }
        div[data-baseweb="tab-highlight"] {
            background-color: #0ea5e9 !important; 
        }
        button[data-baseweb="tab"][aria-selected="true"] * {
            color: #0ea5e9 !important; 
        }

        /*Crear tarjetas corporativas*/
        [data-testid="stMetric"] {
            background-color: rgba(14, 165, 233, 0.05) !important; 
            border-left: 6px solid #0ea5e9 !important; 
            padding: 10px 15px !important; 
            border-radius: 8px !important; 
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2) !important; 
        }
        [data-testid="stMetricLabel"] {
            font-size: 15px !important;
            font-weight: 600 !important;
            margin-bottom: 4px !important; 
        }
        [data-testid="stMetricValue"] {
            font-size: 26px !important; 
            color: #0ea5e9 !important; 
            font-weight: 700 !important; 
            line-height: 1.2 !important; 
            margin-bottom: 4px !important; 
        }
        [data-testid="stMetricDelta"] {
            margin-top: 5px !important; 
        }

        /*Crear separadores sutiles corporativos*/
        hr {
            margin: 15px 0px !important;
            border: 0 !important;
            border-top: 1px solid rgba(128, 128, 128, 0.3) !important;
        }
    </style>
    <title>Predicción de la Deserción de Abonados 2026 CVR-MORELIA</title>
    <meta name="author" content="Rubén Lara Bárcenas">
""", unsafe_allow_html=True) #Inyectar codigo html y css en la aplicacion


def acceso(): #Definir funcion para control de acceso mediante contrasena
    def password_entered(): #Definir funcion interna para validar la clave ingresada
        if st.session_state["password"] == st.secrets["password"]: #Comparar clave ingresada con los secretos de streamlit
            st.session_state["password_correct"] = True #Establecer bandera de acceso exitoso
            del st.session_state["password"] #Borrar contrasena de la memoria por seguridad
        else: #Ejecutar bloque si la contrasena es incorrecta
            st.session_state["password_correct"] = False #Establecer bandera de acceso denegado

    if "password_correct" not in st.session_state: #Verificar si es la primera vez que el usuario ingresa
        st.text_input("Por favor, ingresa la clave de acceso al Dashboard:", type="password", on_change=password_entered, key="password") #Solicitar clave de acceso inicial
        return False #Retornar falso para detener la ejecucion
    elif not st.session_state["password_correct"]: #Verificar si el usuario fallo el intento
        st.text_input("Por favor, ingresa la clave de acceso al Dashboard:", type="password", on_change=password_entered, key="password") #Solicitar clave de acceso nuevamente
        st.error("Clave incorrecta. Inténtalo de nuevo.") #Mostrar mensaje de error por clave equivocada
        return False #Retornar falso para mantener bloqueada la aplicacion
    else: #Ejecutar bloque cuando la validacion es correcta
        return True #Retornar verdadero para liberar la aplicacion


def formatear_mes_anio(codigo_aamm): #Definir funcion para convertir codigo de mes a formato legible
    meses = {"01":"ENERO", "02":"FEBRERO", "03":"MARZO", "04":"ABRIL", "05":"MAYO", "06":"JUNIO", "07":"JULIO", "08":"AGOSTO", "09":"SEPTIEMBRE", "10":"OCTUBRE", "11":"NOVIEMBRE", "12":"DICIEMBRE"} #Crear diccionario de traduccion de meses
    anio = "20" + codigo_aamm[:2] #Extraer y formatear el ano del codigo
    mes = meses.get(codigo_aamm[2:], "") #Extraer y traducir el mes del codigo
    return f"{mes} {anio}" #Retornar la cadena de texto combinada amigable

def crear_lista_detallada(df): #Definir funcion para generar cadenas formateadas para listas desplegables
    if df.empty: #Verificar si el dataframe recibido no tiene datos
        return ["Sin alertas"] #Retornar opcion unica indicando ausencia de alertas
    lista = ["Ver contratos..."] #Inicializar lista con opcion por defecto para el selector
    for _, row in df.iterrows(): #Iterar sobre cada fila del dataframe filtrado
        contrato = str(row.get('CONTRATO', 'N/D')).replace('nan', 'N/D') #Limpiar valores nulos en numero de contrato
        zona = str(row.get('ZONA', 'N/D')).replace('nan', 'N/D') #Limpiar valores nulos en el campo zona
        ont = str(row.get('ONT_MODEL', 'N/D')).replace('nan', 'N/D').replace('None', 'N/D') #Limpiar valores nulos en el modelo del equipo
        
        rx_val = row.get('RX_AVG') #Extraer valor de nivel optico
        if pd.isna(rx_val): #Validar si la potencia es un valor nulo
            rx = "N/D" #Asignar texto de no disponible
        else: #Ejecutar bloque si existe lectura de potencia
            try: #Iniciar manejo de posible error de conversion a flotante
                rx = f"{float(rx_val):.2f} dBm" #Convertir a numero y redondear a dos decimales
            except: #Capturar error si el dato es texto erroneo
                rx = "N/D" #Asignar texto de no disponible por error
                
        lista.append(f"{contrato} | Z: {zona} | ONT: {ont} | Rx: {rx}") #Concatenar variables con formato de tabla y agregar a la lista
    return lista #Retornar lista completa de opciones

if "buscar_contrato" not in st.session_state: #Comprobar si existe la variable global del buscador
    st.session_state.buscar_contrato = "" #Inicializar variable global vacia

def actualizar_desde_abandono(): #Definir funcion para sincronizar lista de abandono con buscador
    val = st.session_state.sb_abandono #Leer valor seleccionado en el dropdown de abandono
    if val and val not in ["Ver contratos...", "Sin alertas"]: #Validar que no sea una opcion de relleno
        st.session_state.buscar_contrato = val.split(" | ")[0].strip() #Extraer unicamente el numero de contrato y asignarlo al buscador

def actualizar_desde_riesgo(): #Definir funcion para sincronizar lista de riesgo con buscador
    val = st.session_state.sb_riesgo #Leer valor seleccionado en el dropdown de riesgo
    if val and val not in ["Ver contratos...", "Sin alertas"]: #Validar que no sea una opcion general
        st.session_state.buscar_contrato = val.split(" | ")[0].strip() #Extraer y asignar el contrato a la variable global

def actualizar_desde_texto(): #Definir funcion para actualizar variable desde caja de texto
    st.session_state.buscar_contrato = st.session_state.txt_buscar #Sobrescribir contrato con la entrada manual del usuario


if True: #Reemplazar temporalmente validacion para desarrollo sin login
    RUTA_GOLD = "ETL/datalake/gold/clean/dataset_master_gold.parquet" #Definir constante con la ruta del conjunto maestro
    RUTA_MODELADO = "MODELADO/data/dataset_modelado_churn.parquet" #Definir constante con la ruta de datos de modelado
    RUTA_RESUMEN_CSV = "EDA/data/resumen_estadistico_completo.csv" #Definir constante con la ruta del resumen base

    st.title("Predicción de la Deserción de Abonados 2026 CVR-MORELIA") #Mostrar el titulo principal de la aplicacion

    with st.sidebar: #Abrir contexto para dibujar en el panel lateral
        menu_principal = option_menu(
            menu_title="Navegación", 
            options=["Predicciones Mensuales 2026", "Análisis Histórico y Modelo 2025", "Actualizar Datos"], 
            icons=["graph-up-arrow", "database", "arrow-repeat"], 
            menu_icon="cast", 
            default_index=0, #Definir indice de seleccion por defecto al inicio
            key="menu_key", #Asignar llave de identificacion al componente de menu
            styles={
                "container": {"padding": "0!important", "background-color": "transparent"},
                "icon": {"color": "inherit", "font-size": "24px"}, 
                "nav-link": {
                    "font-size": "18px", 
                    "text-align": "left", 
                    "margin":"5px 0px", 
                    "font-family": "'Inter', sans-serif",
                    "--hover-color": "rgba(16, 185, 129, 0.2)" #Establecer color verde suave para efecto hover
                },
                "nav-link-selected": {"background-color": "#0ea5e9", "color": "white", "font-weight": "600"}, #Regresar color azul corporativo para elemento seleccionado
            }
        ) #Construir y estilizar el menu de navegacion visual

    st.sidebar.markdown("---") #Insertar una linea horizontal divisoria en la barra lateral
    
    if menu_principal == "Actualizar Datos": #Comprobar si el usuario selecciono la opcion de recarga
        st.cache_data.clear() #Limpiar la memoria cache de streamlit para forzar lectura fresca
        st.session_state.buscar_contrato = "" #Reiniciar la caja del buscador a su estado vacio
        del st.session_state["menu_key"] #Eliminar la memoria interna del menu para resetear pestana
        st.rerun() #Forzar la recarga automatica y completa de la pagina web

    elif menu_principal == "Predicciones Mensuales 2026": #Comprobar si se activo la seccion mensual
        st.header("Monitoreo Mensual de Riesgo de Abandono (Churn) 2026 CVR-MORELIA") #Dibujar el encabezado de la seccion mensual
        
        ruta_scored = "ETL/datalake/gold/scored/" #Definir ruta local donde residen los archivos mensuales
        if os.path.exists(ruta_scored): #Verificar que la carpeta de destino realmente exista en disco
            archivos_pred = glob.glob(f"{ruta_scored}predicciones_churn_*.csv") #Generar lista de todos los archivos csv que coincidan con el patron
            meses_disp = sorted([f.split('_')[-1].replace('.csv', '') for f in archivos_pred], reverse=True) #Extraer y ordenar inversamente las etiquetas de los meses encontrados
        else: #Ejecutar bloque alternativo si la carpeta no existe
            meses_disp = [] #Crear una lista completamente vacia de meses
            
        if meses_disp: #Validar si la lista de meses contiene elementos viables
            mes_amigable = st.selectbox(
                "Selecciona el período a analizar:", 
                options=meses_disp, 
                format_func=formatear_mes_anio 
            ) #Desplegar selector de meses aplicando la funcion de formato estetico
            
            df_mes = pd.read_csv(f"{ruta_scored}predicciones_churn_{mes_amigable}.csv") #Leer el dataframe correspondiente al mes elegido en la interfaz
            
            tab_predicciones, tab_resumen_mes, tab_eda_mes = st.tabs(["Predicciones y Riesgo", "Resumen Ejecutivo", "Exploración de Datos"]) #Construir las tres pestanas de navegacion interna
            
            with tab_predicciones: #Abrir contexto para la primera pestana predictiva
                if 'PREDICCION_CLASE' in df_mes.columns: #Comprobar si el modelo genero la columna binaria de clase
                    df_riesgo = df_mes[df_mes['PREDICCION_ABONADO'] == 1] #Filtrar subconjunto de clientes marcados como fuga inminente
                else: #Proceder si no existe la columna de clase absoluta
                    df_riesgo = df_mes[df_mes['PROBABILIDAD_RIESGO'] >= 0.5] #Filtrar clientes usando el umbral de probabilidad probabilistica base
                    
                df_riesgo_alto = df_mes[df_mes['PROBABILIDAD_RIESGO'] >= 0.15] #Filtrar subconjunto secundario con clientes en umbral precautorio

                k1, k2, k3 = st.columns(3) #Dividir el lienzo en tres columnas equitativas
                
                with k1: #Trabajar dentro de la primera columna
                    st.metric("Total Clientes Evaluados", f"{len(df_mes):,}") #Insertar tarjeta con el recuento total de clientes procesados
                    
                with k2: #Trabajar dentro de la segunda columna
                    st.metric("Clientes Predicción de Abandono", f"{len(df_riesgo):,}") #Insertar tarjeta con recuento de abandonos detectados
                    lista_abandono = crear_lista_detallada(df_riesgo) #Procesar opciones textuales con datos de los clientes en abandono
                    st.selectbox("Contratos en Abandono:", lista_abandono, key="sb_abandono", on_change=actualizar_desde_abandono, label_visibility="collapsed") #Pintar dropdown funcional ocultando su etiqueta superior
                    
                with k3: #Trabajar dentro de la tercera columna
                    st.metric("Clientes en Riesgo", f"{len(df_riesgo_alto):,}") #Insertar tarjeta con recuento de alerta amarilla
                    lista_riesgo_alto = crear_lista_detallada(df_riesgo_alto) #Procesar opciones textuales para riesgo moderado
                    st.selectbox("Contratos en Riesgo:", lista_riesgo_alto, key="sb_riesgo", on_change=actualizar_desde_riesgo, label_visibility="collapsed") #Pintar dropdown interactivo para la tercera tarjeta
                
                st.markdown("---") #Pintar linea separadora visual
                
                col_grafico, col_buscador = st.columns([1.5, 1]) #Dividir espacio inferior en dos columnas asimetricas
                
                with col_grafico: #Abrir bloque de la columna izquierda para graficos
                    st.subheader("Indicadores de Riesgo del Mes") #Poner titulo del cuadrante de graficos
                    ruta_shap = f"MODELADO/graficos_modelado_{mes_amigable}/01_shap_summary_{mes_amigable}.png" #Generar ruta dinamica para buscar el grafico del mes
                    if os.path.exists(ruta_shap): #Verificar disponibilidad de la imagen generada
                        st.markdown("<br>", unsafe_allow_html=True) #Anadir separador superior estandar
                        st.image(ruta_shap, use_column_width=True) #Proyectar imagen shap adaptandose al ancho contenedor
                        st.markdown("---") #Anadir separador inferior sutil
                    else: #Actuar en caso de falta de imagen local
                        st.warning("El gráfico SHAP para este mes aún no ha sido generado.") #Emitir advertencia visual de ausencia
                        
                with col_buscador: #Abrir bloque derecho destinado al modulo de busqueda
                    st.subheader("Buscar Contrato") #Imprimir titulo del buscador
                    st.info("Selecciona un contrato en las listas superiores o ingrésalo manualmente.") #Desplegar tooltip con instrucciones
                    contrato_input = st.text_input("Ingresa el Número de Contrato:", value=st.session_state.buscar_contrato, key="txt_buscar", on_change=actualizar_desde_texto) #Crear campo de entrada conectandolo al callback global
                    
                    if st.session_state.buscar_contrato: #Averiguar si existe un valor a buscar actualmente
                        resultado = df_mes[df_mes['CONTRATO'].astype(str) == st.session_state.buscar_contrato] #Ejecutar consulta en dataframe por coincidencia de contrato
                        if not resultado.empty: #Asegurar que la consulta devolvio resultados
                            score_cliente = resultado['PROBABILIDAD_RIESGO'].values[0] * 100 #Obtener la probabilidad especifica y escalarla a base cien
                            st.metric(label="Probabilidad de Abandono", value=f"{score_cliente:.2f} %") #Exhibir el puntaje de riesgo del cliente con tarjeta
                        else: #Proceder si el numero tipeado no se encontro
                            st.error("Contrato no encontrado en este período.") #Generar banner de error al usuario

            with tab_resumen_mes: #Entrar en contexto de la segunda pestana
                st.subheader(f"Resumen Datos Clave - Período {mes_amigable}") #Renderizar subtitulo con el periodo actual
                ruta_resumen_mes = f"EDA/data/resumen_estadistico_{mes_amigable}.csv" #Componer la ruta de datos estadisticos correspondientes
                if os.path.exists(ruta_resumen_mes): #Confirmar integridad del archivo origen
                    try: #Proteger lectura de datos propensa a fallos
                        df_resumen_mes = pd.read_csv(ruta_resumen_mes) #Extraer informacion del csv a pandas
                        
                        m1, m2, m3 = st.columns(3) #Generar tres divisiones para indicadores secundarios
                        m1.metric(f"Total Registros {mes_amigable}", f"{len(df_mes):,}") #Plasmar cantidad de registros del archivo
                        m2.metric("Nivel Óptico Promedio", f"{df_mes['RX_AVG'].mean():.2f} dBm") #Plasmar promedio del nivel de senal del mes
                        m3.metric("Días Atención Promedio", f"{df_mes['DIAS_ATENCION'].mean():.1f}") #Plasmar promedio de dias tardados
                        
                        st.markdown("<br>", unsafe_allow_html=True) #Forzar salto de linea usando elemento de hipertexto
                        
                        st.metric("Top Paquete", f"{df_resumen_mes.loc[df_resumen_mes['Columna'] == 'PAQUETE_x', 'Top_Valor'].iloc[0]}", f"{df_resumen_mes.loc[df_resumen_mes['Columna'] == 'PAQUETE_x', 'Valores_Unicos'].iloc[0]} UNICOS") #Pintar bloque descriptivo del paquete mas frecuente
                        st.metric("Top Motivo", f"{df_resumen_mes.loc[df_resumen_mes['Columna'] == 'MOTIVO_PEDIDO', 'Top_Valor'].iloc[0]}", f"{df_resumen_mes.loc[df_resumen_mes['Columna'] == 'MOTIVO_PEDIDO', 'Valores_Unicos'].iloc[0]} UNICOS") #Pintar bloque del motivo de queja mas comun
                        st.metric("Top Detalle", f"{df_resumen_mes.loc[df_resumen_mes['Columna'] == 'DETALLE_PEDIDO1', 'Top_Valor'].iloc[0]}", f"{df_resumen_mes.loc[df_resumen_mes['Columna'] == 'DETALLE_PEDIDO1', 'Valores_Unicos'].iloc[0]} UNICOS") #Pintar bloque del tipo de dano lider
                        st.metric("Top Modelo ONT", f"{df_resumen_mes.loc[df_resumen_mes['Columna'] == 'ONT_MODEL', 'Top_Valor'].iloc[0]}", f"{df_resumen_mes.loc[df_resumen_mes['Columna'] == 'ONT_MODEL', 'Valores_Unicos'].iloc[0]} UNICOS") #Pintar bloque del aparato optico predeterminado
                        
                        st.markdown("---") #Romper layout con linea
                        col_left, col_right = st.columns([1, 1]) #Hacer dos columnas pares para previsualizacion
                        
                        with col_left: #Controlar zona izquierda de previsualizacion
                            st.subheader("Vista Previa de Datos Mensuales") #Escribir titulo de tabla izquierda
                            mostrar_todo_mes = st.toggle("Mostrar todas las columnas", key="tog_mes") #Crear interruptor para expandir columnas
                            
                            if 'PREDICCION_ABANDONO' not in df_mes.columns and 'PROBABILIDAD_RIESGO' in df_mes.columns: #Asegurar existencia de columna predictiva final
                                df_mes['PREDICCION_ABANDONO'] = (df_mes['PROBABILIDAD_RIESGO'] >= 0.5).astype(int) #Generar clasificacion binaria en caliente
                                
                            cols_deseadas_mes = ['CONTRATO', 'ZONA', 'PAQUETE_x', 'ESTATUS_x', 'DIAS_ANTIGUEDAD', 'FECHA_PEDIDO', 'FECHA_CUMPLIMIENTO', 'MOTIVO_PEDIDO', 'DETALLE_PEDIDO1', 'ONT_MODEL', 'RX_AVG', 'PROBABILIDAD_RIESGO', 'PREDICCION_ABANDONO'] #Definir lista de columnas prioritarias incluyendo rx y prediccion
                            cols_filtradas_mes = [col for col in cols_deseadas_mes if col in df_mes.columns] #Filtrar asegurando que las columnas existan en origen
                            df_vista_mes = df_mes if mostrar_todo_mes else df_mes[cols_filtradas_mes] #Asignar vista completa o filtrada segun el interruptor
                            st.dataframe(df_vista_mes, use_container_width=True) #Integrar widget tabular expansivo
                            
                        with col_right: #Controlar zona derecha estadistica
                            st.subheader("Descripción Estadística") #Escribir titulo de tabla derecha
                            mostrar_todo_res_mes = st.toggle("Mostrar todas las columnas", key="tog_res_mes") #Crear interruptor para mostrar columnas de resumen
                            if 'Tipo_Dato' in df_resumen_mes.columns: #Verificar existencia de columna irrelevante
                                df_resumen_mes = df_resumen_mes.drop(columns=['Tipo_Dato']) #Eliminar columna de tipo de dato
                            cols_res = list(df_resumen_mes.columns) #Extraer nombres de columnas actuales
                            for c in ['Total_Valores', 'Valores_Nulos', 'Valores_Unicos']: #Iterar sobre columnas de conteos a reubicar
                                if c in cols_res: #Asegurar existencia antes de mover
                                    cols_res.remove(c) #Remover columna de su posicion original
                                    cols_res.append(c) #Insertar columna al final de la lista
                            df_resumen_mes = df_resumen_mes[cols_res] #Aplicar nuevo orden de columnas al dataframe
                            if not mostrar_todo_res_mes: #Evaluar estado del interruptor de columnas
                                df_resumen_mes = df_resumen_mes.drop(columns=[col for col in ['Valores_Nulos', 'Valores_Unicos'] if col in df_resumen_mes.columns]) #Ocultar columnas de nulos y unicos
                            st.dataframe(df_resumen_mes, use_container_width=True) #Integrar resumen detallado de pandas reordenado
                            
                    except Exception as e: #Aislar el error en variable generica
                        st.error(f"Error al cargar los datos estadísticos del mes: {e}") #Mostrar texto descriptivo del incidente de lectura
                else: #Accion por defecto ante ruta invalida
                    st.warning("No se encontró el archivo de resumen estadístico para este mes.") #Notificar que falta ejecucion previa del script

            with tab_eda_mes: #Activar pestana final de exploracion visual
                st.subheader(f"Comportamiento de las Variables Principales - Período {mes_amigable}") #Poner titular de exploracion
                
                col1, col_sep, col2 = st.columns([1, 0.02, 1]) #Fraccionar area inferior en tres columnas reduciendo grosor central
                
                with col_sep: #Configurar columna central como linea divisoria
                    st.markdown("<div style='background-color: rgba(128, 128, 128, 0.4); width: 2px; height: 1500px; margin: 0 auto;'></div>", unsafe_allow_html=True) #Dibujar linea vertical continua y solida
                
                #Construir primer grafico interactivo
                fig_hist = px.histogram(df_mes, x="RX_AVG", nbins=30, title="Distribución de Potencia Óptica (dBm)", color_discrete_sequence=['#0ea5e9']) #Generar figura plotly tipo histograma
                fig_hist.update_layout(height=400, margin=dict(l=20, r=20, t=40, b=20)) #Estandarizar tamano estructural del grafico
                
                #Construir segundo grafico interactivo
                df_motivos = df_mes['MOTIVO_PEDIDO'].value_counts().reset_index().head(10) #Contar frecuencias de los motivos principales
                df_motivos.columns = ['Motivo', 'Frecuencia'] #Renombrar columnas del dataframe temporal
                fig_motivos = px.bar(df_motivos, x='Motivo', y='Frecuencia', title="Top 10 Motivos de Fallas", color_discrete_sequence=['#10b981']) #Generar figura plotly de barras
                fig_motivos.update_layout(height=400, margin=dict(l=20, r=20, t=40, b=20), xaxis_tickangle=-45) #Estandarizar tamano e inclinar etiquetas
                
                #Construir tercer grafico interactivo
                df_ont_riesgo = df_mes.groupby('ONT_MODEL')['PROBABILIDAD_RIESGO'].mean().reset_index().sort_values(by='PROBABILIDAD_RIESGO', ascending=False) #Agrupar nivel de riesgo promedio por modelo
                fig_ont_riesgo = px.bar(df_ont_riesgo, x='ONT_MODEL', y='PROBABILIDAD_RIESGO', title="Riesgo de Deserción Promedio por ONT", color_discrete_sequence=['#f43f5e']) #Generar figura plotly evaluando riesgo
                fig_ont_riesgo.update_layout(height=400, margin=dict(l=20, r=20, t=40, b=20)) #Estandarizar tamano de presentacion visual
                
                #Construir cuarto grafico interactivo
                if 'PREDICCION_ABANDONO' not in df_mes.columns and 'PROBABILIDAD_RIESGO' in df_mes.columns: #Asegurar existencia de clasificacion binaria
                    df_mes['PREDICCION_ABANDONO'] = (df_mes['PROBABILIDAD_RIESGO'] >= 0.5).astype(int) #Generar columna binaria en caliente
                df_mes['CLASE_TEXTO'] = df_mes['PREDICCION_ABANDONO'].map({0: 'Retenido', 1: 'Abandono'}) #Asignar mapeo textual para leyenda del grafico
                fig_box = px.box(df_mes, x="CLASE_TEXTO", y="RX_AVG", color="CLASE_TEXTO", title="Nivel Óptico vs Predicción de Deserción", color_discrete_sequence=['#0ea5e9', '#f43f5e']) #Generar diagrama de cajas y bigotes
                fig_box.update_layout(height=400, margin=dict(l=20, r=20, t=40, b=20)) #Estandarizar contenedor de diagrama de cajas
                
                #Construir quinto grafico interactivo
                df_donut = df_mes['ONT_MODEL'].value_counts().reset_index() #Contar distribucion volumetrica de equipos
                df_donut.columns = ['Modelo', 'Cantidad'] #Renombrar parametros temporales
                fig_donut = px.pie(df_donut, names='Modelo', values='Cantidad', hole=0.4, title="Distribución de Modelos ONTs", color_discrete_sequence=px.colors.sequential.Teal) #Generar pastel con agujero central
                fig_donut.update_layout(height=400, margin=dict(l=20, r=20, t=40, b=20)) #Estandarizar contenedor geometrico
                
                #Construir sexto grafico interactivo
                if 'DIAS_ATENCION' in df_mes.columns: #Condicionar elaboracion a la existencia de la variable
                    df_zonas = df_mes.groupby('ZONA')['DIAS_ATENCION'].mean().reset_index().sort_values(by='DIAS_ATENCION', ascending=False).head(10) #Consolidar retraso promedio en top diez
                    fig_zonas = px.bar(df_zonas, x='ZONA', y='DIAS_ATENCION', title="Top Zonas con Mayor Demora Promedio (Días)", color_discrete_sequence=['#f59e0b']) #Renderizar diagrama de tiempo invertido
                else: #Prever escenario de columna ausente
                    fig_zonas = px.bar(title="Datos de Días de Atención No Disponibles") #Crear grafico vacio con aviso
                fig_zonas.update_layout(height=400, margin=dict(l=20, r=20, t=40, b=20)) #Estandarizar tamano final
                
                with col1: #Alojar primer lote de graficos
                    st.plotly_chart(fig_hist, use_container_width=True) #Proyectar visualizacion plotly del histograma
                    st.markdown("---") #Anadir separador horizontal sutil
                    
                    st.plotly_chart(fig_motivos, use_container_width=True) #Proyectar visualizacion plotly de fallas
                    st.markdown("---") #Anadir separador horizontal sutil
                    
                    st.plotly_chart(fig_ont_riesgo, use_container_width=True) #Proyectar visualizacion plotly de riesgo en modelos
                    st.markdown("---") #Anadir separador horizontal sutil
                    
                with col2: #Alojar segundo lote de graficos
                    st.plotly_chart(fig_box, use_container_width=True) #Proyectar visualizacion plotly relacional
                    st.markdown("---") #Anadir separador horizontal sutil
                    
                    st.plotly_chart(fig_donut, use_container_width=True) #Proyectar visualizacion plotly distribucional
                    st.markdown("---") #Anadir separador horizontal sutil
                    
                    st.plotly_chart(fig_zonas, use_container_width=True) #Proyectar visualizacion plotly de logistica
                    st.markdown("---") #Anadir separador horizontal sutil

        else: #Opcion residual si la busqueda de archivos esta vacia
            st.warning("No se encontraron predicciones mensuales en el Datalake. Ejecuta el pipeline.") #Alerta final de vacio

    elif menu_principal == "Análisis Histórico y Modelo 2025": #Validar seleccion de la macroestructura historica
        st.header("Análisis Histórico y Entrenamiento del Modelo Año 2025") #Dibujar etiqueta titular del contexto 2025
        
        tab_modelado, tab_resumen, tab_eda = st.tabs(["Desempeño del Modelo", "Resumen Ejecutivo", "Exploración de Datos"]) #Armar arreglo de pestanas globales
        
        with tab_modelado: #Activar primer espacio explicativo del modelo
            st.subheader("Principales Hallazgos: Influencia de Variables en el Riesgo de Cancelación") #Textualizar area del shap global
            st.image("MODELADO/graficos_modelado/03_shap_xgboost.png", caption="Interpretación de impacto mediante valores SHAP", use_column_width=True) #Invocar renderizado de foto del peso de caracteristicas
            st.info("El gráfico superior identifica los disparadores críticos del abandono de clientes.") #Colocar barra de informacion
            
            st.markdown("---") #Crear quiebre tematico horizontal
            st.subheader("Evaluación y Desempeño del Modelo Campeón") #Establecer titulo de metricas de validacion
            col_roc, col_mat = st.columns(2) #Picar pantalla en dos lienzos cuadrados
            with col_roc: #Usar el cuadro izquierdo
                st.image("MODELADO/graficos_modelado/02_curva_roc_combinada.png", caption="Comparativa de Capacidad Predictiva (Curva ROC)", use_column_width=True) #Pegar png con el rendimiento probabilistico global
            with col_mat: #Usar el cuadro derecho
                st.image("MODELADO/graficos_modelado/01_matrices_confusion_comparativa.png", caption="Comparativa de Matrices de Confusión", use_column_width=True) #Pegar png con matriz de verdaderos o falsos positivos

        with tab_resumen: #Ingresar al panel de lectura maestra de la data 2025
            st.subheader("Resumen Datos Clave") #Presentar titulillo
            try: #Abrir entorno a prueba de caidas por archivos corruptos
                df_churn = pd.read_parquet(RUTA_MODELADO) #Materializar el dataset enorme guardado en apache parquet
                df_resumen = pd.read_csv(RUTA_RESUMEN_CSV) #Materializar la tabla auxiliar del perfilado
                
                m1, m2, m3 = st.columns(3) #Definir tres lugares en fila
                m1.metric("Total Registros 2025", f"{len(df_churn):,}") #Estampar el volumen masivo de datos del ano
                m2.metric("Nivel Óptico Promedio", f"{df_churn['RX_AVG_PROMEDIO'].mean():.2f} dBm") #Estampar el calculo global optico
                m3.metric("Días Atención Promedio", f"{df_churn['DIAS_ATENCION_PROMEDIO'].mean():.1f}") #Estampar el lapso de servicio anual
                
                st.markdown("<br>", unsafe_allow_html=True) #Dejar espacio en blanco
                
                st.metric("Top Paquete", f"{df_resumen.loc[df_resumen['Columna'] == 'PAQUETE_x', 'Top_Valor'].iloc[0]}", f"{df_resumen.loc[df_resumen['Columna'] == 'PAQUETE_x', 'Valores_Unicos'].iloc[0]} UNICOS") #Construir metrica base leyendo paquete principal de 2025
                st.metric("Top Motivo", f"{df_resumen.loc[df_resumen['Columna'] == 'MOTIVO_PEDIDO', 'Top_Valor'].iloc[0]}", f"{df_resumen.loc[df_resumen['Columna'] == 'MOTIVO_PEDIDO', 'Valores_Unicos'].iloc[0]} UNICOS") #Construir metrica leyendo queja historica preeminente
                st.metric("Top Detalle", f"{df_resumen.loc[df_resumen['Columna'] == 'DETALLE_PEDIDO1', 'Top_Valor'].iloc[0]}", f"{df_resumen.loc[df_resumen['Columna'] == 'DETALLE_PEDIDO1', 'Valores_Unicos'].iloc[0]} UNICOS") #Construir metrica apuntando al origen del problema anual
                st.metric("Top Modelo ONT", f"{df_resumen.loc[df_resumen['Columna'] == 'ONT_MODEL', 'Top_Valor'].iloc[0]}", f"{df_resumen.loc[df_resumen['Columna'] == 'ONT_MODEL', 'Valores_Unicos'].iloc[0]} UNICOS") #Construir metrica senalando el equipo del que mas dependio ceeveerre
                
                st.markdown("---") #Imprimir barra delgada grisacea
                col_left, col_right = st.columns([1, 1]) #Partir zona baja a mitades
                
                with col_left: #Escribir bloque para datos crudos historicos
                    st.subheader("Vista Previa de Datos Preparados") #Poner caption de encabezado
                    st.dataframe(df_churn, use_container_width=True) #Mandar volcado de datos con widget oficial sin ocultar columnas
                    
                with col_right: #Escribir bloque para reporte de info estadistica historica
                    st.subheader("Descripción Estadística Base") #Poner rotulo correspondiente
                    if 'Tipo_Dato' in df_resumen.columns: #Verificar si el campo tipo de dato esta presente
                        df_resumen = df_resumen.drop(columns=['Tipo_Dato']) #Excluir el campo de tipos de dato del reporte
                    cols_res_hist = list(df_resumen.columns) #Listar distribucion actual de las columnas
                    for c in ['Total_Valores', 'Valores_Nulos', 'Valores_Unicos']: #Procesar cada variable de resumen matematico
                        if c in cols_res_hist: #Validar su localizacion real
                            cols_res_hist.remove(c) #Sacar de en medio para aislar
                            cols_res_hist.append(c) #Insertar al final de la cola formativa
                    df_resumen = df_resumen[cols_res_hist] #Consolidar dataframe base reestructurado
                    st.dataframe(df_resumen, use_container_width=True) #Mandar renderizado de reporte base completo sin interruptor
                    
            except Exception as e: #Lidiar con excepciones genericas guardando el log
                st.error(f"Error al cargar los datos históricos: {e}") #Notificar visualmente el fracaso al intentar leer la matriz
                
        with tab_eda: #Operar en pestana historica de graficos generales
            st.subheader("Comportamiento de las Variables Principales") #Declarar seccion inicial del eda
            
            #Inyectar css personalizado para celdas y titulos interactivos
            st.markdown("""
                <style>
                    .chart-wrapper {
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        margin-bottom: 5px;
                    }
                    .chart-title {
                        font-size: 18px;
                        font-weight: 600;
                        margin-bottom: 10px;
                        text-align: center;
                    }
                    /*Clase para la celda contenedora del grafico*/
                    .chart-grid-cell {
                        display: flex;
                        justify-content: center; 
                        align-items: center; 
                        width: 100%;
                        height: 420px; 
                        border: 1px solid rgba(128, 128, 128, 0.2); 
                        border-radius: 10px;
                        background-color: rgba(128, 128, 128, 0.05); 
                        padding: 10px;
                        overflow: hidden; 
                    }
                    /*Estilos para ajustar imagen al contenedor*/
                    .chart-grid-cell img {
                        max-width: 100%;
                        max-height: 100%;
                        object-fit: contain; 
                        border-radius: 5px;
                    }
                </style>
            """, unsafe_allow_html=True) #Inyectar estilos visuales
            
            def render_centered_image_html(image_path, title): #Definir funcion para empaquetar imagen y titulo
                try: #Controlar error de busqueda de archivo
                    with open(image_path, "rb") as image_file: #Abrir imagen en modo binario
                        encoded_string = base64.b64encode(image_file.read()).decode() #Codificar imagen a texto base64
                    return f'<div class="chart-wrapper"><div class="chart-title">{title}</div><div class="chart-grid-cell"><img src="data:image/png;base64,{encoded_string}" alt="{title}"></div></div>' #Retornar estructura html completa con titulo
                except FileNotFoundError: #Capturar fallo de busqueda
                    return f'<div class="chart-wrapper"><div class="chart-title">{title}</div><div class="chart-grid-cell" style="color: rgba(128, 128, 128, 0.5);">Imagen no encontrada en ruta: {image_path}</div></div>' #Retornar marcador de error visual
            
            col1, col_sep, col2 = st.columns([1, 0.02, 1]) #Fraccionar area inferior en tres columnas reduciendo grosor central
            
            with col_sep: #Configurar columna central como linea divisoria
                st.markdown("<div style='background-color: rgba(128, 128, 128, 0.4); width: 2px; height: 1500px; margin: 0 auto;'></div>", unsafe_allow_html=True) #Dibujar linea vertical continua adaptada a nuevas celdas
            
            with col1: #Alojar familia izquierda de visuales estaticos
                st.markdown(render_centered_image_html("EDA/graficos_eda/01_histograma_rx_avg.png", "Distribución de Nivel Óptico (dBm)"), unsafe_allow_html=True) #Proyectar grafico centrado con titulo incrustado
                st.markdown("---") #Anadir separador horizontal sutil
                
                st.markdown(render_centered_image_html("EDA/graficos_eda/02_barras_motivo_pedido.png", "Frecuencia de Motivos de Fallas"), unsafe_allow_html=True) #Proyectar grafico centrado con titulo incrustado
                st.markdown("---") #Anadir separador horizontal sutil
                
                st.markdown(render_centered_image_html("EDA/graficos_eda/01_ont_vs_tasa_reincidencia.png", "Tasa de Reincidencia por Modelo de ONT"), unsafe_allow_html=True) #Proyectar grafico centrado con titulo incrustado
                st.markdown("---") #Anadir separador horizontal sutil

            with col2: #Alojar bloque visual restante estatico
                st.markdown(render_centered_image_html("EDA/graficos_eda/03_churn_vs_potencia.png", "Relacion Nivel Óptico y Deserción"), unsafe_allow_html=True) #Proyectar grafico centrado con titulo incrustado
                st.markdown("---") #Anadir separador horizontal sutil
                
                st.markdown(render_centered_image_html("EDA/graficos_eda/03_donut_ont_model.png", "Distribución de Modelos ONTs"), unsafe_allow_html=True) #Proyectar grafico centrado con titulo incrustado
                st.markdown("---") #Anadir separador horizontal sutil
                
                st.markdown(render_centered_image_html("EDA/graficos_eda/02_zona_vs_tiempo.png", "Top Zonas con Mayor Demora Promedio (SLA)"), unsafe_allow_html=True) #Proyectar grafico centrado con titulo incrustado
                st.markdown("---") #Anadir separador horizontal sutil