import streamlit as st #Importar libreria principal para la interfaz grafica
import pandas as pd #Importar libreria pandas para manejo de datos tabulares
import os #Importar modulo del sistema para rutas y directorios
import glob #Importar modulo para busqueda de archivos mediante patrones
import datetime #Importar modulo para el manejo de fechas
import plotly.express as px #Importar libreria plotly para graficos interactivos
import plotly.graph_objects as go #Importar modulo de objetos graficos para superponer lineas
import numpy as np #Importar libreria matematica para arreglos numericos
from streamlit_option_menu import option_menu #Importar libreria para el menu lateral moderno
from scipy.stats import gaussian_kde #Importar funcion estadistica para calcular curva de tendencia
from PIL import Image, ImageOps #Importar libreria de procesamiento de imagenes para estandarizacion

st.set_page_config(
    page_title="Predicción de la Deserción de Abonados 2026 CVR-MORELIA", 
    page_icon="DASHBOARD/churn_tele.png",
    layout="wide"
) #Establecer configuracion global de la pagina web

def adjuntar_css_externo(ruta_archivo): #Definir funcion para cargar estilos externos
    with open(ruta_archivo) as f: #Abrir archivo css de forma segura
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True) #Inyectar contenido leido al html de la pagina

adjuntar_css_externo("estilos.css") #Llamar funcion para estilizar interfaz

@st.cache_data #Habilitar cache de memoria para acelerar lecturas posteriores
def cargar_datos_historicos(ruta_parquet, ruta_csv): #Definir funcion para leer datos masivos
    df_modelo = pd.read_parquet(ruta_parquet) #Cargar matriz historica principal
    df_stats = pd.read_csv(ruta_csv) #Cargar tabla de estadisticas
    return df_modelo, df_stats #Devolver ambos dataframes

def acceso(): #Definir funcion para control de acceso mediante contrasena
    def password_entered(): #Definir funcion interna para validar la clave ingresada
        if st.session_state["password"] == st.secrets["password"]: #Comparar clave ingresada 
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

def crear_lista_detallada(df): #Definir funcion para generar cadenas para listas desplegables
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
    val = st.session_state.get("sb_abandono") #Leer valor seleccionado de forma segura
    if val and val not in ["Ver contratos...", "Sin alertas"]: #Validar que no sea una opcion de relleno
        st.session_state.buscar_contrato = str(val).split(" | ")[0].strip() #Extraer unicamente el numero de contrato y asignarlo al buscador

def actualizar_desde_riesgo(): #Definir funcion para sincronizar lista de riesgo con buscador
    val = st.session_state.get("sb_riesgo") #Leer valor seleccionado de forma segura
    if val and val not in ["Ver contratos...", "Sin alertas"]: #Validar que no sea una opcion general
        st.session_state.buscar_contrato = str(val).split(" | ")[0].strip() #Extraer y asignar el contrato a la variable global

def actualizar_desde_texto(): #Definir funcion para actualizar variable desde caja de texto
    val = st.session_state.get("txt_buscar") #Leer texto ingresado de forma segura
    if val: #Validar que exista texto
        st.session_state.buscar_contrato = str(val).strip() #Sobrescribir contrato con la entrada manual del usuario


if True: #Reemplazar temporalmente validacion para desarrollo sin login
    RUTA_GOLD = "ETL/datalake/gold/clean/dataset_master_gold.parquet" #Definir constante con la ruta del conjunto maestro
    RUTA_MODELADO = "MODELADO/data/dataset_modelado_churn.parquet" #Definir constante con la ruta de datos de modelado
    RUTA_RESUMEN_CSV = "EDA/data/resumen_estadistico_completo.csv" #Definir constante con la ruta del resumen base

    st.title("Predicción de la Deserción de Abonados 2026 CVR-MORELIA") #Mostrar el titulo principal de la aplicacion

    with st.sidebar: #Abrir contexto para dibujar en el panel lateral
        menu_principal = option_menu(
            menu_title="Navegación", 
            options=["Predicciones Mensuales 2026", "Análisis Histórico y Modelo 2025"], #Retirar boton de actualizar del array para evitar ciclos infinitos
            icons=["graph-up-arrow", "database"], #Retirar icono
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
                "nav-link-selected": {"background-color": "#0ea5e9", "color": "white", "font-weight": "600"}, #Color azul corporativo para elemento seleccionado
            }
        ) #Construir y dar estilo el menu de navegacion visual

        st.markdown("---") #Insertar una linea horizontal divisoria en la barra lateral
        
        if st.button("ACTUALIZAR DATOS", use_container_width=True): #Comprobar si el usuario presiono el boton independiente
            st.cache_data.clear() #Limpiar la memoria cache de streamlit para forzar lectura fresca
            st.session_state.buscar_contrato = "" #Vaciar variable de busqueda central
            
            llaves_a_borrar = ['txt_buscar', 'sb_abandono', 'sb_riesgo'] #Definir lista de componentes visuales
            for llave in llaves_a_borrar: #Iterar sobre cada uno
                if llave in st.session_state: #Confirmar existencia
                    del st.session_state[llave] #Eliminar para forzar reinicio en blanco
                    
            st.success("Datos actualizados correctamente.") #Mostrar tarjeta verde corporativa

    if menu_principal == "Predicciones Mensuales 2026": #Opcion 1 menu
        st.header("Monitoreo Mensual de Riesgo de Abandono (Churn) 2026 CVR-MORELIA") #Dibujar el encabezado de la seccion mensual
        
        ruta_scored = "ETL/datalake/gold/scored/" #Definir ruta local de los archivos mensuales
        if os.path.exists(ruta_scored): #Verificar que la carpeta de destino exista
            archivos_pred = glob.glob(f"{ruta_scored}predicciones_churn_*.csv") #Generar lista de todos los archivos csv que coincidan con el mes
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
                    df_riesgo = df_mes[df_mes['PROBABILIDAD_RIESGO'] >= 0.5] #Filtrar clientes de probabilidad probabilistica base
                    
                df_riesgo_alto = df_mes[df_mes['PROBABILIDAD_RIESGO'] >= 0.15] #Filtrar subconjunto secundario con clientes

                if 'PROBABILIDAD_RIESGO' in df_mes.columns: #Verificar existencia de columna probabilistica para ordenamiento
                    df_riesgo = df_riesgo.sort_values(by='PROBABILIDAD_RIESGO', ascending=False) #Ordenar contratos de abandono de mayor a menor riesgo
                    df_riesgo_alto = df_riesgo_alto.sort_values(by='PROBABILIDAD_RIESGO', ascending=False) #Ordenar contratos de riesgo de mayor a menor probabilidad

                k1, k2, k3 = st.columns(3) #Dividir en tres columnas iguales
                
                with k1: #Trabajar dentro de la primera columna
                    st.metric("Total Clientes Evaluados", f"{len(df_mes):,}") #Insertar tarjeta con el recuento total de clientes procesados
                    
                with k2: #Trabajar dentro de la segunda columna
                    st.metric("Clientes Predicción de Abandono", f"{len(df_riesgo):,}") #Insertar tarjeta con recuento de abandonos detectados
                    lista_abandono = crear_lista_detallada(df_riesgo) #Procesar opciones textuales con datos de los clientes en abandono
                    st.selectbox("Contratos en Abandono:", lista_abandono, key="sb_abandono", on_change=actualizar_desde_abandono, label_visibility="collapsed") #Pintar dropdown funcional ocultando su etiqueta superior
                    
                with k3: #Trabajar dentro de la tercera columna
                    st.metric("Clientes en Riesgo", f"{len(df_riesgo_alto):,}") #Insertar tarjeta con recuento
                    lista_riesgo_alto = crear_lista_detallada(df_riesgo_alto) #Procesar opciones textuales para riesgo moderado
                    st.selectbox("Contratos en Riesgo:", lista_riesgo_alto, key="sb_riesgo", on_change=actualizar_desde_riesgo, label_visibility="collapsed") #Pintar dropdown interactivo para la tercera tarjeta
                
                st.markdown("---") #Pintar linea separadora visual
                
                col_grafico, col_buscador = st.columns([1.5, 1]) #Dividir espacio inferior en dos columnas asimetricas
                
                with col_grafico: #Abrir bloque de la columna izquierda para graficos
                    st.subheader("Indicadores de Riesgo del Mes") #Poner titulo del cuadrante de graficos
                    ruta_shap = f"MODELADO/graficos_modelado_{mes_amigable}/01_shap_summary_{mes_amigable}.png" #Generar ruta dinamica para buscar el grafico del mes
                    if os.path.exists(ruta_shap): #Verificar disponibilidad de la imagen generada
                        st.markdown("<br>", unsafe_allow_html=True) #Anadir separador superior estandar
                        st.image(ruta_shap, use_container_width=True) #Proyectar imagen shap
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
                            
                            fila_res = resultado.iloc[0] #Aislar primera fila
                            c_det = str(fila_res.get('CONTRATO', 'N/D')).replace('nan', 'N/D') #Procesar contrato
                            z_det = str(fila_res.get('ZONA', 'N/D')).replace('nan', 'N/D') #Procesar zona
                            o_det = str(fila_res.get('ONT_MODEL', 'N/D')).replace('nan', 'N/D').replace('None', 'N/D') #Procesar modelo
                            r_val = fila_res.get('RX_AVG') #Leer rx
                            r_det = f"{float(r_val):.2f} dBm" if not pd.isna(r_val) else "N/D" #Estandarizar rx
                            
                            mc1, mc2 = st.columns(2) #Crear primer par de columnas para tarjetas
                            mc1.metric(label="Contrato", value=c_det) #Incluir tarjeta de contrato
                            mc2.metric(label="Zona", value=z_det) #Incluir tarjeta de zona
                            mc3, mc4 = st.columns(2) #Crear segundo par de columnas para tarjetas
                            mc3.metric(label="ONT", value=o_det) #Incluir tarjeta de equipo
                            mc4.metric(label="Nivel Óptico (Rx)", value=r_det) #Incluir tarjeta de potencia
                        else: #Proceder si el numero no se encontro
                            st.error("Contrato no encontrado en este período.") #Generar banner de error al usuario

            with tab_resumen_mes: #Entrar en contexto de la segunda pestana
                st.subheader(f"Resumen Datos Clave - Período {mes_amigable}") #Renderizar subtitulo con el periodo actual
                ruta_resumen_mes = f"EDA/data/resumen_estadistico_{mes_amigable}.csv" #Componer la ruta de datos estadisticos correspondientes
                if os.path.exists(ruta_resumen_mes): #Confirmar integridad del archivo origen
                    try: #Proteger lectura de datos propensa a fallos
                        df_resumen_mes = pd.read_csv(ruta_resumen_mes) #Extraer informacion del csv a pandas
                        
                        m1, m2, m3 = st.columns(3) #Generar tres divisiones para indicadores secundarios
                        m1.metric(f"Total Registros {mes_amigable}", f"{len(df_mes):,}") #Incluir cantidad de registros del archivo
                        m2.metric("Nivel Óptico Promedio", f"{df_mes['RX_AVG'].mean():.2f} dBm") #Incluir promedio del nivel de senal del mes
                        m3.metric("Días Atención Promedio", f"{df_mes['DIAS_ATENCION'].mean():.1f}") #Incluir promedio de dias tardados
                        
                        st.markdown("<br>", unsafe_allow_html=True) #Forzar salto de linea
                        
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
                                df_mes['PREDICCION_ABANDONO'] = (df_mes['PROBABILIDAD_RIESGO'] >= 0.5).astype(int) #Generar clasificacion binaria
                                
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
                            st.dataframe(df_resumen_mes, use_container_width=True) #Integrar resumen detallado
                            
                    except Exception as e: #Aislar el error en variable generica
                        st.error(f"Error al cargar los datos estadísticos del mes: {e}") #Mostrar texto descriptivo del incidente de lectura
                else: #Accion por defecto ante ruta invalida
                    st.warning("No se encontró el archivo de resumen estadístico para este mes.") #Notificar que falta ejecucion previa del script

            with tab_eda_mes: #Activar pestana final de exploracion visual mensual interactiva
                st.subheader(f"Comportamiento de las Variables Principales - Período {mes_amigable}") #Poner titulo
                
                col1, col_sep, col2 = st.columns([1, 0.02, 1]) #Fraccionar area inferior en tres columnas
                
                with col_sep: #Configurar columna central como linea divisoria
                    st.markdown("<div style='background-color: rgba(128, 128, 128, 0.4); width: 2px; height: 1500px; margin: 0 auto;'></div>", unsafe_allow_html=True) #Dibujar linea vertical continua y solida
                
                with col1: #Primeros graficos
                    fig_hist = px.histogram(df_mes, x="RX_AVG", nbins=40, color_discrete_sequence=['dodgerblue'], labels={'RX_AVG': 'Nivel Óptico', 'count': 'Cantidad de Clientes'}) #Instanciar histograma
                    
                    df_valid_rx = df_mes['RX_AVG'].dropna() #Aislar datos validos
                    if len(df_valid_rx) > 1: #Comprobar que existen registros suficientes
                        kde = gaussian_kde(df_valid_rx) #Instanciar modelo de estimacion de densidad
                        x_range = np.linspace(df_valid_rx.min(), df_valid_rx.max(), 500) #Generar arreglo de puntos equidistantes
                        y_kde = kde(x_range) #Evaluar densidades en el rango estipulado
                        bin_width = (df_valid_rx.max() - df_valid_rx.min()) / 40 #Calcular ancho matematico de cada barra
                        y_kde_norm = y_kde * len(df_valid_rx) * bin_width #Normalizar curva al eje de frecuencias absolutas
                        fig_hist.add_trace(go.Scatter(x=x_range, y=y_kde_norm, mode='lines', line=dict(color='magenta', width=4), name='Tendencia General (KDE)', showlegend=False, hoverinfo='skip')) #Superponer curva suavizada                    
                    fig_hist.update_traces(hovertemplate='Nivel Óptico: %{x:.2f} dBm<br>Cantidad de Clientes: %{y}<extra></extra>', selector=dict(type='histogram')) #Sobrescribir leyenda emergente                    
                    fig_hist.update_layout(
                        title="Distribución de Nivel Óptico (RX_AVG)", 
                        xaxis_title="Nivel Óptico Recibido (dBm)", 
                        yaxis_title="Frecuencia (Cantidad de Clientes)", 
                        height=400, 
                        margin=dict(l=20, r=20, t=40, b=20),
                        showlegend=True, #Habilitar leyenda para explicar curva
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), #Posicionar leyenda horizontal arriba
                        yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.2)'), #Garantizar grilla en Y corporativa
                        xaxis=dict(
                            showgrid=True, #Habilitar cuadrícula principal
                            gridcolor='rgba(128,128,128,0.2)', #Pintar cuadrícula tenue
                            dtick=2, #Forzar etiquetas de texto cada 2 dBm
                            minor=dict(dtick=1, showgrid=True, gridcolor='rgba(128,128,128,0.1)') #Añadir cuadrícula intermedia sin texto cada 1 dBm
                        ) #Normalizar ejes y leyendas corporativas combinando etiquetas limpias y cuadrícula precisa
                    ) #Actualizar layout simetrico y profesional                    
                    st.plotly_chart(fig_hist, use_container_width=True, config={'locale': 'es'}) #Proyectar visualizacion
                    st.markdown("---") #Anadir separador horizontal sutil
                    
                    df_mes['MOTIVO_PEDIDO_CLN'] = df_mes['MOTIVO_PEDIDO'].astype(str).str.replace('DA?ADO', 'DAÑADO', regex=False).str.replace('DAADO', 'DAÑADO', regex=False) #Limpiar texto de motivos
                    top_motivos = df_mes['MOTIVO_PEDIDO_CLN'].value_counts().head(10).reset_index() #Extraer frecuencias top diez
                    top_motivos.columns = ['Motivo', 'Cantidad'] #Renombrar columnas temporales
                    top_motivos = top_motivos.sort_values(by='Cantidad', ascending=True) #Invertir orden para que plotly dibuje la barra mayor arriba                    
                    top_motivos['Texto'] = top_motivos['Cantidad'].astype(str) + " Reportes" #Concatenar numero y palabra clave
                    fig_motivos = px.bar(top_motivos, x='Cantidad', y='Motivo', orientation='h', color='Cantidad', color_continuous_scale='Viridis', text='Texto', labels={'Cantidad': 'Reportes Totales', 'Motivo': 'Falla Registrada'}) #Generar figura plotly
                    fig_motivos.update_traces(textposition='outside', hovertemplate='Motivo: %{y}<br>Reportes: %{x}<extra></extra>') #Forzar dibujo de texto por fuera y personalizar leyenda
                    fig_motivos.update_layout(title="Frecuancia de Motivos de Fallas", xaxis_title="Cantidad de Reportes", yaxis_title="Motivo de Pedido", height=400, margin=dict(l=20, r=80, t=40, b=20), showlegend=False) #Ajustar titulos
                    fig_motivos.update_xaxes(range=[0, top_motivos['Cantidad'].max() * 1.35]) #Expandir limite derecho para mostrar texto completo
                    st.plotly_chart(fig_motivos, use_container_width=True, config={'locale': 'es'}) #Proyectar visualizacion
                    st.markdown("---") #Anadir separador horizontal sutil
                    
                    df_mes['ONT_MODEL_CLN'] = df_mes['ONT_MODEL'].astype(str).replace(['nan', 'NaN', 'NAN', 'None'], 'DESCONOCIDO').fillna('DESCONOCIDO') #Estandarizar nombres de equipos nulos
                    top_10_vol = df_mes['ONT_MODEL_CLN'].value_counts().head(10).index #Identificar equipos con mayor presencia fisica
                    df_top_ont = df_mes[df_mes['ONT_MODEL_CLN'].isin(top_10_vol)] #Filtrar datos unicamente al top diez
                    fallas = df_top_ont['ONT_MODEL_CLN'].value_counts() #Sumarizar fallas por equipo
                    unicos = df_top_ont.groupby('ONT_MODEL_CLN')['CONTRATO'].nunique() #Agrupar y contar clientes unicos afectados
                    tasa = (fallas / unicos).reset_index() #Dividir para obtener tasa pura
                    tasa.columns = ['Modelo', 'Tasa'] #Renombrar columnas resultantes
                    tasa = tasa.sort_values(by='Tasa', ascending=True) #Invertir ordenamiento para diagrama horizontal
                    tasa['Texto'] = tasa['Tasa'].round(2).astype(str) + " fallas/cliente" #Construir cadena textual para etiqueta
                    fig_reincidencia = px.bar(tasa, x='Tasa', y='Modelo', orientation='h', text='Texto', color_discrete_sequence=['dodgerblue']) #Dibujar barras horizontales limpiando configuraciones previas conflictivas
                    fig_reincidencia.update_traces(textposition='outside', hovertemplate='Modelo de ONT: %{y}<br>Tasa Promedio: %{x:.2f} fallas/cliente<extra></extra>') #Forzar dibujo de texto externo y sobrescribir tooltip completamente
                    fig_reincidencia.update_layout(title="Tasa de Reincidencia por Modelo de ONT", xaxis_title="Tasa de Reincidencia por Modelo de ONT", yaxis_title="Modelo de ONT", height=400, margin=dict(l=20, r=20, t=40, b=20)) #Configurar layout visual
                    fig_reincidencia.update_xaxes(range=[0, tasa['Tasa'].max() * 1.2]) #Expandir limite x para evitar cortes de texto
                    st.plotly_chart(fig_reincidencia, use_container_width=True, config={'locale': 'es'}) #Proyectar visualizacion
                    st.markdown("---") #Anadir separador horizontal sutil
                    
                with col2: #Segundos graficos
                    if 'PREDICCION_ABANDONO' not in df_mes.columns and 'PROBABILIDAD_RIESGO' in df_mes.columns: #Garantizar columna objetivo
                        df_mes['PREDICCION_ABANDONO'] = (df_mes['PROBABILIDAD_RIESGO'] >= 0.5).astype(int) #Crear clasificador
                    df_mes['CLASE_TEXTO'] = df_mes['PREDICCION_ABANDONO'].map({0: 'ACTIVO', 1: 'BAJA'}) #Traducir codigo a texto corporativo                    
                    mapa_colores = {'ACTIVO': 'mediumseagreen', 'BAJA': 'indianred'} #Establecer paleta de colores
                    
                    fig_box = px.box(df_mes, x="RX_AVG", y="CLASE_TEXTO", color="CLASE_TEXTO", color_discrete_map=mapa_colores, category_orders={"CLASE_TEXTO": ["BAJA", "ACTIVO"]}, labels={'RX_AVG': 'Potencia (dBm)', 'CLASE_TEXTO': 'Estado Actual'}) #Armar boxplot horizontal asignando etiquetas legibles
                    fig_box.update_traces(hovertemplate='Estado: %{y}<br>Nivel Óptico: %{x:.2f} dBm<extra></extra>') #Limpiar tooltip eliminando nombres de variables base
                    fig_box.update_xaxes(hoverformat='.2f') #Aplicar formato de dos decimales al eje x                    
                    fig_box.update_layout(title="Relacion Nivel Óptico y Deserción", xaxis_title="Nivel Óptico Recibido (dBm) - [Más cerca de 0 es mejor]", yaxis_title="Estado Operativo del Cliente", height=400, margin=dict(l=20, r=20, t=40, b=20), showlegend=False, template="plotly_white") #Empaquetar titulos descriptivos conservando plantilla clara
                    fig_box.update_yaxes(categoryorder="array", categoryarray=["BAJA", "ACTIVO"]) #Reafirmar posicionamiento vertical de categorias                    
                    st.plotly_chart(fig_box, use_container_width=True, config={'locale': 'es'}) #Proyectar visualizacion
                    st.markdown("---") #Anadir separador horizontal sutil
                    
                    top_7_ont = df_mes['ONT_MODEL_CLN'].value_counts().head(7).reset_index() #Seleccionar top siete fabricantes
                    top_7_ont.columns = ['Modelo', 'Cantidad'] #Renombrar datos agregados
                    fig_donut = px.pie(top_7_ont, names='Modelo', values='Cantidad', hole=0.7, color_discrete_sequence=px.colors.qualitative.Pastel) #Crear tarta calibrada limpiando etiquetas automáticas conflictivas                    
                    fig_donut.update_traces(textposition='auto', textinfo='percent+label', hovertemplate='Modelo de ONT: %{label}<br>Equipos Instalados: %{value}<extra></extra>') #Permitir extraccion de textos en rebanadas pequenas y personalizar leyenda
                    fig_donut.update_layout(title="Distribución de Modelos de ONT Instalados", height=400, margin=dict(l=20, r=20, t=40, b=20), showlegend=False) #Adherir titulo principal
                    st.plotly_chart(fig_donut, use_container_width=True, config={'locale': 'es'}) #Proyectar visualizacion
                    st.markdown("---") #Anadir separador horizontal sutil
                    
                    if 'DIAS_ATENCION' in df_mes.columns: #Verificar datos temporales
                        tiempo_zona = df_mes.groupby('ZONA')['DIAS_ATENCION'].mean().reset_index() #Agregar tiempos por zona
                        tiempo_zona = tiempo_zona.sort_values(by='DIAS_ATENCION', ascending=False).head(15) #Aislar quince peores zonas
                        tiempo_zona = tiempo_zona.sort_values(by='DIAS_ATENCION', ascending=True) #Preparar lista para trazado ascendente plotly                        
                        fig_zonas = px.bar(tiempo_zona, x='DIAS_ATENCION', y='ZONA', orientation='h', color_discrete_sequence=['coral'], text='DIAS_ATENCION', labels={'DIAS_ATENCION': 'Días de Retraso', 'ZONA': 'Zona'}) #Delinear grafico de impacto inyectando texto nativo
                        fig_zonas.update_traces(texttemplate='%{x:.2f} Días de Retraso', textposition='outside', hovertemplate='Zona: %{y}<br>Días de Retraso: %{x:.2f}<extra></extra>') #Forzar formato de texto y decimales en etiquetas y cajas emergentes
                        fig_zonas.update_layout(title="Zonas con Mayor Tiempo Promedio de Atención", xaxis_title="Tiempo Promedio de Atención (Días)", yaxis_title="Zona", height=400, margin=dict(l=20, r=20, t=40, b=20)) #Registrar descripciones
                        fig_zonas.update_xaxes(range=[0, tiempo_zona['DIAS_ATENCION'].max() * 1.3]) #Expandir limite derecho para mostrar texto completo
                    else: #Fallo controlado
                        fig_zonas = px.bar(title="Datos de Días de Atención No Disponibles") #Crear ventana                  
                    st.plotly_chart(fig_zonas, use_container_width=True, config={'locale': 'es'}) #Proyectar visualizacion
                    st.markdown("---") #Anadir separador horizontal sutil

        else: #Opcion si la busqueda de archivos esta vacia
            st.warning("No se encontraron predicciones mensuales en el Datalake. Ejecuta el pipeline.") #Alerta final de vacio

    elif menu_principal == "Análisis Histórico y Modelo 2025": #Validar seleccion historica
        st.header("Análisis Histórico y Entrenamiento del Modelo Año 2025") #Dibujar etiqueta titular del 2025
        
        tab_modelado, tab_resumen, tab_eda = st.tabs(["Desempeño del Modelo", "Resumen Ejecutivo", "Exploración de Datos"]) #Armar arreglo de pestanas globales
        
        with tab_modelado: #Activar primer espacio explicativo del modelo
            st.subheader("Principales Hallazgos: Influencia de Variables en el Riesgo de Cancelación") #Preparar area del shap global
            st.image("MODELADO/graficos_modelado/03_shap_xgboost.png", caption="Interpretación de impacto mediante valores SHAP", use_container_width=True) #Invocar renderizado 
            st.info("El gráfico superior identifica los disparadores críticos del abandono de clientes.") #Colocar barra de informacion
            
            st.markdown("---") #Crear quiebre tematico horizontal
            st.subheader("Evaluación y Desempeño del Modelo Campeón") #Establecer titulo de metricas de validacion
            col_roc, col_mat = st.columns(2) #Picar pantalla en dos lienzos cuadrados
            with col_roc: #Usar el cuadro izquierdo
                st.image("MODELADO/graficos_modelado/02_curva_roc_combinada.png", caption="Comparativa de Capacidad Predictiva (Curva ROC)", use_container_width=True) #Pegar png nativo conservando menu
            with col_mat: #Usar el cuadro derecho
                st.image("MODELADO/graficos_modelado/01_matrices_confusion_comparativa.png", caption="Comparativa de Matrices de Confusión", use_container_width=True) #Pegar png interactivo ajustado visualmente

        with tab_resumen: #Ingresar al panel de lectura de 2025
            st.subheader("Resumen Datos Clave") #Presentar titulo
            try: #Abrir entorno a prueba de caidas por archivos corruptos
                df_churn, df_resumen = cargar_datos_historicos(RUTA_MODELADO, RUTA_RESUMEN_CSV) #Invocar funcion para agilizar lectura
                
                m1, m2, m3 = st.columns(3) #Definir tres lugares en fila
                m1.metric("Total Registros 2025", f"{len(df_churn):,}") #Fijar el volumen masivo de datos del ano
                m2.metric("Nivel Óptico Promedio", f"{df_churn['RX_AVG_PROMEDIO'].mean():.2f} dBm") #Fijar el calculo global optico
                m3.metric("Días Atención Promedio", f"{df_churn['DIAS_ATENCION_PROMEDIO'].mean():.1f}") #Fijar el lapso de servicio anual
                
                st.markdown("<br>", unsafe_allow_html=True) #Dejar espacio en blanco
                
                st.metric("Top Paquete", f"{df_resumen.loc[df_resumen['Columna'] == 'PAQUETE_x', 'Top_Valor'].iloc[0]}", f"{df_resumen.loc[df_resumen['Columna'] == 'PAQUETE_x', 'Valores_Unicos'].iloc[0]} UNICOS") #Construir metrica base leyendo paquete principal de 2025
                st.metric("Top Motivo", f"{df_resumen.loc[df_resumen['Columna'] == 'MOTIVO_PEDIDO', 'Top_Valor'].iloc[0]}", f"{df_resumen.loc[df_resumen['Columna'] == 'MOTIVO_PEDIDO', 'Valores_Unicos'].iloc[0]} UNICOS") #Construir metrica leyendo queja historica preeminente
                st.metric("Top Detalle", f"{df_resumen.loc[df_resumen['Columna'] == 'DETALLE_PEDIDO1', 'Top_Valor'].iloc[0]}", f"{df_resumen.loc[df_resumen['Columna'] == 'DETALLE_PEDIDO1', 'Valores_Unicos'].iloc[0]} UNICOS") #Construir metrica apuntando al origen del problema anual
                st.metric("Top Modelo ONT", f"{df_resumen.loc[df_resumen['Columna'] == 'ONT_MODEL', 'Top_Valor'].iloc[0]}", f"{df_resumen.loc[df_resumen['Columna'] == 'ONT_MODEL', 'Valores_Unicos'].iloc[0]} UNICOS") #Construir metrica senalando el equipo del que mas dependio ceeveerre
                
                st.markdown("---") #Imprimir barra
                col_left, col_right = st.columns([1, 1]) #Partir zona baja
                
                with col_left: #Escribir bloque para datos historicos
                    st.subheader("Vista Previa de Datos Preparados") #Poner caption de encabezado
                    st.dataframe(df_churn, use_container_width=True) #Impresion de datos con widget oficial sin ocultar columnas
                    
                with col_right: #Escribir bloque para reporte de info estadistica historica
                    st.subheader("Descripción Estadística Base") #Poner titulo correspondiente
                    if 'Tipo_Dato' in df_resumen.columns: #Verificar si el campo tipo de dato esta presente
                        df_resumen = df_resumen.drop(columns=['Tipo_Dato']) #Excluir el campo de tipos de dato del reporte
                    cols_res_hist = list(df_resumen.columns) #Listar distribucion actual de las columnas
                    for c in ['Total_Valores', 'Valores_Nulos', 'Valores_Unicos']: #Procesar cada variable de resumen matematico
                        if c in cols_res_hist: #Validar su localizacion real
                            cols_res_hist.remove(c) #Sacar de en medio para aislar
                            cols_res_hist.append(c) #Insertar al final de la cola formativa
                    df_resumen = df_resumen[cols_res_hist] #Consolidar dataframe base reestructurado
                    st.dataframe(df_resumen, use_container_width=True) #Mostrar reporte base completo sin interruptor
                    
            except Exception as e: #Guardar Excepciones
                st.error(f"Error al cargar los datos históricos: {e}") #Notificar visualmente el fracaso al intentar leer la matriz
                
        with tab_eda: #Operar en pestana historica de graficos generales
            st.subheader("Comportamiento de las Variables Principales") #Declarar seccion inicial del eda
            
            def renderizar_grafico_estandarizado(ruta_imagen, titulo_html): #Definir funcion para estandarizar formas de imagenes estaticas
                st.markdown(f"<h4 style='text-align: center; font-size: 18px; margin-bottom: 5px;'>{titulo_html}</h4>", unsafe_allow_html=True) #Imprimir titulo grande centrado
                try: #Iniciar control de carga de imagen
                    img_original = Image.open(ruta_imagen) #Cargar imagen original en memoria
                    img_cuadricula = ImageOps.pad(img_original, (1200, 800), color="white") #Rellenar imagen con bordes blancos hasta formato 3:2 exacto
                    st.image(img_cuadricula, use_container_width=True) #Proyectar imagen homogeneizada
                except Exception as e: #Capturar fallos de disco
                    st.warning(f"No se encontró el gráfico: {ruta_imagen}") #Notificar perdida de recurso visual
            
            col1, col_sep, col2 = st.columns([1, 0.02, 1]) #Distribuir area inferior en tres columnas reduciendo grosor central
            
            with col_sep: #Configurar columna central como linea divisoria
                st.markdown("<div style='background-color: rgba(128, 128, 128, 0.4); width: 2px; height: 1600px; margin: 0 auto;'></div>", unsafe_allow_html=True) #Dibujar linea vertical continua adaptada a dimensiones uniformes
            
            with col1: #Mostrar primeros graficos
                renderizar_grafico_estandarizado("EDA/graficos_eda/01_histograma_rx_avg.png", "Distribución de Potencia Óptica (dBm)") #Llamar funcion para proyectar primer grafico
                st.markdown("---") #Anadir separador horizontal sutil
                
                renderizar_grafico_estandarizado("EDA/graficos_eda/02_barras_motivo_pedido.png", "Frecuancia de Motivos de Fallas") #Llamar funcion para proyectar segundo grafico
                st.markdown("---") #Anadir separador horizontal sutil
                
                renderizar_grafico_estandarizado("EDA/graficos_eda/01_ont_vs_tasa_reincidencia.png", "Tasa de Reincidencia por Modelo de ONT") #Llamar funcion para proyectar tercer grafico
                st.markdown("---") #Anadir separador horizontal sutil

            with col2: #Mostrar segundos graficos
                renderizar_grafico_estandarizado("EDA/graficos_eda/03_churn_vs_potencia.png", "Relacion Nivel Óptico y Deserción") #Llamar funcion para proyectar cuarto grafico
                st.markdown("---") #Anadir separador horizontal sutil
                
                renderizar_grafico_estandarizado("EDA/graficos_eda/03_donut_ont_model.png", "Distribución de Modelos ONTs") #Llamar funcion para proyectar quinto grafico
                st.markdown("---") #Anadir separador horizontal sutil
                
                renderizar_grafico_estandarizado("EDA/graficos_eda/02_zona_vs_tiempo.png", "Zonas con Mayor Tiempo Promedio de Atención") #Llamar funcion para proyectar sexto grafico
                st.markdown("---") #Anadir separador horizontal sutil

    st.markdown("---") #Insertar linea separadora final
    st.markdown(
        """
        <div id='pie_pagina'>
            &copy; 2026 Predicción de la Deserción de Abonados CVR-MORELIA. | Desarrollado por: Rubén Lara Bárcenas
        </div>
        """, 
        unsafe_allow_html=True
    ) #Incluir pie de pagina corporativo en formato html