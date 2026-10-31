"""Miniproyecto 1: la serie del grupo, de las líneas base al mejor modelo clásico.

Se corre de principio a fin con

    python miniproyecto.py

y deja las figuras en figuras/ y la tabla en resultados/metricas.csv. Las
partes marcadas con TODO las completa el grupo; mientras falten, el guion las
reporta como pendientes y sigue. El informe, docs/informe.md, cita las cifras
y las figuras que produce este guion.
"""
import itertools
import warnings

import matplotlib

matplotlib.use("Agg")
import holidays  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import matplotlib.dates as mdates
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.seasonal import STL
from statsmodels.tsa.stattools import acf, adfuller, pacf


from comun import (RAIZ, backtest, cargar_serie, estacional_ingenuo,  # noqa: E402
                   fechas_siguientes, ingenuo)

warnings.filterwarnings("ignore")
FIGURAS = RAIZ / "figuras"
RESULTADOS = RAIZ / "resultados"
FIGURAS.mkdir(exist_ok=True)
RESULTADOS.mkdir(exist_ok=True)

# ============================================================
# 1. La serie
# ============================================================
# Cambie estos cuatro datos por los de la serie del grupo y documente la
# fuente en datos/README.md. La serie de ejemplo solo sirve para probar que
# el guion corre.
ARCHIVO = "datos/trafico_vehicular_peaje_siberia.csv"
FECHA = "mes"
VALOR = "total"
PERIODO = 12
PAIS = "CO"
ESCALA = 10_000

# Lo que se hizo con los huecos y con los datos atípicos, en una línea. Va
# a la columna `decision` de la tabla de métricas.
DECISION = (
    "Sin meses faltantes; no se detectaron atípicos con el criterio 1,5 × IQR. "
    "Se conservaron los valores originales, sin corrección automática."
)

def preparar(serie):
    """Valida los huecos y conserva los valores originales de la serie.

    Rechaza series vacías o con NaN para exigir una decisión explícita.
    El criterio 1,5 × IQR se usa como diagnóstico, sin recorte automático.
    """
    if serie.empty:
        raise ValueError("La serie está vacía.")
    if serie.isna().any():
        raise ValueError(
            "La serie tiene meses faltantes. Revise los datos y documente "
            "cómo tratarlos antes de continuar."
        )

    q1, q3 = serie.quantile([0.25, 0.75])
    iqr = q3 - q1
    limite_inferior = q1 - 1.5 * iqr
    limite_superior = q3 + 1.5 * iqr
    atipicos = serie[(serie < limite_inferior) | (serie > limite_superior)]
    print(
        f"Diagnóstico IQR: Q1={q1:.2f}; Q3={q3:.2f}; IQR={iqr:.2f}; "
        f"límites=[{limite_inferior:.2f}, {limite_superior:.2f}]."
    )
    print(f"Rango observado: [{serie.min():.2f}, {serie.max():.2f}].")
    print(
        f"Atípicos según 1,5 × IQR: {len(atipicos)}; "
        "se conservan los valores originales."
    )
    return serie


def graficar_serie(serie):
    figura, eje = plt.subplots(figsize=(9, 3.4))
    eje.plot(serie.index, serie.to_numpy())
    eje.set_title("Camiones por mes/año")
    eje.set_ylabel("Número de Camiones")
    eje.set_xlabel("Mes/Año")
    eje.xaxis.set_major_locator(mdates.MonthLocator(interval=12))
    eje.xaxis.set_major_formatter(mdates.DateFormatter('%b-%Y'))
    eje.tick_params(axis='x', rotation=45)
    figura.tight_layout()
    figura.savefig(FIGURAS / "serie.png", dpi=120)
    plt.close(figura)


# ============================================================
# 2. Descomposición
# ============================================================

def descomponer(serie):
    """Genera la STL robusta y resume sus componentes en unidades originales."""
    with plt.rc_context({"figure.figsize": (8, 3.4), "font.size": 11}):
        resultado = STL(serie, period=PERIODO, robust=True).fit()
        figura = resultado.plot()
        figura.savefig(FIGURAS / "stl.png", dpi=120)
    plt.close(figura)

    tendencia = resultado.trend
    cambio = tendencia.iloc[-1] - tendencia.iloc[0]
    print(f"\nSTL robusta con periodo {PERIODO}:")
    print(
        f"Tendencia: {tendencia.index[0]:%Y-%m}={tendencia.iloc[0]:.2f}; "
        f"{tendencia.index[-1]:%Y-%m}={tendencia.iloc[-1]:.2f} vehículos."
    )
    print(
        f"Cambio de tendencia: {cambio:.2f} vehículos "
        f"({100 * cambio / tendencia.iloc[0]:.2f} %)."
    )

    nombres_meses = (
        "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
    )
    estacional_por_mes = resultado.seasonal.groupby(serie.index.month).mean()
    estacional_por_mes.index = pd.Index(
        [nombres_meses[mes - 1] for mes in estacional_por_mes.index], name="mes"
    )
    print("Componente estacional media por mes (vehículos):")
    print(estacional_por_mes.to_frame("efecto_medio").to_string(
        float_format=lambda valor: f"{valor:.2f}"
    ))

    fecha_residuo = resultado.resid.abs().idxmax()
    print(
        f"Mayor residuo absoluto: {fecha_residuo:%Y-%m}, "
        f"residuo={resultado.resid.loc[fecha_residuo]:.2f} vehículos."
    )
    print(
        f"En ese mes: observado={serie.loc[fecha_residuo]:.2f}; "
        f"tendencia={tendencia.loc[fecha_residuo]:.2f}; "
        f"estacional={resultado.seasonal.loc[fecha_residuo]:.2f}; "
        f"tendencia + estacional="
        f"{tendencia.loc[fecha_residuo] + resultado.seasonal.loc[fecha_residuo]:.2f}."
    )



# ============================================================
# 3. Estacionariedad e identificación
# ============================================================

def estacionariedad(serie):
    """Contrasta cuatro transformaciones y documenta la elección de d y D.

    Usa constante y tendencia en niveles, y constante tras diferenciar.
    Genera ACF/PACF de la diferencia regular y devuelve la decisión (1, 0).
    """
    alfa = 0.05
    escalada = serie / ESCALA
    versiones = {
        "original": (escalada, "ct"),
        "diferencia regular": (escalada.diff().dropna(), "c"),
        "diferencia estacional": (escalada.diff(PERIODO).dropna(), "c"),
        "ambas diferencias": (escalada.diff(PERIODO).diff().dropna(), "c"),
    }
    resultados_adf = {}
    for nombre, (valores, regresion) in versiones.items():
        estadistico, valor_p, rezagos, nobs = adfuller(
            valores, regression=regresion, autolag="AIC"
        )[:4]
        resultados_adf[nombre] = {
            "regression": regresion,
            "ADF": estadistico,
            "valor_p": valor_p,
            "rezagos": rezagos,
            "nobs": nobs,
            "rechaza_H0": "sí" if valor_p < alfa else "no",
        }

    tabla_adf = pd.DataFrame.from_dict(resultados_adf, orient="index")
    tabla_adf.index.name = "version"
    print(f"\nADF: H0 = No estacionaria; alfa={alfa}; autolag=AIC.")
    print(tabla_adf.to_string(formatters={
        "ADF": lambda valor: f"{valor:.4f}",
        "valor_p": lambda valor: f"{valor:.8f}",
    }))

    # Decisión del grupo para esta serie: una diferencia regular es suficiente
    # para rechazar H0; se estudia la dependencia anual con P y Q.
    # ADF no contrasta específicamente la existencia de raíces estacionales.
    if (resultados_adf["original"]["valor_p"] < alfa
            or resultados_adf["diferencia regular"]["valor_p"] >= alfa):
        raise ValueError(
            "Los resultados ADF cambiaron: revise la justificación de d=1, D=0."
        )
    d, D = 1, 0
    print(
        "Elección del grupo: d=1, D=0. La diferencia regular rechaza raíz "
        "unitaria al 5 %; se conserva como transformación inicial sin añadir "
        "una diferencia estacional. La dependencia anual se estudia con P y Q."
    )
    estacionaria = versiones["diferencia regular"][0]
    print(f"{len(estacionaria)} meses tras la diferencia regular")
    print(
        "Bandas del 95 %: ACF según Bartlett; "
        f"PACF aproximadamente ±{1.96 / np.sqrt(len(estacionaria)):.3f}."
    )
    lags = min(24, len(estacionaria) // 2 - 1)
    valores_acf, intervalos_acf = acf(
        estacionaria, nlags=lags, alpha=alfa, fft=False, bartlett_confint=True
    )
    valores_pacf, intervalos_pacf = pacf(
        estacionaria, nlags=lags, alpha=alfa, method="ywm"
    )
    for nombre, valores, intervalos in (
        ("ACF", valores_acf, intervalos_acf),
        ("PACF", valores_pacf, intervalos_pacf),
    ):
        fuera = (intervalos[1:, 0] > 0) | (intervalos[1:, 1] < 0)
        significativos = pd.DataFrame({
            "rezago": np.arange(1, lags + 1)[fuera],
            "coeficiente": valores[1:][fuera],
        })
        print(f"{nombre}: rezagos fuera de las bandas del 95 % (sin rezago 0):")
        print(significativos.to_string(
            index=False, float_format=lambda valor: f"{valor:.4f}"
        ))

    figura, ejes = plt.subplots(1, 2, figsize=(11, 3.4))
    plot_acf(
        estacionaria, lags=lags, ax=ejes[0], title="ACF", alpha=alfa,
        fft=False, bartlett_confint=True
    )
    plot_pacf(
        estacionaria, lags=lags, ax=ejes[1], title="PACF", alpha=alfa, method="ywm"
    )
    figura.tight_layout()
    figura.savefig(FIGURAS / "acf_pacf.png", dpi=120)
    plt.close(figura)
    return d, D




# ============================================================
# 4. Modelos clásicos
# ============================================================
# Cada modelo es una función modelo(entrenamiento, h) que devuelve h
# pronósticos y solo usa `entrenamiento`. Así entra al backtest común.

def elegir_sarima(serie, d, D):
    """Selecciona una rejilla SARIMA por AIC y diagnostica sus residuos.

    Ajusta con toda la serie preparada y corrige Ljung-Box por p+q+P+Q.
    Guarda figuras/residuos.png y devuelve los órdenes elegidos.
    """
    escalada = serie / ESCALA

    resultados = []
    fallos = []
    for p, q, P, Q in itertools.product([0, 1], repeat=4):
        orden = (p, d, q)
        orden_estacional = (P, D, Q, PERIODO)
        try:
            ajuste = ARIMA(
                escalada,
                order=orden,
                seasonal_order=orden_estacional,
            ).fit()
        except (ValueError, np.linalg.LinAlgError) as error:
            fallos.append((orden, orden_estacional, error))
            continue
        resultados.append({
            "order": orden,
            "seasonal_order": orden_estacional,
            "AIC": ajuste.aic,
            "converged": ajuste.mle_retvals.get("converged", True),
            "fit": ajuste,
        })

    if not resultados:
        raise RuntimeError("No se pudo ajustar ningún modelo de la rejilla SARIMA.")

    rejilla = pd.DataFrame([
        {clave: valor for clave, valor in resultado.items() if clave != "fit"}
        for resultado in resultados
    ]).sort_values("AIC")
    print(f"Rejilla SARIMA sobre serie / {ESCALA:g}, con d={d} y D={D}:")
    print(rejilla.to_string(index=False, float_format=lambda valor: f"{valor:.2f}"))
    if fallos:
        print(f"Modelos que no se pudieron ajustar: {len(fallos)}")
        for orden, orden_estacional, error in fallos:
            print(f"  {orden} x {orden_estacional}: {type(error).__name__}: {error}")
    
    candidatos = [
        resultado for resultado in resultados
        if resultado["converged"] and np.isfinite(resultado["AIC"])
    ]
    if not candidatos:
        raise RuntimeError("Ningún modelo SARIMA convergió con AIC finito.")

    mejor = min(candidatos, key=lambda resultado: resultado["AIC"])
    orden = mejor["order"]
    orden_estacional = mejor["seasonal_order"]
    ajuste = mejor["fit"]
    residuos = ajuste.resid.iloc[d + PERIODO * D:]
    grados_modelo = orden[0] + orden[2] + orden_estacional[0] + orden_estacional[2]
    lags_ljung_box = [
        lag for lag in (12, 24) if grados_modelo < lag < len(residuos)
    ]
    if not lags_ljung_box:
        raise ValueError(
            "No hay rezagos válidos para Ljung-Box: deben superar los grados "
            "de libertad del modelo y ser menores que el número de residuos."
        )

    print(f"\nModelo elegido: {orden} x {orden_estacional}")
    print(ajuste.summary())
    alfa = 0.05
    diagnostico = acorr_ljungbox(
        residuos, lags=lags_ljung_box, model_df=grados_modelo, return_df=True
    )
    diagnostico.insert(0, "gl", diagnostico.index - grados_modelo)
    diagnostico["rechaza_H0"] = np.where(diagnostico["lb_pvalue"] < alfa, "sí", "no")
    print(
        f"\nLjung-Box: {len(residuos)} residuos; "
        f"model_df=p+q+P+Q={grados_modelo}; gl=rezago-model_df."
    )
    print(f"H0: sin autocorrelación hasta el rezago evaluado; alfa={alfa}.")
    print(diagnostico.to_string(float_format=lambda valor: f"{valor:.6f}"))
    if (diagnostico["lb_pvalue"] < alfa).any():
        print(
            "Se rechaza H0 en al menos un rezago: persiste autocorrelación "
            "residual. El mínimo AIC de la rejilla no garantiza ruido blanco."
        )
    else:
        print("No se rechaza H0 en los rezagos evaluados al 5 %.")

    lags_grafica = min(24, len(residuos) // 2)
    figura = ajuste.plot_diagnostics(lags=lags_grafica, figsize=(10, 8))
    figura.tight_layout()
    figura.savefig(FIGURAS / "residuos.png", dpi=120)
    plt.close(figura)
    return orden, orden_estacional



def modelo_sarima(orden, orden_estacional):
    """TODO: devuelva la función modelo(entrenamiento, h) del SARIMA elegido."""
    def pronosticar(entrenamiento, h):
        ajuste = ARIMA(
            entrenamiento / ESCALA,
            order=orden,
            seasonal_order=orden_estacional,
        ).fit()
        return ajuste.forecast(steps=h).to_numpy() * ESCALA

    return pronosticar


def exogenas(serie):
    """TODO: DataFrame de variables conocidas de antemano, con el índice de la serie.

    Por ejemplo, el número de festivos o de días hábiles de cada mes. Debe
    cubrir también los 12 meses que siguen al final de la serie.
    """
    anios = range(serie.index[0].year, serie.index[-1].year + 2)
    indice = pd.date_range(
        serie.index[0], periods=len(serie) + PERIODO, freq="MS"
    )
    calendario_festivos = holidays.country_holidays(PAIS, years=anios)
    fechas_festivos = pd.to_datetime(list(calendario_festivos.keys()))
    conteo_mensual = (
        pd.Series(1, index=fechas_festivos)
        .resample("MS")
        .sum()
        .reindex(indice, fill_value=0)
        .astype(float)
        .rename("festivos")
    )
    return conteo_mensual.to_frame()



def modelo_sarimax(orden, orden_estacional, x):
    """TODO: devuelva modelo(entrenamiento, h) de un SARIMAX con exógenas x.

    Use x.loc[entrenamiento.index] para ajustar y
    x.loc[fechas_siguientes(entrenamiento, h)] para pronosticar.
    """
    def pronosticar(entrenamiento, h):
        fechas_futuras = fechas_siguientes(entrenamiento, h)
        exog_entrenamiento = x.loc[entrenamiento.index]
        exog_futuras = x.loc[fechas_futuras]
        ajuste = ARIMA(
            entrenamiento / ESCALA,
            order=orden,
            seasonal_order=orden_estacional,
            exog=exog_entrenamiento,
        ).fit()
        return ajuste.forecast(steps=h, exog=exog_futuras).to_numpy() * ESCALA

    return pronosticar
# ============================================================
# 5. La tabla de métricas
# ============================================================

def fila(nombre, serie, modelo):
    _, promedio = backtest(serie, modelo)
    return {"modelo": nombre, "decision": DECISION,
            "RMSE": round(promedio["RMSE"], 2), "MAE": round(promedio["MAE"], 2),
            "MAPE": round(promedio["MAPE"], 2)}


def pendiente(parte, error):
    print(f"  pendiente: {parte} ({error})")


def main():
    cruda = cargar_serie(ARCHIVO, FECHA, VALOR)
    print(f"Serie: {len(cruda)} meses, de {cruda.index[0]:%Y-%m} a "
          f"{cruda.index[-1]:%Y-%m}, {cruda.isna().sum()} vacíos")
    serie = preparar(cruda)
    graficar_serie(serie)

    filas = [fila("ingenuo", serie, ingenuo),
             fila("estacional ingenuo", serie,
                  lambda t, h: estacional_ingenuo(t, h, PERIODO))]

    try:
        descomponer(serie)
    except NotImplementedError as error:
        pendiente("parte 2", error)

    try:
        d, D = estacionariedad(serie)
    except NotImplementedError as error:
        pendiente("parte 3", error)
        d = D = None

    if d is not None:
        try:
            orden, estacional = elegir_sarima(serie, d, D)
            filas.append(fila(f"SARIMA{orden}{estacional}", serie,
                              modelo_sarima(orden, estacional)))
            x = exogenas(serie)
            filas.append(fila(f"SARIMAX{orden}{estacional} + exógenas", serie,
                              modelo_sarimax(orden, estacional, x)))
        except NotImplementedError as error:
            pendiente("parte 4", error)

    tabla = pd.DataFrame(filas).sort_values("RMSE")
    tabla.to_csv(RESULTADOS / "metricas.csv", index=False)
    print(tabla.drop(columns="decision").to_string(index=False))
    print("Mejor modelo por RMSE:", tabla.iloc[0]["modelo"])


if __name__ == "__main__":
    main()
