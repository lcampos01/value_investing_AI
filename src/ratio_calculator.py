import pandas as pd
import json
import os

# --- 1. CONFIGURACIÓN DE ARCHIVOS Y RUTAS ---
# Usamos un marcador de posición {ticker} para construir las rutas de los archivos
# Asumimos que los archivos están en la misma carpeta que el script para este ejemplo.
FILE_PATTERN = './data/raw/{ticker}_{type}.json'
TICKERS_TO_ANALYZE = ['AAPL', 'MSFT', 'GOOGL'] # Ejemplo de tickers si tuvieras más archivos


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
        return None, None

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
    
    if market_cap is None or current_price is None:
        # Devolvemos el histórico pero con un error en el resumen actual
        return {'Error': 'Market Cap o Precio actual no disponible.'}, df_combined.copy()

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
        # Ratios de rentabilidad (último año)
        'ROE (%)': last_period_data['ROE (%)'],
        'ROIC (%)': last_period_data['ROIC (%)'],
        # Ratios de Valoración (Usan precio de mercado actual)
        'PER (Price/EPS)': current_price / diluted_eps if diluted_eps != 0 else float('inf'),
        'EV/EBIT': EV / ebit if ebit != 0 else float('inf'),
        'EV/EBITDA': EV / ebitda if ebitda != 0 else float('inf'),
        'EV/FCF': EV / fcf if fcf != 0 else float('inf'),
    }
    
    # Retornamos el resumen actual y la tabla histórica (copia para evitar modificar el original)
    return pd.Series(results_current), df_combined.copy()

def analyze_ticker(ticker):
    """
    Función principal para cargar, consolidar y analizar los datos de una única empresa (ticker).
    """
    print(f"\n--- Procesando {ticker} ---")
    
    # 1. Definir rutas de archivo
    financials_path = FILE_PATTERN.format(ticker=ticker, type='financials')
    balance_path = FILE_PATTERN.format(ticker=ticker, type='balance_sheet')
    cashflow_path = FILE_PATTERN.format(ticker=ticker, type='cashflow')
    info_path = FILE_PATTERN.format(ticker=ticker, type='info')

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
        # Retorna None para el resumen actual y None para el histórico
        return None, None

    try:
        with open(info_path, 'r') as f:
            info_data = json.load(f)
    except FileNotFoundError:
        print(f"Advertencia: Archivo INFO no encontrado para {ticker}.")
        return None, None

    # 3. Consolidar (Solo las filas completas son críticas para ratios)
    df_combined = pd.concat([df_financials, df_balance, df_cashflow], axis=1).dropna(
        subset=['Net Income', 'Stockholders Equity', 'EBIT', 'EBITDA', 'Free Cash Flow']
    )
    
    if df_combined.empty:
        print(f"Advertencia: No hay períodos completos de datos para {ticker}.")
        return None, None

    # 4. Calcular y obtener ratios del último período
    ratios_series, df_historical = calculate_ratios(df_combined, info_data, ticker)
    
    if ratios_series is not None and isinstance(ratios_series, pd.Series):
        ratios_series.name = ticker # Asignar el ticker como nombre de la Serie
        return ratios_series, df_historical
    else:
        print(f"Error al calcular ratios de mercado para {ticker}: {ratios_series.get('Error', 'Error desconocido')}")
        return None, df_historical


# --- 3. Bucle Principal para Múltiples Empresas ---

# Simulamos la detección de Tickers basándonos en los archivos cargados.
# Si solo tienes los archivos de AAPL, forzamos el análisis de AAPL.
if 'AAPL_financials.json' in os.listdir():
    TICKERS_TO_ANALYZE = ['AAPL']
elif 'AAPL' not in TICKERS_TO_ANALYZE:
    TICKERS_TO_ANALYZE.append('AAPL')


all_ratios = []
historical_dataframes = {} # Diccionario para almacenar los DataFrames históricos

for ticker in TICKERS_TO_ANALYZE:
    result_current, df_historical = analyze_ticker(ticker)
    
    if result_current is not None:
        all_ratios.append(result_current)
    
    if df_historical is not None:
        # Almacenar el DataFrame histórico con el Ticker como clave
        historical_dataframes[ticker] = df_historical

# 4. Crear el DataFrame de Resultados Finales
if all_ratios:
    df_final_ratios = pd.DataFrame(all_ratios)
    df_final_ratios.index.name = 'Ticker' # El índice es el nombre del Ticker
    
    # Formatear el DataFrame para una visualización limpia
    # Convertir a miles de millones (B) y formatear
    df_final_ratios['Market Cap'] = (df_final_ratios['Market Cap'] / 1e9).round(2).apply(lambda x: f"{x:,.2f}B")
    df_final_ratios['EV'] = (df_final_ratios['EV'] / 1e9).round(2).apply(lambda x: f"{x:,.2f}B")
    
    # Redondeo final de los ratios
    for col in ['ROE (%)', 'ROIC (%)', 'PER (Price/EPS)', 'EV/EBIT', 'EV/EBITDA', 'EV/FCF']:
        df_final_ratios[col] = df_final_ratios[col].apply(lambda x: f"{x:.2f}" if x != float('inf') else 'N/A')

    print("\n\n#######################################################")
    print("--- TABLA CONSOLIDADA: RESUMEN DE RATIOS ACTUALES ---")
    print("#######################################################")
    print("\nEstos ratios usan el precio de mercado actual y datos del último reporte:")
    print(df_final_ratios.to_string())
    
else:
    print("\nNo se pudo calcular ningún ratio de resumen actual.")


# 5. Mostrar un ejemplo del DataFrame Histórico (para demostración)
if historical_dataframes:
    print("\n\n#####################################################")
    print("--- EJEMPLO: DATOS HISTÓRICOS DETALLADOS ---")
    print("#####################################################")
    
    # Mostrar el DataFrame histórico de la primera empresa
    first_ticker = list(historical_dataframes.keys())[0]
    df_hist = historical_dataframes[first_ticker]
    
    print(f"\nDatos Históricos de {first_ticker} (ROE y ROIC por año):")
    # Mostramos solo las columnas clave para el histórico
    print(df_hist[['Net Income', 'Stockholders Equity', 'EBIT', 'Invested Capital', 'ROE (%)', 'ROIC (%)']].tail())
    
    print("\nNota: Todos los DataFrames históricos completos están almacenados en el diccionario 'historical_dataframes'.")
    
else:
    print("\nNo se generaron DataFrames históricos.")
