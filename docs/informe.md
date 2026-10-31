# Informe del miniproyecto 1

Llene cada sección reemplazando los marcadores `{{...}}`, sin quitar las
secciones. Las cifras salen de lo que imprime `python miniproyecto.py` y las
figuras son las que ese guion deja en `figuras/`. Las fórmulas van en LaTeX
(`$...$` o `$$...$$`).

## 1. La serie

{{Qué mide la serie, de dónde sale (fuente y licencia), frecuencia, periodo y
número de observaciones. Por qué el grupo la eligió.}}

![La serie](../figuras/serie.png)

La revisión del calendario mensual, de enero de 2014 a mayo de 2026, mostró
149 observaciones y ningún mes faltante. Por ello, no fue necesario imputar
ni interpolar datos. La función `preparar` verifica que la serie no esté
vacía ni contenga valores ausentes; si los encuentra, detiene la ejecución
para exigir una decisión explícita sobre su tratamiento.

Para identificar posibles datos atípicos se aplicó el criterio de
$1{,}5\times IQR$ a los valores originales, donde:

$$
IQR = Q_3 - Q_1, \qquad
L_{\mathrm{inf}} = Q_1 - 1{,}5\,IQR, \qquad
L_{\mathrm{sup}} = Q_3 + 1{,}5\,IQR.
$$

Se obtuvo $Q_1=75\,367$, $Q_3=101\,146$ e $IQR=25\,779$ vehículos.
Los límites fueron 36.698,5 y 139.814,5 vehículos. El mínimo observado fue
60.922 y el máximo 112.471; ningún valor quedó fuera de los límites, por
lo que se detectaron **cero atípicos según este criterio**.

El IQR se calculó sobre toda la serie y no considera su orden temporal:
este resultado no descarta meses inusuales respecto de la tendencia o la
estacionalidad, que se examinan mediante la descomposición y los residuos.

La decisión aplicada en `preparar` coincide con el texto de `DECISION`,
que se incluye en la columna `decision` de la tabla de métricas:

> Sin meses faltantes; no se detectaron atípicos con el criterio 1,5 × IQR.
> Se conservaron los valores originales, sin corrección automática.

## 2. Componentes

![STL](../figuras/stl.png)

{{Lectura de la descomposición STL: cómo es la tendencia, qué meses quedan
arriba y abajo en la estacional y con cuánto, y dónde está el residuo más
grande.}}

## 3. Líneas base y backtest

{{Cómo es el backtest: cuántos orígenes, horizonte y qué meses quedan en la
prueba. Por qué ningún dato posterior al origen entra al modelo.}}

{{RMSE, MAE y MAPE del ingenuo y del estacional ingenuo, y cuál gana.}}

## 4. Estacionariedad e identificación

{{Valor p de la prueba ADF para la serie, su diferencia regular, la
estacional y las dos juntas. El d y el D elegidos.}}

![ACF y PACF](../figuras/acf_pacf.png)

{{Qué rezagos salen de las bandas y qué órdenes sugieren.}}

## 5. Modelos clásicos

{{La rejilla de órdenes y su AIC. El modelo elegido, escrito con su
ecuación.}}

![Residuos](../figuras/residuos.png)

{{Diagnóstico de los residuos: Ljung-Box y lo que muestran la gráfica y su
ACF.}}

{{La variable exógena: qué es, por qué se conoce de antemano y si mejora al
SARIMA.}}

## 6. Tabla de métricas

{{Copie aquí `resultados/metricas.csv` como tabla de Markdown, ordenada por
RMSE.}}

| Modelo | Decisión | RMSE | MAE | MAPE (%) |
|---|---|---|---|---|
| {{...}} | {{...}} | {{...}} | {{...}} | {{...}} |

## 7. Conclusión

{{El mejor modelo clásico, cuánto mejora a la mejor línea base en cada
métrica y en qué meses o tramos sigue fallando. Es el modelo que el
miniproyecto 2 debe superar.}}
