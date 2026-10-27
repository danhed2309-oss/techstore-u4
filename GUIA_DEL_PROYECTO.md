# Guía: qué viene en cada archivo y dónde está en el proyecto

## ¿Qué documento da las instrucciones?
- **Word (`CLN_U4_Practica_Guiada_Alumnos_TechStore.docx`)**: son las **instrucciones paso a paso** de la práctica. Es el que se sigue para hacer el trabajo.
- **PDF (`CLN_U4_Manual_Alumnos_Ilustrado.pdf`)**: es el **manual de lectura** (teoría). Explica los conceptos de la Unidad 4 y resume lo que pide la Actividad 4 (capítulo 9). Sirve para entender el porqué.
- **ZIP**: el material de trabajo (datos y cargador).

## Mapa: concepto -> manual -> práctica -> archivo
| Concepto | PDF (capítulo) | Word (sección) | Archivo del proyecto |
|---|---|---|---|
| Entidades y Value Objects (Money, OrderItem) | 2 | 6.1, 6.2, 6.3 | `app/domain.py` |
| Specification Pattern (AND/OR/NOT) | 3 | 8 | `app/specifications.py` |
| Máquina de estados | 4 | 9 | `Order` en `app/domain.py` |
| Domain Events | 5 | 9 | `DomainEvent` en `app/domain.py` |
| API REST (controlador delgado) | 6 | 11 | `app/api.py` |
| Excepciones de dominio | 7 | 6.1 | primeras clases de `app/domain.py` |
| Vibe coding y pruebas | 8 | 12 | `tests/` |
| Entregables de la actividad | 9 | 13 y 14 | todo el repositorio |
| Carga de datos | - | 5 y 7 | `cargar_csv.py` + `datos/` |
| 15 escenarios | - | 10 | `ejecutar_escenarios.py`, `BITACORA.md` |

## Archivos del ZIP original
- `cargar_csv.py`: lee los CSV y crea objetos `Customer`, `Order`, `OrderItem` y `Money`. Importa `app.domain`, por eso no funcionaba hasta crear ese módulo.
- Los 5 CSV son texto plano (Excel los abre, pero no son archivos .xlsx).
- `README.txt`: reglas del paquete.
- `__pycache__/*.pyc`: caché que genera Python; se ignora y no se sube a GitHub.

## Nota sobre los acentos
Los documentos (.md) llevan acentos. El código (.py) está escrito sin acentos a propósito,
para que no se vea mal en la terminal ni en editores con otra codificación.

## Qué falta que hagas tú
1. Revisar Python 3.11 o superior, crear el entorno virtual e instalar las dependencias (ver `README.md`).
2. Ejecutar `python cargar_csv.py` y capturar la terminal con los 16 pedidos.
3. Ejecutar `python -m pytest -q` y capturar el resultado.
4. Abrir Swagger (`uvicorn app.api:app --reload`, luego `/docs`) y probar: ID inexistente (404), confirmar O013 dos veces (200 y luego 409) y confirmar O007 (422). Capturar una operación exitosa y una rechazada.
5. Llenar a mano la tabla de la sección 5 del Word: O001 -> C001, 4 unidades, 2100.00; O006 -> C006, 1 unidad, 18000.00; O010 -> C010, 2 unidades, 500.00.
6. Escribir tu reflexión en `REPORTE.md` (tres errores reales, cómo los solucionaste y qué aprendiste).
7. Reescribir con tus palabras las 5 respuestas de `REPORTE.md`.
8. Ejecutar `python ejecutar_escenarios.py` y revisar que `BITACORA.md` coincida con lo que ves.
9. Dibujar o capturar el diagrama de estados si te lo piden como imagen (el texto está en `DIAGRAMA_ESTADOS.md`).
10. Crear el repositorio en GitHub y subir todo, sin `.venv` ni `__pycache__` (el `.gitignore` ya los excluye).
