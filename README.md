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

## WhatsApp Business / Meta Cloud API
La app incluye un webhook para recibir mensajes de WhatsApp y convertirlos en pedidos:

- URL del webhook: `https://TU-DOMINIO/api/whatsapp/webhook`
- Metodo de verificacion de Meta: `GET`
- Recepcion de mensajes: `POST`

Variables de entorno necesarias:

- `WHATSAPP_VERIFY_TOKEN`: texto secreto que tambien colocas en Meta al configurar el webhook.
- `WHATSAPP_APP_SECRET`: App Secret de la app de Meta, usado para validar firmas de webhooks.
- `WHATSAPP_PHONE_NUMBER_ID`: ID interno del numero de WhatsApp en Meta.
- `WHATSAPP_ACCESS_TOKEN`: token permanente de System User con permisos de WhatsApp.
- `WHATSAPP_GRAPH_API_VERSION`: opcional, por defecto `v25.0`.

Flujo actual del bot para clientes:

1. El cliente escribe por WhatsApp.
2. El bot pide ciudad; por ahora solo acepta `San Miguel`.
3. El bot muestra categorias del menu: desayunos, panes todo el dia, extras y bebidas.
4. El cliente elige productos por numero o nombre.
5. El bot pide cantidad y arma el carrito.
6. El cliente puede escribir `agregar`, `ver`, `confirmar` o `cancelar`.
7. Al confirmar, se guarda una orden de cliente recibida por WhatsApp.

Endpoints internos para revisar ordenes de clientes:

- `GET /api/customer-orders`
- `GET /api/customer-orders/{order_id}`

Menu cargado actualmente:

- Desayunos: Panfri, Companeros, Jamuevo, El Mananero, Panpollo, Panchori.
- Panes todo el dia: Senor Bistec, Senora Milanesa, El Tropicalito, Guanacoburger, Pansalchi, El Pibe, Jamancito, Salchiloco, Jamorty, El Criollo, Steak Sandwich.
- Extras: Nachos Guanacos, Nachos Premium, Alitas Asadas, Papas Fritas.
- Bebidas: categoria lista para cargar cuando este definido el menu.
