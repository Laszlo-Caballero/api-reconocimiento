# Documentación de la API para el Dashboard

Esta documentación detalla todos los endpoints disponibles en la API del sistema, agrupados por módulos, con información sobre esquemas de petición, parámetros y respuestas, ideal para la integración de un Dashboard de administración y monitoreo.

---

## 1. Módulo de Autenticación (`/api/auth`)

### Registrar Usuario
* **Ruta**: `POST /api/auth/register`
* **Descripción**: Crea una cuenta de usuario nueva en el sistema.
* **Cuerpo de Petición (JSON)**:
  ```json
  {
    "username": "usuario123",
    "email": "usuario@ejemplo.com",
    "password": "miPasswordSegura"
  }
  ```
* **Respuesta**:
  ```json
  {
    "status": "success",
    "message": "Usuario registrado exitosamente"
  }
  ```

### Iniciar Sesión (Login)
* **Ruta**: `POST /api/auth/login`
* **Descripción**: Autentica al usuario y devuelve un token de acceso JWT necesario para los endpoints protegidos.
* **Cuerpo de Petición (JSON)**:
  ```json
  {
    "username": "usuario123",
    "password": "miPasswordSegura"
  }
  ```
* **Respuesta**:
  ```json
  {
    "status": "success",
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": 1,
      "username": "usuario123",
      "email": "usuario@ejemplo.com"
    }
  }
  ```

---

## 2. Módulo de Productos (`/api/products`)

> [!NOTE]
> Todos los endpoints de este módulo requieren la cabecera `Authorization: Bearer <JWT_TOKEN>`.

### Listar y Buscar Productos
* **Ruta**: `GET /api/products/`
* **Descripción**: Obtiene la lista de productos filtrando opcionalmente por coincidencia de texto.
* **Parámetros de Consulta (Query)**:
  - `query` (opcional, string): Palabra clave para buscar productos.
* **Respuesta**:
  ```json
  [
    {
      "productoid": 1,
      "nombre": "Leche Gloria UHT",
      "descripcion": "Leche entera caja 1L",
      "precio": 4.50,
      "vendido_por": "Plaza Vea Sagitario"
    }
  ]
  ```

### Identificar Producto por Imagen (Búsqueda Vectorial)
* **Ruta**: `POST /api/products/identify`
* **Descripción**: Envía una foto para buscar y clasificar el producto usando coincidencia vectorial con CLIP.
* **Cuerpo de Petición**: `multipart/form-data`
  - `file`: Archivo binario de la imagen.
* **Respuesta**:
  ```json
  {
    "status": "success",
    "matches": [
      {
        "productoid": 1,
        "nombre": "Leche Gloria UHT",
        "score": 0.89
      }
    ]
  }
  ```

### Búsqueda de Productos por Voz
* **Ruta**: `POST /api/products/voice`
* **Descripción**: Ejecuta una búsqueda de productos procesando la consulta transcrita de voz.
* **Cuerpo de Petición (JSON)**:
  ```json
  {
    "query": "buscar leche gloria de un litro"
  }
  ```
* **Respuesta**:
  ```json
  [
    {
      "productoid": 1,
      "nombre": "Leche Gloria UHT",
      "precio": 4.50
    }
  ]
  ```

### Crear Producto
* **Ruta**: `POST /api/products/`
* **Descripción**: Crea un nuevo producto y calcula automáticamente su vector de texto para búsquedas semánticas.
* **Cuerpo de Petición (JSON)**:
  ```json
  {
    "nombre": "Yogurt Gloria Fresa 1kg",
    "precios": [6.50, 6.80],
    "vendido_por": "Metro Chorrillos",
    "marca": "Gloria",
    "url_venta": "https://www.metro.pe/yogurt-gloria-fresa",
    "caracteristicas": ["Bajo en grasa", "Con pulpa de fruta"],
    "categoria": "Lácteos",
    "sub_categoria": "Yogurt",
    "especificaciones": ["Contenido: 1kg", "Sabor: Fresa"]
  }
  ```
* **Respuesta**:
  ```json
  {
    "status": "success",
    "message": "Producto creado con éxito",
    "data": {
      "productoid": 12,
      "nombre": "Yogurt Gloria Fresa 1kg",
      "vendido_por": "Metro Chorrillos"
    }
  }
  ```

### Actualizar Producto
* **Ruta**: `PUT /api/products/{product_id}`
* **Descripción**: Modifica los campos de un producto existente. Si el nombre cambia, recalcula su vector semántico automáticamente.
* **Cuerpo de Petición (JSON)**:
  ```json
  {
    "nombre": "Yogurt Gloria Fresa 1kg (Familiar)",
    "precios": [6.90]
  }
  ```
* **Respuesta**:
  ```json
  {
    "status": "success",
    "message": "Producto actualizado con éxito",
    "data": {
      "productoid": 12,
      "nombre": "Yogurt Gloria Fresa 1kg (Familiar)"
    }
  }
  ```

### Eliminar Producto
* **Ruta**: `DELETE /api/products/{product_id}`
* **Descripción**: Elimina un producto de forma permanente.
* **Respuesta**:
  ```json
  {
    "status": "success",
    "message": "Producto eliminado con éxito"
  }
  ```

---

## 3. Módulo de Tiendas (`/api/stores`)

### Listar Tiendas
* **Ruta**: `GET /api/stores/`
* **Descripción**: Obtiene todas las tiendas (o locales) guardadas en el sistema.
* **Parámetros de Consulta (Query)**:
  - `seller_name` (opcional, string): Filtrar tiendas por el nombre del vendedor/marca (ej. "Plaza Vea").
* **Respuesta**:
  ```json
  [
    {
      "tiendaId": 1,
      "nombre": "Plaza Vea Sagitario",
      "latitud": -12.14658,
      "longitud": -76.98921,
      "ancho": 1024,
      "alto": 768,
      "grafo": {
        "nodes": [...],
        "edges": [...]
      }
    }
  ]
  ```

### Actualizar Ubicación GPS de una Tienda
* **Ruta**: `PATCH /api/stores/{store_id}/location`
* **Descripción**: Configura o modifica las coordenadas geográficas (latitud/longitud) para Google Maps de una tienda física.
* **Cuerpo de Petición (JSON)**:
  ```json
  {
    "latitud": -12.14658,
    "longitud": -76.98921
  }
  ```
* **Respuesta**:
  ```json
  {
    "status": "success",
    "message": "Ubicación de la tienda actualizada exitosamente",
    "data": {
      "tiendaId": 1,
      "nombre": "Plaza Vea Sagitario",
      "latitud": -12.14658,
      "longitud": -76.98921
    }
  }
  ```

---

## 4. Módulo de Planos y Grafo Topológico (`/api/v2/floorplan`)

### Analizar Imagen de Plano (Inicio de Proceso Asíncrono)
* **Ruta**: `POST /api/v2/floorplan/analyze`
* **Descripción**: Recibe una imagen de plano arquitectónico e inicia el pipeline de reconocimiento y segmentación OpenCV + clasificación IA de forma asíncrona mediante Celery.
* **Cuerpo de Petición**: `multipart/form-data`
  - `file`: Archivo binario de la imagen del plano.
* **Respuesta**:
  ```json
  {
    "status": "processing",
    "message": "El análisis del plano se está procesando en segundo plano.",
    "task_id": "9a12c4b8-f027-4a11-8be9-cf4d201bb8d9"
  }
  ```

### Consultar Estado y Resultado del Análisis
* **Ruta**: `GET /api/v2/floorplan/result/{task_id}`
* **Descripción**: Verifica el estado de la tarea en segundo plano. Devuelve el grafo topológico completo de navegación y URLs de imágenes resultantes cuando culmina.
* **Respuesta (Completado)**:
  ```json
  {
    "status": "success",
    "message": "El análisis del plano se ha completado.",
    "data": {
      "nodes": [
        {
          "id": 0,
          "name": "Oficina de Administración",
          "type": "office",
          "area": 12540.0,
          "centroid": [150, 320],
          "sqm": 31.3
        },
        {
          "id": 1,
          "name": "Pasillo Principal",
          "type": "hallway",
          "area": 8450.0,
          "centroid": [280, 320],
          "sqm": 21.1
        }
      ],
      "edges": [
        {
          "source": 0,
          "target": 1,
          "weight": 1.0,
          "connection_type": "door"
        }
      ],
      "summary": {
        "plan_type": "green_walls",
        "total_nodes": 2,
        "total_edges": 1,
        "rooms": 1,
        "corridors": 1,
        "open_spaces": 0
      },
      "visualization_url": "/images/floorplan/result_v2_9a12c4b8.png",
      "debug_url": "/images/floorplan/debug_9a12c4b8.png",
      "width": 1200,
      "height": 900
    }
  }
  ```

### Monitorear Todas las Tareas de Análisis
* **Ruta**: `GET /api/v2/floorplan/all_tasks`
* **Descripción**: Devuelve la lista completa de todas las tareas ejecutadas y sus respectivos metadatos almacenados en Redis. Útil para estadísticas de rendimiento e historial en el Dashboard.
* **Respuesta**:
  ```json
  {
    "tasks": [
      {
        "task_id": "9a12c4b8-f027-4a11-8be9-cf4d201bb8d9",
        "task_name": "analyze_floorplan_service",
        "status": "SUCCESS",
        "args": null,
        "result": { ... },
        "traceback": null
      }
    ],
    "total": 1
  }
  ```

---

## 5. Módulo de Historial (`/api/history`)

> [!NOTE]
> Requiere la cabecera `Authorization: Bearer <JWT_TOKEN>`.

### Obtener Historial de Búsquedas
* **Ruta**: `GET /api/history` (Ruta alternativa compatible: `/history`)
* **Descripción**: Devuelve la bitácora de búsquedas (de voz y de imagen) realizadas por el usuario activo.
* **Respuesta**:
  ```json
  [
    {
      "historialid": 5,
      "tipo_busqueda": "voice",
      "consulta": "leche gloria",
      "fecha": "2026-07-01T15:30:22.000Z"
    }
  ]
  ```

### Borrar Todo el Historial
* **Ruta**: `DELETE /api/history`
* **Descripción**: Elimina de forma permanente todos los registros del historial del usuario activo.
* **Respuesta**:
  ```json
  {
    "status": "success",
    "message": "Historial eliminado exitosamente"
  }
  ```

---

## 6. Módulo de Notificaciones (`/api/notifications`)

> [!NOTE]
> Requiere la cabecera `Authorization: Bearer <JWT_TOKEN>`.

### Registrar Dispositivo para Notificaciones Push (FCM)
* **Ruta**: `POST /api/notifications/register-token`
* **Descripción**: Registra el token de Firebase Cloud Messaging (FCM) y la plataforma del dispositivo móvil.
* **Cuerpo de Petición (JSON)**:
  ```json
  {
    "token": "fcm_token_device_unique_string...",
    "platform": "android"
  }
  ```
* **Respuesta**:
  ```json
  {
    "status": "success",
    "message": "Token registrado correctamente"
  }
  ```

### Listar Todos los Tokens Registrados
* **Ruta**: `GET /api/notifications/tokens`
* **Descripción**: Recupera la lista de todos los tokens FCM registrados y sus plataformas asociadas para enviar notificaciones selectivas.
* **Respuesta**:
  ```json
  {
    "status": "success",
    "message": "Tokens recuperados con éxito",
    "data": [
      {
        "token_id": 1,
        "usuarioid": 3,
        "token": "fcm_token_device_unique_string...",
        "platform": "android"
      }
    ]
  }
  ```

### Enviar/Simular Notificación Push
* **Ruta**: `POST /api/notifications/send`
* **Descripción**: Envía una notificación push a un dispositivo en particular por su token o realiza un broadcast (envío masivo) a todos los dispositivos registrados si no se provee un token específico.
* **Cuerpo de Petición (JSON)**:
  ```json
  {
    "title": "¡Gran Descuento de Fin de Semana!",
    "body": "Aprovecha 20% de descuento en la categoría de Lácteos en todas las tiendas.",
    "token": null
  }
  ```
* **Respuesta**:
  ```json
  {
    "status": "success",
    "message": "Notificación enviada con éxito a 15 dispositivos.",
    "data": {
      "title": "¡Gran Descuento de Fin de Semana!",
      "body": "Aprovecha 20% de descuento en la categoría de Lácteos en todas las tiendas.",
      "devices_notified": 15
    }
  }
  ```

