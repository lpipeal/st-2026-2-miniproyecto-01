# datos

La serie del grupo vive en esta carpeta, en CSV. La ficha siguiente la
identifica y documenta de dónde sale.

| Campo | Valor |
|---|---|
| Archivo | `trafico_vehicular_peaje_siberia.csv` |
| Qué mide | Vehículos que pasaron cada mes por el peaje Siberia, en el corredor Bogotá–Medellín, sumando las categorías tarifarias III a VII |
| Fuente | Agencia Nacional de Infraestructura (ANI), conjunto *Tráfico Vehicular ANI*, registros del peaje Siberia. Datos Abiertos Colombia: <https://www.datos.gov.co/d/8yi9-t44c> |
| Licencia | Creative Commons Atribución-CompartirIgual 4.0 Internacional (CC BY-SA 4.0) |
| Frecuencia | mensual |
| Periodo | enero de 2014 a mayo de 2026 (149 observaciones) |
| Columna de fecha | `mes` (primer día del mes) |
| Columna que se pronostica | `total` (número de vehículos en el mes) |

## Cómo se construyó el archivo

El CSV se descargó de la API Socrata de Datos Abiertos Colombia con una
consulta que agrega por mes la suma de `cantidadtrafico` de las categorías
III a VII del peaje Siberia:

```text
https://www.datos.gov.co/resource/8yi9-t44c.csv
  ?$select=date_trunc_ym(desde) as mes, sum(cantidadtrafico) as total
  &$where=peaje='SIBERIA' and categoriatarifa in('III','IV','V','VI','VII')
  &$group=mes
  &$order=mes
```

La consulta devuelve una fila por mes con dos columnas, `mes` y `total`, y
cubre exactamente el periodo 2014-01 a 2026-05 que usa el guion.
