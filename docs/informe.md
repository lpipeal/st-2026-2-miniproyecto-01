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

Se aplicó una descomposición STL aditiva con periodo de 12 meses y ajuste
robusto (`robust=True`). La serie se expresa como:

$$
y_t = T_t + S_t + R_t,
$$

donde $T_t$ es la tendencia, $S_t$ la componente estacional y $R_t$ el
residuo. Las tres componentes se expresan en vehículos por mes.

La tendencia muestra un crecimiento de largo plazo: pasa de **67.411,64
vehículos en enero de 2014 a 104.681,43 en mayo de 2026**, un aumento de
37.269,79 vehículos, equivalente al **55,29 %** del nivel inicial estimado.
El crecimiento no es uniforme: la curva presenta una mayor pendiente
alrededor de 2019–2021 y variaciones más moderadas desde 2022.

Para resumir la estacionalidad se promedió la componente $S_t$ de cada mes
del calendario sobre los años disponibles. Un efecto positivo se suma al
nivel de tendencia y uno negativo lo reduce:

| Mes | Efecto estacional medio (vehículos) |
|---|---:|
| Enero | −2.450,31 |
| Febrero | −5.441,71 |
| Marzo | −91,21 |
| Abril | −1.834,54 |
| Mayo | +1.696,45 |
| Junio | −4.598,51 |
| Julio | +1.573,85 |
| Agosto | +904,56 |
| Septiembre | +2.427,20 |
| Octubre | +4.405,89 |
| Noviembre | +1.426,12 |
| Diciembre | +2.429,05 |

**Octubre tiene el mayor efecto estacional medio y febrero el menor**;
junio también presenta una reducción marcada respecto de la tendencia.
Estos valores resumen la componente estimada, cuyo efecto puede cambiar
entre años. Enero a mayo cuentan con 13 observaciones por mes y los demás
meses con 12, porque la muestra termina en mayo de 2026.

El **mayor residuo en valor absoluto corresponde a abril de 2020**, con
$R_t=-14\,007{,}81$ vehículos. Ese mes se observaron 68.302 vehículos,
frente a una tendencia estimada de 85.243,04 y un efecto estacional de
−2.933,23. La suma de tendencia y estacionalidad fue 82.309,81 vehículos;
el dato observado quedó 14.007,81 por debajo de esa suma.
Este residuo mide la desviación respecto de los componentes estimados por
STL. Su magnitud muestra que puede existir un mes inusual en su contexto
temporal debido a la pandemia.

## 3. Líneas base y backtest

{{Cómo es el backtest: cuántos orígenes, horizonte y qué meses quedan en la
prueba. Por qué ningún dato posterior al origen entra al modelo.}}

{{RMSE, MAE y MAPE del ingenuo y del estacional ingenuo, y cuál gana.}}

## 4. Estacionariedad e identificación

Se aplicó la prueba Dickey–Fuller aumentada (ADF) a la serie original y a
tres transformaciones, con un nivel de significancia del 5 %. La hipótesis
nula $H_0$ es que es estacionaria; se rechaza cuando el valor p es
menor que 0,05. No rechazar $H_0$ no demuestra que la raíz exista, pero
indica que esta prueba no aporta evidencia suficiente para descartarla.

Las transformaciones comparadas fueron la diferencia regular
$\Delta y_t=y_t-y_{t-1}$, la diferencia estacional
$\Delta_{12}y_t=y_t-y_{t-12}$ y su combinación
$\Delta\Delta_{12}y_t$. Los primeros valores ausentes producidos por cada
diferencia se retiraron antes de aplicar ADF. El cálculo se realizó sobre
la serie dividida por 10.000, igual que en los modelos; este cambio de
unidad no modifica la decisión sobre la hipotesis nula.

En niveles se usó `regression="ct"`, con constante y tendencia lineal,
porque la gráfica y STL muestran crecimiento de largo plazo. En las
versiones diferenciadas se usó `regression="c"`: se permite una media
distinta de cero tras diferenciar y no se añade una tendencia lineal
determinista a los cambios. Los rezagos auxiliares se seleccionaron con
`autolag="AIC"`, dentro del máximo predeterminado de la biblioteca. Estos
parámetros y la hipótesis del contraste se describen en la
[documentación de ADF en statsmodels](https://www.statsmodels.org/stable/generated/statsmodels.tsa.stattools.adfuller.html).

| Versión | `regression` | Estadístico ADF | Valor p | Rezagos ADF | Observaciones efectivas | Rechaza $H_0$ al 5 % |
|---|---|---:|---:|---:|---:|---|
| Original | `ct` | −1,9617 | 0,62214390 | 13 | 135 | No |
| Diferencia regular | `c` | −3,8263 | 0,00264947 | 11 | 136 | Sí |
| Diferencia estacional | `c` | −2,4295 | 0,13358578 | 13 | 123 | No |
| Ambas diferencias | `c` | −4,8596 | 0,00004176 | 13 | 122 | Sí |

La columna de observaciones efectivas descuenta tanto la diferenciación
como las observaciones necesarias para la regresión ADF y sus rezagos.
Por ello, no equivale a la longitud de cada versión de la serie.

Se eligió **$d=1$ y $D=0$ como especificación inicial**. La prueba no
rechaza hipotesis nula en niveles y sí la rechaza después de una diferencia
regular. La diferencia estacional sola no logra ese rechazo. Ambas
diferencias también lo logran, pero su menor valor p no convierte esa
transformación en un mejor modelo: una diferencia regular ya proporciona
evidencia contra la no estacionariedad y conserva 148 observaciones, frente a
136 al aplicar ambas.
La ADF utilizada no es un contraste específico de raíces estacionales y
su rechazo no demuestra por sí solo todas las condiciones de
estacionariedad. Por ello, **$D=0$ es una decisión de modelado que se
contrasta después con el ajuste y los residuos**. La dependencia anual
que permanezca se estudia mediante los términos estacionales $P$ y $Q$
del SARIMA; no se interpreta $D=0$ como ausencia de estacionalidad.

![ACF y PACF](../figuras/acf_pacf.png)

La figura corresponde a la diferencia regular, con 148 observaciones,
desde febrero de 2014 hasta mayo de 2026, y muestra los primeros 24
rezagos. Se usaron bandas del 95 % calculadas con Bartlett para la ACF y
una PACF estimada por Yule–Walker sin ajuste (`method="ywm"`), con banda
aproximada de $\pm1{,}96/\sqrt{148}=\pm0{,}161$. Las bandas ACF varían
según el rezago; no se les aplica ese mismo umbral constante. Las opciones
se detallan en la documentación de
[ACF](https://www.statsmodels.org/stable/generated/statsmodels.graphics.tsaplots.plot_acf.html)
y [PACF](https://www.statsmodels.org/stable/generated/statsmodels.graphics.tsaplots.plot_pacf.html).

Los coeficientes que salen de las bandas, excluido el rezago cero, son:

| Rezago | ACF fuera de banda | PACF fuera de banda |
|---:|---:|---:|
| 1 | −0,5250 | −0,5250 |
| 2 | — | −0,2307 |
| 4 | −0,2326 | −0,1878 |
| 8 | — | −0,2110 |
| 11 | — | −0,1843 |
| 12 | +0,3904 | +0,2788 |
| 13 | −0,2976 | — |

El guion indica los mismos rezagos y coeficientes. Una raya significa que
el coeficiente queda dentro de la banda de esa función.

El pico negativo de la ACF en el rezago 1 sugiere incluir un término MA(1)
entre los candidatos. El pico anual en el rezago 12 de ambas funciones
motiva explorar términos AR y MA estacionales. Los picos adicionales no
permiten identificar un único orden de forma concluyente; se propone la
rejilla pequeña $p,q,P,Q\in\{0,1\}$, manteniendo $d=1$, $D=0$ y periodo
12, para comparar las combinaciones por AIC y revisar sus residuos.
Estas bandas se usan como guía exploratoria, no como una selección
automática del modelo.

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
