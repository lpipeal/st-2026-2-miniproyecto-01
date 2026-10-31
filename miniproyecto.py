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
    """TODO: aplique la decisión del grupo sobre huecos y datos atípicos.

    Por ejemplo, interpolar los meses vacíos o recortar el tramo afectado.
    Debe devolver una serie sin NaN.
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
    """TODO: STL robusta con el periodo de la serie; guarde figuras/stl.png."""
    raise NotImplementedError("descomposición STL")


# ============================================================
# 3. Estacionariedad e identificación
# ============================================================

def estacionariedad(serie):
    """TODO: ADF sobre la serie, su diferencia regular, la estacional y las dos.

    Imprima el valor p de cada versión, elija d y D, y guarde la ACF y la
    PACF de la serie elegida en figuras/acf_pacf.png. Devuelva (d, D).
    """
    d, D = 1, 0
    escalada = serie / ESCALA
    estacionaria = escalada.copy()
    if D == 1:
        estacionaria = estacionaria.diff(PERIODO)
    if d == 1:
        estacionaria = estacionaria.diff()
    estacionaria = estacionaria.dropna()
    print(f"{len(estacionaria)} meses en la serie estacionaria")
    print(f"banda de confianza: ±{1.96 / np.sqrt(len(estacionaria)):.3f}")
    lags = min(24, len(estacionaria) // 2 - 1)
    figura, ejes = plt.subplots(1, 2, figsize=(11, 3.4))
    plot_acf(estacionaria, lags=lags, ax=ejes[0], title="ACF")
    plot_pacf(estacionaria, lags=lags, ax=ejes[1], title="PACF")
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
    """TODO: rejilla pequeña de órdenes (p, q, P, Q) comparada por AIC.

    Ajuste con toda la serie preparada, imprima la tabla de AIC, revise los
    residuos del elegido con Ljung-Box y guarde figuras/residuos.png.
    Devuelva el orden y el orden estacional elegidos.
    """
    raise NotImplementedError("selección del SARIMA")


def modelo_sarima(orden, orden_estacional):
    """TODO: devuelva la función modelo(entrenamiento, h) del SARIMA elegido."""
    raise NotImplementedError("SARIMA en el backtest")


def exogenas(serie):
    """TODO: DataFrame de variables conocidas de antemano, con el índice de la serie.

    Por ejemplo, el número de festivos o de días hábiles de cada mes. Debe
    cubrir también los 12 meses que siguen al final de la serie.
    """
    raise NotImplementedError("variables exógenas")


def modelo_sarimax(orden, orden_estacional, x):
    """TODO: devuelva modelo(entrenamiento, h) de un SARIMAX con exógenas x.

    Use x.loc[entrenamiento.index] para ajustar y
    x.loc[fechas_siguientes(entrenamiento, h)] para pronosticar.
    """
    raise NotImplementedError("SARIMAX en el backtest")


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
