Fórmulas de Ratios para Value Investing

Estos ratios se utilizan comúnmente en el análisis fundamental para determinar el valor y la salud financiera de una empresa.

1. Rentabilidad sobre Fondos Propios (ROE)

El ROE mide la capacidad de una empresa para generar beneficios con el dinero que los accionistas han invertido.

Fórmula:


$$\text{ROE} = \frac{\text{Beneficio Neto (Net Income)}}{\text{Patrimonio Neto (Total Stockholders Equity)}}$$

Origen de Datos:

Beneficio Neto: AAPL_financials.json (Net Income)

Patrimonio Neto: AAPL_balance_sheet.json (Stockholders Equity)

2. Retorno de la Inversión (ROI)

Aunque a menudo se confunde con el ROIC (Return on Invested Capital), usaremos el término ROI en el contexto más amplio de yFinance como el Retorno sobre el Capital Invertido (ROIC), que mide qué tan bien utiliza el capital invertido (deuda + patrimonio) para generar beneficios.

Fórmula:


$$\text{ROIC} \approx \frac{\text{EBIT} \times (1 - \text{Tasa Impositiva})}{\text{Capital Invertido (Invested Capital)}}$$

Origen de Datos:

EBIT: AAPL_financials.json (EBIT)

Tasa Impositiva: AAPL_financials.json (Tax Provision / Pretax Income)

Capital Invertido: AAPL_balance_sheet.json (Invested Capital)

3. Ratio Precio/Beneficios (PER)

El PER (Price-to-Earnings Ratio) es uno de los ratios más populares y compara el precio de la acción con los beneficios que genera la empresa.

Fórmula (utilizando datos del archivo info y financials):


$$\text{PER} = \frac{\text{Precio por Acción (Share Price)}}{\text{BPA (Earnings Per Share, Diluted EPS)}}$$

Origen de Datos:

Precio por Acción (Price): AAPL_info.json (currentPrice)

BPA (EPS): AAPL_financials.json (Diluted EPS)

Nota: Para el PER, utilizaremos los datos más recientes disponibles en AAPL_info.json y el último año de AAPL_financials.json.

4. EV/EBIT (Enterprise Value / Earnings Before Interest and Taxes)

Este ratio es una métrica de valoración superior al PER porque considera tanto la deuda como el efectivo de la empresa (Enterprise Value, EV) y utiliza el EBIT, que es independiente de la estructura de capital y los impuestos.

Fórmula:


$$\text{EV} = \text{Market Cap (Capitalización Bursátil)} + \text{Deuda Total (Total Debt)} - \text{Efectivo y Equivalentes (Cash and Equivalents)}$$

$$\text{EV/EBIT} = \frac{\text{EV}}{\text{EBIT}}$$

Origen de Datos:

Market Cap: AAPL_info.json (marketCap)

Deuda Total: AAPL_balance_sheet.json (Total Debt)

Efectivo: AAPL_balance_sheet.json (Cash And Cash Equivalents)

EBIT: AAPL_financials.json (EBIT)

5. EV/EBITDA (Enterprise Value / Earnings Before Interest, Taxes, Depreciation and Amortization)

Similar al EV/EBIT, pero añade la depreciación y amortización, lo que resulta útil para comparar empresas con diferentes políticas de depreciación.

Fórmula:


$$\text{EV/EBITDA} = \frac{\text{EV}}{\text{EBITDA}}$$

Origen de Datos:

EV: Calculado anteriormente (Market Cap + Total Debt - Cash).

EBITDA: AAPL_financials.json (EBITDA)

6. EV/FCF (Enterprise Value / Free Cash Flow)

Mide cuántos años de Flujo de Caja Libre (FCF) se necesitarían para pagar el Enterprise Value de la empresa. Es excelente para ver la capacidad de la empresa de generar efectivo real después de cubrir sus gastos de capital.

Fórmula:


$$\text{EV/FCF} = \frac{\text{EV}}{\text{FCF (Free Cash Flow)}}$$

Origen de Datos:

EV: Calculado anteriormente (Market Cap + Total Debt - Cash).

FCF: AAPL_cashflow.json (Free Cash Flo