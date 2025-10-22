import yfinance as yf
import pandas as pd
import json
import os
import time
from datetime import datetime

# --- CONFIGURACIÓN DE RUTAS (Basada en ratio_calculator.py) ---
# Directorio base donde se encuentra la información de la industria
INPUT_DIR = 'data/raw' 
# Usamos un marcador de posición {ticker} para construir los nombres de los archivos
FILE_PATTERN = '{ticker}_{type}.json'
# Lista de empresas a analizar (DEBE COINCIDIR con la utilizada en otros scripts)
TICKERS_TO_ANALYZE = ['MSFT', 'ORCL', 'CRM', 'CSCO', 'ADBE', 'NOW', 'AKAM', 'VRSN', 'CDNS', 'ANSS', 'JPM', 'BAC', 'WFC', 'V', 'MA', 'BLK', 'GS', 'SPGI', 'MCO', 'C', 'JNJ', 'UNH', 'LLY', 'MRK', 'ABBV', 'PFE', 'TMO', 'ABT', 'DHR', 'GILD', 'PG', 'KO', 'PEP', 'WMT', 'COST', 'MDLZ', 'CL', 'KHC', 'GIS', 'CHD']
# Carpeta de salida para los datos procesados (donde se guardan los ratios)
OUTPUT_BASE_DIR = 'data/processed'

# --- FUNCIONES CORE ---

def get_industry_key(ticker):
    """
    Lee el archivo 'info.json' para obtener la IndustryKey (sector) de un ticker.
    Esto garantiza que los precios se guarden en la misma carpeta que los ratios.
    """
    # Construir la ruta al archivo info.json usando el patrón de archivo
    info_path = os.path.join(INPUT_DIR, FILE_PATTERN.format(ticker=ticker, type='info'))
    try:
        with open(info_path, 'r') as f:
            info_data = json.load(f)
            # Intentar obtener 'industryKey', si no, usar 'sector', si no, 'default_industry'
            return info_data.get('industryKey') or info_data.get('sector') or 'default_industry'
    except FileNotFoundError:
        print(f"Advertencia: Archivo INFO no encontrado para {ticker} en {info_path}. Usando 'default_industry'.")
        return 'default_industry'
    except Exception as e:
        print(f"Error al leer el archivo INFO de {ticker}: {e}. Usando 'default_industry'.")
        return 'default_industry'

def download_and_save_prices(ticker):
    """
    Descarga los precios históricos (últimos 5 años) y los guarda en un CSV
    dentro de la subcarpeta de su industria dentro de OUTPUT_BASE_DIR.
    """
    
    # 1. Obtener la IndustryKey (Sector)
    industry = get_industry_key(ticker)
    
    # 2. Definir la ruta de salida
    # La ruta de salida incluye la subcarpeta del sector: data/processed/{sector}/
    industry_output_dir = os.path.join(OUTPUT_BASE_DIR, industry)
    os.makedirs(industry_output_dir, exist_ok=True)
    
    file_name = f"{ticker}_historical_prices.csv"
    output_path = os.path.join(industry_output_dir, file_name)
    
    print(f"\n--- Descargando precios de {ticker} (Industria: {industry}) ---")

    try:
        # Descargar los precios: 5 años de datos con intervalo semanal para mantener el tamaño razonable
        # Sí, la función correcta es yf.download()
        data = yf.download(ticker, period='5y', interval='1wk', progress=False) 

        if data.empty:
            print(f"Advertencia: No se encontraron datos de precios para {ticker}.")
            return False

        # Guardar solo las columnas relevantes
        data[['Close', 'Volume']].to_csv(output_path)
        print(f"Éxito: Precios históricos de {ticker} guardados en: {output_path}")
        return True

    except Exception as e:
        print(f"ERROR: Falló la descarga de precios para {ticker}. Razón: {e}")
        return False

def run_price_download_pipeline(tickers_list=TICKERS_TO_ANALYZE):
    """Orquesta el proceso de descarga de datos de precios para toda la lista de tickers."""
    
    # Crear la carpeta de salida principal si no existe
    os.makedirs(OUTPUT_BASE_DIR, exist_ok=True)
    
    print("Iniciando la descarga de precios históricos...")
    
    downloaded_count = 0
    for ticker in tickers_list:
        if download_and_save_prices(ticker):
            downloaded_count += 1
        
        # Pausa breve para buenas prácticas
        time.sleep(0.5) 
            
    print("\n--- RESUMEN DE LA DESCARGA DE PRECIOS ---")
    print(f"Total de tickers procesados: {len(tickers_list)}")
    print(f"Archivos de precios guardados: {downloaded_count}")



# Se asume que este es el script principal que deseas ejecutar.
run_price_download_pipeline()