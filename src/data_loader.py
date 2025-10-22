import yfinance as yf
import pandas as pd
import json
import os
import time

# --- CONFIGURACIÓN ---
# Carpeta donde se guardarán los datos brutos descargados
RAW_DATA_DIR = 'data/raw'

# Tickers de ejemplo. En un proyecto real, cargarías los 500 tickers desde un archivo.
TICKERS_EJEMPLO = ['MSFT', 'ORCL', 'CRM', 'CSCO', 'ADBE', 'NOW', 'AKAM', 'VRSN', 'CDNS', 'JPM', 'BAC', 'WFC', 'V', 'MA', 'BLK', 'GS', 'SPGI', 'MCO', 'C', 'JNJ', 'UNH', 'LLY', 'MRK', 'ABBV', 'PFE', 'TMO', 'ABT', 'DHR', 'GILD', 'PG', 'KO', 'PEP', 'WMT', 'COST', 'MDLZ', 'CL', 'KHC', 'GIS', 'CHD']

# --- FUNCIONES CORE ---

def setup_directories():
    """Asegura que las carpetas de datos existan."""
    if not os.path.exists(RAW_DATA_DIR):
        os.makedirs(RAW_DATA_DIR)
        print(f"Directorio creado: {RAW_DATA_DIR}")

def download_and_save_data(ticker):
    """
    Descarga la información financiera clave de un solo ticker y la guarda
    en múltiples archivos JSON dentro de la carpeta RAW_DATA_DIR.
    """
    print(f"\n--- Procesando {ticker} ---")
    try:
        # 1. Inicializar el objeto Ticker
        stock = yf.Ticker(ticker)

        # 2. Obtener información general (ratios, sector, etc.)
        info = stock.info
        if not info:
            print(f"AVISO: No se encontró información para {ticker}.")
            return False
        
        # 3. Guardar la información general
        with open(os.path.join(RAW_DATA_DIR, f'{ticker}_info.json'), 'w') as f:
            json.dump(info, f, indent=4)

        # 4. Obtener Estados Financieros (últimos 4 años)
        financials = stock.financials.to_json(orient='columns', indent=4)
        with open(os.path.join(RAW_DATA_DIR, f'{ticker}_financials.json'), 'w') as f:
            f.write(financials)

        # 5. Obtener Balance General (últimos 4 años)
        balance_sheet = stock.balance_sheet.to_json(orient='columns', indent=4)
        with open(os.path.join(RAW_DATA_DIR, f'{ticker}_balance_sheet.json'), 'w') as f:
            f.write(balance_sheet)
        
        # 6. Obtener Flujos de Caja (últimos 4 años)
        cashflow = stock.cashflow.to_json(orient='columns', indent=4)
        with open(os.path.join(RAW_DATA_DIR, f'{ticker}_cashflow.json'), 'w') as f:
            f.write(cashflow)

        print(f"Datos de {ticker} descargados y guardados con éxito.")
        return True

    except Exception as e:
        print(f"ERROR: Falló la descarga de datos para {ticker}. Razón: {e}")
        return False

def run_data_pipeline(tickers_list):
    """Orquesta el proceso de descarga de datos para toda la lista de tickers."""
    setup_directories()
    
    print(f"Iniciando descarga para {len(tickers_list)} tickers.")
    downloaded_count = 0

    for ticker in tickers_list:
        if download_and_save_data(ticker):
            downloaded_count += 1
        
        # Pausa para evitar ser bloqueado por la API (Buenas prácticas)
        time.sleep(1) 

    print("\n--- RESUMEN DE LA DESCARGA ---")
    print(f"Total de tickers procesados: {len(tickers_list)}")
    print(f"Descargas exitosas: {downloaded_count}")
    print("El proceso de descarga de datos brutos ha finalizado.")

if __name__ == '__main__':
    # En un proyecto real, cargarías una lista grande.
    # Por ejemplo, leyendo desde un JSON o CSV que contenga los 500 tickers.
    # Ejemplo: tickers = pd.read_csv('config/sp500_tickers.csv')['Symbol'].tolist()
    
    run_data_pipeline(TICKERS_EJEMPLO)
