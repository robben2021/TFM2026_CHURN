::!/bin/bash
echo "Iniciando Pipeline de Datos..."

:: 1. Correr ETL
jupyter nbconvert --to notebook --execute --inplace ETL/A_BRONZE_EXPLORACION_OLT.ipynb
jupyter nbconvert --to notebook --execute --inplace ETL/A_BRONZE_EXPLORACION_ZABBIX.ipynb
jupyter nbconvert --to notebook --execute --inplace ETL/B_SILVER_PROCESAR_OS_FECHA-INSTALACION.ipynb
jupyter nbconvert --to notebook --execute --inplace ETL/B_SILVER_AGREGAR_RX_ZABBIX.ipynb
jupyter nbconvert --to notebook --execute --inplace ETL/B_SILVER_AGREGAR_ONT-MODEL_SOFTWARE-VERSION.ipynb
jupyter nbconvert --to notebook --execute --inplace ETL/C_GOLD_LIMPIEZA_VALORES-DUPLICADOS.ipynb

:: 2. Correr EDA
jupyter nbconvert --to notebook --execute --inplace EDA/RESUMEN_ESTADISTICO.ipynb

:: 3. Correr Inferencia Mensual del Modelo
jupyter nbconvert --to notebook --execute --inplace MODELADO/MODELADO.ipynb

echo "Pipeline finalizado con exito. Datos listos para Streamlit."

pause