import pandas as pd
import json
import os
from datetime import datetime

# --- 1. CONFIGURACIÓN DE ARCHIVOS Y RUTAS ---
# Directorio base donde se encuentran los archivos JSON
INPUT_DIR = 'data/raw' 
# Usamos un marcador de posición {ticker} para construir los nombres de los archivos
FILE_PATTERN = '{ticker}_{type}.json'
# LISTA DE EMPRESAS A ANALIZAR. Si faltan archivos, el script mostrará una advertencia para ese ticker.
TICKERS_TO_ANALYZE = ['MSFT', 'ORCL', 'CRM', 'CSCO', 'ADBE', 'NOW', 'AKAM', 'VRSN', 'CDNS']

# Columnas necesarias de cada archivo para los cálculos
FINANCIALS_COLS = ['Net Income', 'EBIT', 'EBITDA', 'Tax Provision', 'Pretax Income', 'Diluted EPS']
BALANCE_SHEET_COLS = ['Stockholders Equity', 'Invested Capital', 'Total Debt', 'Cash And Cash Equivalents']
CASHFLOW_COLS = ['Free Cash Flow']

# --- 2. Funciones de Carga y Limpieza de Datos (Adaptadas para un ticker específico) ---
def load_and_clean_financial_data(file_path, keep_columns):
    """
    Carga un archivo JSON de yFinance (balance, financials, cashflow), lo convierte a DataFrame,
    limpia y usa los timestamps como índice.
    """
    try:
        # Aquí se simula la carga desde el sistema de archivos local
        with open(file_path, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        # Esto es normal si se usa un patrón. Simplemente devuelve un DataFrame vacío.
        return pd.DataFrame() 

    # Cargar y transponer el DataFrame para que las fechas sean filas
    df = pd.DataFrame.from_dict(data, orient='index')
    
    # Convertir timestamps (milisegundos) a datetime
    df.index = pd.to_datetime(df.index.astype(float) / 1000, unit='s')
    df.index.name = 'Date'
    
    # Seleccionar solo las columnas necesarias y ordenar
    df = df[keep_columns].sort_index(ascending=True)
    
    return df

def calculate_ratios(df_combined, info_data, ticker):
    """
    Calcula todos los ratios (históricos y de mercado) para el último período disponible.
    Devuelve una Serie de Pandas con los resultados del último periodo y el DataFrame histórico.
    """
    if df_combined.empty:
        return None, None, None

    # --- Ratios Históricos (ROE y ROIC) ---
    
    # 1. ROE (Retorno sobre Fondos Propios)
    # ROE = Net Income / Stockholders Equity
    df_combined['ROE (%)'] = (df_combined['Net Income'] / df_combined['Stockholders Equity']) * 100

    # 2. ROIC (Retorno sobre el Capital Invertido)
    # Tasa Impositiva
    tax_rate = df_combined.apply(
        lambda row: row['Tax Provision'] / row['Pretax Income'] if row['Pretax Income'] != 0 else 0.21, 
        axis=1
    )
    df_combined['ROIC (%)'] = (df_combined['EBIT'] * (1 - tax_rate) / df_combined['Invested Capital']) * 100

    
    # --- Ratios Basados en el Mercado (PER, EV/X) para el último período (Actual) ---
    
    market_cap = info_data.get('marketCap')
    current_price = info_data.get('currentPrice')
    industry_key = info_data.get('industryKey', 'default_industry') # Captura industryKey
    
    if market_cap is None or current_price is None:
        # Devolvemos el histórico pero con un error en el resumen actual
        return {'Error': 'Market Cap o Precio actual no disponible.'}, df_combined.copy(), industry_key

    # Obtener la fila de datos financieros más reciente
    last_period_data = df_combined.iloc[-1]
    last_date = last_period_data.name.strftime('%Y-%m-%d')
    
    total_debt = last_period_data['Total Debt']
    cash = last_period_data['Cash And Cash Equivalents']
    ebit = last_period_data['EBIT']
    ebitda = last_period_data['EBITDA']
    fcf = last_period_data['Free Cash Flow']
    diluted_eps = last_period_data['Diluted EPS']

    # Cálculo del Enterprise Value (EV)
    EV = market_cap + total_debt - cash

    # Preparar el diccionario de resultados ACTUALES
    results_current = {
        'Date (Últ. Reporte)': last_date,
        'Market Cap': market_cap,
        'EV': EV,
        'IndustryKey': industry_key, # Añadir industryKey al resumen actual
        # Ratios de rentabilidad (último año)
        'ROE (%)': last_period_data['ROE (%)'],
        'ROIC (%)': last_period_data['ROIC (%)'],
        # Ratios de Valoración (Usan precio de mercado actual)
        'PER (Price/EPS)': current_price / diluted_eps if diluted_eps != 0 else float('inf'),
        'EV/EBIT': EV / ebit if ebit != 0 else float('inf'),
        'EV/EBITDA': EV / ebitda if ebitda != 0 else float('inf'),
        'EV/FCF': EV / fcf if fcf != 0 else float('inf'),
    }
    
    # Retornamos el resumen actual, la tabla histórica y el industryKey
    return pd.Series(results_current), df_combined.copy(), industry_key

def analyze_ticker(ticker):
    """
    Función principal para cargar, consolidar y analizar los datos de una única empresa (ticker).
    Retorna (ratios_series, df_historical, industry_key)
    """
    print(f"\n--- Procesando {ticker} ---")
    
    # 1. Definir rutas de archivo
    financials_path = os.path.join(INPUT_DIR, FILE_PATTERN.format(ticker=ticker, type='financials'))
    balance_path = os.path.join(INPUT_DIR, FILE_PATTERN.format(ticker=ticker, type='balance_sheet'))
    cashflow_path = os.path.join(INPUT_DIR, FILE_PATTERN.format(ticker=ticker, type='cashflow'))
    info_path = os.path.join(INPUT_DIR, FILE_PATTERN.format(ticker=ticker, type='info'))

    # 2. Cargar datos
    df_financials = load_and_clean_financial_data(financials_path, FINANCIALS_COLS)
    df_balance = load_and_clean_financial_data(balance_path, BALANCE_SHEET_COLS)
    df_cashflow = load_and_clean_financial_data(cashflow_path, CASHFLOW_COLS)

    # Bloque para indicar qué DataFrame está vacío
    if df_financials.empty or df_balance.empty or df_cashflow.empty:
        missing = []
        if df_financials.empty:
            missing.append('Financials')
        if df_balance.empty:
            missing.append('Balance Sheet')
        if df_cashflow.empty:
            missing.append('Cash Flow')
        
        print(f"Advertencia: No se pudo cargar datos completos para {ticker}. Archivos vacíos: {', '.join(missing)}.")
        # Retorna None para el resumen actual, None para el histórico y None para industryKey
        return None, None, None

    info_data = {}
    try:
        with open(info_path, 'r') as f:
            info_data = json.load(f)
    except FileNotFoundError:
        print(f"Advertencia: Archivo INFO no encontrado para {ticker}.")
        return None, None, None # Retorna None para todo si falta INFO

    # 3. Consolidar (Solo las filas completas son críticas para ratios)
    df_combined = pd.concat([df_financials, df_balance, df_cashflow], axis=1).dropna(
        subset=['Net Income', 'Stockholders Equity', 'EBIT', 'EBITDA', 'Free Cash Flow']
    )
    
    if df_combined.empty:
        print(f"Advertencia: No hay períodos completos de datos para {ticker}.")
        return None, None, info_data.get('industryKey', None) # Retorna None, None y industryKey si existe

    # 4. Calcular y obtener ratios del último período
    ratios_series, df_historical, industry_key = calculate_ratios(df_combined, info_data, ticker)
    
    if ratios_series is not None and isinstance(ratios_series, pd.Series):
        ratios_series.name = ticker # Asignar el ticker como nombre de la Serie
        return ratios_series, df_historical, industry_key
    else:
        print(f"Error al calcular ratios de mercado para {ticker}: {ratios_series.get('Error', 'Error desconocido')}")
        return None, df_historical, industry_key


# --- 3. Bucle Principal para Múltiples Empresas ---

all_ratios = []
historical_dataframes = {} # Diccionario para almacenar los DataFrames históricos
# Diccionario para mapear Ticker a IndustryKey y usarlo al guardar el CSV consolidado
ticker_to_industry = {} 

for ticker in TICKERS_TO_ANALYZE:
    # Capturamos el industry_key
    result_current, df_historical, industry_key = analyze_ticker(ticker)
    
    if result_current is not None:
        all_ratios.append(result_current)
        # Guardamos el mapeo Ticker -> IndustryKey
        ticker_to_industry[ticker] = industry_key
    
    if df_historical is not None:
        # Almacenar el DataFrame histórico con el Ticker como clave
        historical_dataframes[ticker] = df_historical

# --- 4. Crear el DataFrame de Resultados Finales y Guardar ---

# Preparar la carpeta de salida
OUTPUT_BASE_DIR = 'data/processed'
os.makedirs(OUTPUT_BASE_DIR, exist_ok=True)
current_date = datetime.now().strftime('%Y-%m-%d')


if all_ratios:
    df_final_ratios = pd.DataFrame(all_ratios)
    df_final_ratios.index.name = 'Ticker' # El índice es el nombre del Ticker
    
    # Extraer la IndustryKey del DataFrame consolidado antes de dar formato
    # Se agruparán los resultados por la IndustryKey para guardarlos por separado.
    
    # 4.1. Guardar la tabla de ratios actuales (dividida por IndustryKey)
    
    # Usamos la columna IndustryKey para agrupar y guardar
    unique_industries = df_final_ratios['IndustryKey'].unique()
    
    for industry in unique_industries:
        df_industry = df_final_ratios[df_final_ratios['IndustryKey'] == industry].drop(columns=['IndustryKey'])
        
        # 1. Definir la ruta de salida (incluyendo la subcarpeta de la industria)
        industry_output_dir = os.path.join(OUTPUT_BASE_DIR, industry)
        os.makedirs(industry_output_dir, exist_ok=True)

        # 2. Guardar el archivo CSV (versión sin formato)
        file_name_current = f"current_ratios_consolidated_{current_date}.csv"
        output_path_current = os.path.join(industry_output_dir, file_name_current)
        df_industry.to_csv(output_path_current)
        print(f"\nÉxito: Tabla de ratios actuales CONSOLIDADOS para '{industry}' guardada en: {output_path_current}")

        # 3. Preparar para visualización
        df_display_ratios = df_industry.copy()
        df_display_ratios['Market Cap'] = (df_display_ratios['Market Cap'] / 1e9).round(2).apply(lambda x: f"{x:,.2f}B")
        df_display_ratios['EV'] = (df_display_ratios['EV'] / 1e9).round(2).apply(lambda x: f"{x:,.2f}B")
        
        for col in ['ROE (%)', 'ROIC (%)', 'PER (Price/EPS)', 'EV/EBIT', 'EV/EBITDA', 'EV/FCF']:
            df_display_ratios[col] = df_display_ratios[col].apply(lambda x: f"{x:.2f}" if x != float('inf') else 'N/A')
        
        output_cols_display = ['Date (Últ. Reporte)', 'ROE (%)', 'ROIC (%)', 'PER (Price/EPS)', 'EV/EBIT', 'EV/EBITDA', 'EV/FCF', 'Market Cap', 'EV']
        df_display_ratios = df_display_ratios[output_cols_display]
        
        print(f"\n--- TABLA CONSOLIDADA PARA INDUSTRIA: {industry.upper()} ---")
        print(df_display_ratios.to_string())
    
else:
    print("\nNo se pudo calcular ningún ratio de resumen actual.")


# 5. Mostrar un ejemplo del DataFrame Histórico y Guardar Archivos Individuales
if historical_dataframes:
    print("\n\n#####################################################")
    print("--- GUARDANDO DATOS HISTÓRICOS DETALLADOS ---")
    print("#####################################################")
    
    # 5.1. Guardar cada DataFrame histórico individualmente en su carpeta de industria
    for ticker, df_hist in historical_dataframes.items():
        # Usar el mapeo Ticker a IndustryKey para determinar la ruta
        industry = ticker_to_industry.get(ticker, 'default_industry')
        
        industry_output_dir = os.path.join(OUTPUT_BASE_DIR, industry)
        os.makedirs(industry_output_dir, exist_ok=True) # Crear carpeta si no existe

        file_name_historical = f"{ticker}_historical_analysis.csv"
        output_path_historical = os.path.join(industry_output_dir, file_name_historical)
        
        df_hist.to_csv(output_path_historical)
        print(f"Éxito: Histórico de {ticker} (Industria: {industry}) guardado en: {output_path_historical}")


    # 5.2. Mostrar un ejemplo del DataFrame Histórico (para demostración)
    first_ticker = list(historical_dataframes.keys())[0]
    df_hist = historical_dataframes[first_ticker]
    
    print(f"\nEjemplo de Datos Históricos de {first_ticker} (ROE y ROIC por año):")
    # Mostramos solo las columnas clave para el histórico
    print(df_hist[['Net Income', 'Stockholders Equity', 'EBIT', 'Invested Capital', 'ROE (%)', 'ROIC (%)']].tail())
    
    print("\nNota: Todos los DataFrames históricos completos están almacenados en la carpeta 'data/processed/{industry}'.")
    
else:
    print("\nNo se generaron DataFrames históricos.")
