# App Pedidos Negocio

Aplicación web para generar órdenes operativas por proveedor con login.

## Flujo
- Pantalla de ingreso con usuario y contraseña.
- Selección de proveedor: `El Rodeo`, `Todito`, `Pricemart`.
- Búsqueda por nombre (autocompletado) sin mostrar lista completa.
- Al seleccionar producto, se agrega a la captura y a la vista previa al mismo tiempo.
- Campos de línea iguales al formato PDF:
  - `Cantidad`
  - `Producto (Descripción Exacta del Proveedor)`
  - `Notas`
- Historial de pedidos y exportación CSV.

## Credenciales por defecto
- Usuario: `admin`
- Contraseña: `gpfSmiguel`

Puedes cambiarlas con variables de entorno:
- `APP_USERNAME`
- `APP_PASSWORD`
- `SESSION_SECRET`

## Ejecutar local
1. Crear y activar entorno virtual:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
2. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```
3. Ejecutar:
   ```bash
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
4. Abrir:
   ```
   http://127.0.0.1:8000
   ```

## Catálogo
- Archivo: `data/products.csv`
- `El Rodeo` y `Todito` fueron cargados desde tus PDFs.
- `Pricemart` quedó con catálogo inicial editable hasta recibir su formato final.

## Despliegue en Render
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
