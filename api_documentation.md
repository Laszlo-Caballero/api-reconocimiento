# API Checklist

## Módulo: Autenticación

### Endpoint: Registro de Usuario

* [x] Implementado
* [ ] Pendiente
* Método HTTP: POST
* Ruta:

```http
/api/auth/register
```

### Descripción

Registra a un nuevo usuario en la aplicación móvil con sus credenciales y datos básicos de cuenta. Tras registrarse con éxito, el servidor devuelve el token de acceso JWT y la información básica del usuario.

### Headers requeridos

```json
{
  "Content-Type": "application/json"
}
```

### Path Parameters

Ninguno.

### Query Parameters

Ninguno.

### Request Payload

```json
{
  "username": "juan_perez",
  "email": "juan.perez@example.com",
  "password": "mi_password_seguro_123"
}
```

#### Descripción de campos:

| Campo    | Tipo   | Requerido | Descripción                                                |
| -------- | ------ | --------- | ---------------------------------------------------------- |
| username | string | Sí        | Nombre de usuario único para identificarse en la app.      |
| email    | string | Sí        | Correo electrónico del usuario (debe tener formato válido). |
| password | string | Sí        | Contraseña de la cuenta (debe tener al menos 6 caracteres). |

### Response 200 OK

```json
{
  "status": "success",
  "message": "Registro de usuario exitoso",
  "data": {
    "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "userId": 1,
      "username": "juan_perez",
      "email": "juan.perez@example.com",
      "role": "USER"
    }
  }
}
```

### Response 400

```json
{
  "status": "error",
  "message": "Datos inválidos o el usuario ya existe."
}
```

### Response 401

No aplica (es un endpoint público).

### Response 404

```json
{
  "status": "error",
  "message": "Servidor de registro no disponible"
}
```

### Response 500

```json
{
  "status": "error",
  "message": "Error interno del servidor"
}
```

### Reglas de negocio

* **Campos obligatorios:** `username`, `email` y `password` no pueden estar vacíos.
* **Validaciones del email:** El correo electrónico ingresado debe ser sintácticamente válido (valida por `Patterns.EMAIL_ADDRESS`).
* **Longitud mínima de contraseña:** La contraseña debe tener al menos 6 caracteres.
* **Restricción de coincidencia:** En la UI, el campo de confirmación de contraseña debe coincidir exactamente con el campo de contraseña antes de enviar la solicitud.

### Flujo Frontend → Backend

1. **Pantalla:** `RegisterFragment`.
2. **Acción del usuario:** El usuario ingresa su nombre de usuario, correo, contraseña, confirma la contraseña y presiona el botón "Registrar".
3. **Datos que envía:** Un objeto JSON con `username`, `email` y `password`.
4. **Datos que consume de la respuesta:** El `accessToken` y la información del `user` (`userId`, `username`, `email`, `role`).
5. **Comportamiento esperado:** Si es exitoso, guarda la sesión de forma persistente a través del `AuthManager`, registra el token actual de FCM para notificaciones push, realiza un anuncio por voz ("Registro exitoso. Bienvenido.") y redirige al usuario al `MainActivity` limpiando la pila de pantallas (Backstack). Si falla, muestra un texto descriptivo del error en pantalla.

---

### Endpoint: Inicio de Sesión

* [x] Implementado
* [ ] Pendiente
* Método HTTP: POST
* Ruta:

```http
/api/auth/login
```

### Descripción

Autentica al usuario mediante sus credenciales (usuario y contraseña) y retorna el token JWT de acceso para consumos autorizados posteriores.

### Headers requeridos

```json
{
  "Content-Type": "application/json"
}
```

### Path Parameters

Ninguno.

### Query Parameters

Ninguno.

### Request Payload

```json
{
  "username": "juan_perez",
  "password": "mi_password_seguro_123"
}
```

#### Descripción de campos:

| Campo    | Tipo   | Requerido | Descripción                               |
| -------- | ------ | --------- | ----------------------------------------- |
| username | string | Sí        | Nombre de usuario registrado en la app.   |
| password | string | Sí        | Contraseña de acceso asociada al usuario. |

### Response 200 OK

```json
{
  "status": "success",
  "message": "Inicio de sesión exitoso",
  "data": {
    "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "userId": 1,
      "username": "juan_perez",
      "email": "juan.perez@example.com",
      "role": "ADMIN"
    }
  }
}
```

### Response 400

```json
{
  "status": "error",
  "message": "Datos inválidos"
}
```

### Response 401

```json
{
  "status": "error",
  "message": "Usuario o contraseña incorrectos."
}
```

### Response 404

```json
{
  "status": "error",
  "message": "Servidor de autenticación no encontrado."
}
```

### Response 500

```json
{
  "status": "error",
  "message": "Error interno del servidor"
}
```

### Reglas de negocio

* **Campos obligatorios:** El usuario y contraseña son campos requeridos por la interfaz y no pueden enviarse vacíos.
* **Autenticación:** Si las credenciales no corresponden a un usuario registrado o la contraseña es inválida, devuelve un código HTTP `401`.

### Flujo Frontend → Backend

1. **Pantalla:** `LoginFragment`.
2. **Acción del usuario:** El usuario escribe sus credenciales y presiona "Iniciar Sesión".
3. **Datos que envía:** JSON con `username` y `password`.
4. **Datos que consume de la respuesta:** `accessToken` y datos del usuario (`userId`, `username`, `email`, `role`).
5. **Comportamiento esperado:** Al recibir un resultado exitoso (200 OK), el cliente almacena localmente el token de acceso y los datos de usuario en `SharedPreferences` vía `AuthManager`, inicializa el token de notificaciones FCM y redirige al `MainActivity`. Ante un código 401 u otro error, muestra un mensaje descriptivo en color rojo en la interfaz y emite una alerta por voz.

---

## Módulo: Productos e Identificación

### Endpoint: Identificar Producto (Carga de Imagen)

* [x] Implementado
* [ ] Pendiente
* Método HTTP: POST
* Ruta:

```http
/api/products/identify
```

### Descripción

Sube una foto capturada por la cámara o cargada desde la galería del dispositivo móvil al servidor backend, el cual la procesa utilizando CLIP para analizar y reconocer los productos más similares en inventario.

### Headers requeridos

```json
{
  "Authorization": "Bearer {token}",
  "Content-Type": "multipart/form-data"
}
```

### Path Parameters

Ninguno.

### Query Parameters

Ninguno.

### Request Payload

El payload se envía codificado como `multipart/form-data`. Contiene un único parámetro binario:

| Campo | Tipo  | Requerido | Descripción                                                   |
| ----- | ----- | --------- | ------------------------------------------------------------- |
| file  | File  | Sí        | Archivo de imagen capturado/seleccionado (JPEG) para análisis. |

### Response 200 OK

```json
{
  "status": "success",
  "message": "Análisis finalizado con éxito",
  "data": [
    {
      "productoId": 101,
      "nombre": "Laptop Gamer ASUS ROG Zephyrus G14",
      "precios": [5499.00, 5299.00],
      "vendido_por": "Saga Falabella",
      "marca": "ASUS",
      "url_venta": "https://www.falabella.com.pe/falabella-pe/category/cat40712/Laptops",
      "caracteristicas": [
        "Procesador AMD Ryzen 9",
        "Memoria RAM de 16GB DDR5",
        "Tarjeta gráfica NVIDIA RTX 4060",
        "Pantalla ROG Nebula 120Hz"
      ],
      "categoria": "Tecnología",
      "sub_categoria": "Laptops",
      "especificaciones": [
        "Almacenamiento: 1TB SSD NVMe",
        "Sistema Operativo: Windows 11 Home",
        "Batería: 76WHrs, 4S1P, 4 celdas Li-ion",
        "Peso: 1.65 kg"
      ],
      "imagenes": [
        {
          "imagenId": 1,
          "url": "/uploads/laptop.jpg"
        }
      ],
      "similitud": 98.0
    }
  ]
}
```

### Response 400

```json
{
  "status": "error",
  "message": "El archivo enviado no es una imagen válida o está vacío."
}
```

### Response 401

```json
{
  "status": "error",
  "message": "No autorizado. Token de autenticación ausente o expirado."
}
```

### Response 500

```json
{
  "status": "error",
  "message": "Error interno al procesar el análisis de imagen"
}
```

### Reglas de negocio

* **Restricción de formato:** Se espera que el archivo enviado sea de tipo MIME `image/jpeg`.
* **Seguridad:** Requiere autorización JWT mediante cabecera. Si expira el token, el backend devuelve HTTP 401 y la app desloguea al usuario redirigiendo a la pantalla de Auth.
* **Historial automático:** El procesamiento exitoso en el backend debe generar automáticamente una entrada en el historial de búsquedas del usuario autenticado.

### Flujo Frontend → Backend

1. **Pantalla:** `ScanFragment` para captura/selección, seguido por la pantalla de transición `AnalyzingFragment` donde se muestra el cargando.
2. **Acción del usuario:** El usuario pulsa "Tomar foto" o "Cargar de galería", selecciona una imagen y se dispara automáticamente la subida.
3. **Datos que envía:** Envía el archivo binario guardado de forma temporal en el caché de la aplicación bajo el parámetro `file`.
4. **Datos que consume de la respuesta:** Consume la lista `data` que contiene objetos de tipo `ProductAnalysis` con especificaciones, precios y nivel de similitud de los elementos detectados.
5. **Comportamiento esperado:** Si la respuesta no está vacía, navega a `AnalysisResultsFragment` pasando la lista de resultados para que el usuario pueda verlos en un listado y seleccionar uno para ir al detalle. Si está vacía, arroja un `Toast` informativo y retorna a la pantalla anterior.

---

### Endpoint: Búsqueda por Voz

* [x] Implementado
* [ ] Pendiente
* Método HTTP: GET
* Ruta:

```http
/api/products/voice
```

### Descripción

Envía la cadena de texto interpretada por el SpeechRecognizer nativo del dispositivo para buscar productos relacionados semánticamente en el backend de la tienda.

### Headers requeridos

```json
{
  "Authorization": "Bearer {token}",
  "Content-Type": "application/json"
}
```

### Path Parameters

Ninguno.

### Query Parameters

```json
{
  "query": "laptop gamer asus"
}
```

#### Descripción de parámetros:

| Parámetro | Tipo   | Requerido | Descripción                                             |
| --------- | ------ | --------- | ------------------------------------------------------- |
| query     | string | Sí        | Frase de búsqueda de voz dictada e identificada en texto. |

### Response 200 OK

```json
{
  "status": "success",
  "message": "Resultados obtenidos con éxito",
  "data": [
    {
      "productoId": 101,
      "nombre": "Laptop Gamer ASUS ROG Zephyrus G14",
      "precios": [5499.00],
      "vendido_por": "Saga Falabella",
      "marca": "ASUS",
      "url_venta": "https://www.falabella.com.pe/falabella-pe/category/cat40712/Laptops",
      "caracteristicas": ["Procesador AMD Ryzen 9"],
      "categoria": "Tecnología",
      "sub_categoria": "Laptops",
      "especificaciones": ["Peso: 1.65 kg"],
      "imagenes": [
        {
          "imagenId": 1,
          "url": "/uploads/laptop.jpg"
        }
      ],
      "similitud": 100.0
    }
  ]
}
```

### Response 400

```json
{
  "status": "error",
  "message": "El parámetro de consulta query está vacío o es inválido."
}
```

### Response 401

```json
{
  "status": "error",
  "message": "No autorizado."
}
```

### Response 500

```json
{
  "status": "error",
  "message": "Error interno del servidor"
}
```

### Reglas de negocio

* La búsqueda se realiza en el backend mediante indexación semántica o coincidencia de palabras clave sobre el catálogo general.

### Flujo Frontend → Backend

1. **Pantalla:** `VoiceSearchDialog` (cargado desde `SearchFragment`).
2. **Acción del usuario:** El usuario toca el botón de micrófono de búsqueda, dicta la frase, y el reconocimiento de voz de Google la transforma a texto para ejecutar la petición de forma automática.
3. **Datos que envía:** Parámetro query por URL.
4. **Datos que consume de la respuesta:** La lista de productos coincidentes `Root<ProductAnalysis>`.
5. **Comportamiento esperado:** Al recibir resultados exitosos, cierra el diálogo, actualiza la caja de texto en `SearchFragment` con el término buscado, y navega a la pantalla `AnalysisResultsFragment` cargando los productos devueltos por el servidor. Si ocurre algún error, actualiza la interfaz del diálogo con el error y permite al usuario reintentar.

---

### Endpoint: Buscar Productos (Catálogo General)

* [ ] Implementado
* [x] Pendiente (Faltante / Propuesto)
* Método HTTP: GET
* Ruta:

```http
/api/products
```

### Descripción

Realiza búsquedas de texto e indexaciones en el catálogo completo de productos del servidor. Actualmente, el frontend tiene una **inconsistencia crítica**: para realizar búsquedas en `SearchFragment` simula el catálogo consultando el endpoint de historial `/history` y filtrando en el cliente o recurriendo a datos locales hardcodeados en `ProductRepository`. Este endpoint propuesto resolvería esta limitación.

### Headers requeridos

```json
{
  "Authorization": "Bearer {token}",
  "Content-Type": "application/json"
}
```

### Path Parameters

Ninguno.

### Query Parameters

```json
{
  "query": "iphone"
}
```

#### Descripción de parámetros:

| Parámetro | Tipo   | Requerido | Descripción                                             |
| --------- | ------ | --------- | ------------------------------------------------------- |
| query     | string | No        | Término de búsqueda textual o código de barras/marca.   |

### Response 200 OK

```json
{
  "status": "success",
  "message": "Búsqueda de catálogo realizada con éxito",
  "data": [
    {
      "productoId": 103,
      "nombre": "Celular Apple iPhone 15 Pro Max 256GB",
      "precios": [5899.00],
      "vendido_por": "Mercado Libre",
      "marca": "Apple",
      "url_venta": "https://listado.mercadolibre.com.pe/iphone-15-pro-max",
      "caracteristicas": [
        "Diseño de titanio de calidad aeroespacial",
        "Chip A17 Pro con GPU de 6 núcleos"
      ],
      "categoria": "Tecnología",
      "sub_categoria": "Celulares",
      "especificaciones": [
        "Capacidad: 256 GB"
      ],
      "imagenes": [
        {
          "imagenId": 3,
          "url": "/uploads/iphone.jpg"
        }
      ],
      "similitud": 100.0
    }
  ]
}
```

### Response 400

```json
{
  "status": "error",
  "message": "Parámetro inválido"
}
```

### Response 401

```json
{
  "status": "error",
  "message": "No autorizado"
}
```

### Response 500

```json
{
  "status": "error",
  "message": "Error interno del servidor"
}
```

### Reglas de negocio

* El backend debe filtrar la base de datos por coincidencia parcial en campos clave como `nombre`, `marca`, `categoria`, `sub_categoria` o `vendido_por`.
* Si no se provee un parámetro `query`, se debe listar todo el catálogo activo de productos ordenados o paginados.

### Flujo Frontend → Backend (Ideal)

1. **Pantalla:** `SearchFragment`.
2. **Acción del usuario:** El usuario escribe en la barra de búsqueda (posee un debounce de 300 ms) o presiona "Enter" en el teclado.
3. **Datos que envía:** Parámetro `query` con el valor ingresado.
4. **Datos que consume de la respuesta:** Lista de productos que coinciden con el término.
5. **Comportamiento esperado:** Renderiza dinámicamente los productos coincidentes en el `RecyclerView`. Si el resultado es vacío, muestra el componente `lytEmptyState` indicando al usuario que intente con otros términos.

---

## Módulo: Historial de Búsquedas

### Endpoint: Consultar Historial

* [x] Implementado
* [ ] Pendiente
* Método HTTP: GET
* Ruta:

```http
/history
```

> [!WARNING]
> **Inconsistencia de Ruta:** El endpoint `/history` está implementado directamente en la raíz y no comparte el prefijo común `/api/` o `/api/v1/` que tienen los demás endpoints del sistema. Se recomienda estandarizar a `/api/history` o `/api/v1/history`.

### Descripción

Recupera el historial completo de los análisis e identificaciones de imágenes y búsquedas que el usuario autenticado ha realizado previamente.

### Headers requeridos

```json
{
  "Authorization": "Bearer {token}",
  "Content-Type": "application/json"
}
```

### Path Parameters

Ninguno.

### Query Parameters

Ninguno.

### Request Payload

Ninguno.

### Response 200 OK

```json
[
  {
    "id": 12,
    "title": "Laptop Gamer ASUS ROG Zephyrus G14",
    "time": "Hace 2 horas",
    "description": "Búsqueda semántica de laptops premium de alta gama",
    "tags": ["Tecnología", "Laptop"],
    "image": "/uploads/laptop.jpg",
    "category": "Tecnología"
  },
  {
    "id": 15,
    "title": "Smart TV LG OLED C3 55 pulgadas",
    "time": "Ayer",
    "description": "Análisis CLIP exitoso de TV de sala",
    "tags": ["Tecnología", "TV"],
    "image": "/uploads/tv.jpg",
    "category": "Tecnología"
  }
]
```

### Response 401

```json
{
  "success": false,
  "message": "Token inválido o expirado"
}
```

### Response 500

```json
{
  "success": false,
  "message": "Error interno del servidor al recuperar historial"
}
```

### Reglas de negocio

* El backend debe extraer la identidad del usuario del token JWT y filtrar los registros en la base de datos de manera que solo se retornen los registros pertenecientes al usuario solicitante.

### Flujo Frontend → Backend

1. **Pantalla:** `HistoryFrangment`.
2. **Acción del usuario:** El usuario accede a la pestaña de Historial en la navegación principal de la aplicación.
3. **Datos que envía:** Envía el token de autenticación en la cabecera.
4. **Datos que consume de la respuesta:** Lista de objetos de historial conteniendo identificador, título, tiempo relativo, descripción, etiquetas, URL de imagen y categoría.
5. **Comportamiento esperado:** Carga y renderiza de forma ordenada la lista de búsquedas previas en el `RecyclerView` utilizando `HistoryAdapter`.

---

### Endpoint: Eliminar Historial de Búsquedas

* [ ] Implementado
* [x] Pendiente (Faltante / Propuesto)
* Método HTTP: DELETE
* Ruta:

```http
/api/history
```

### Descripción

Permite al usuario limpiar por completo su historial de búsquedas y análisis guardado en el servidor.

### Headers requeridos

```json
{
  "Authorization": "Bearer {token}",
  "Content-Type": "application/json"
}
```

### Path Parameters

Ninguno.

### Query Parameters

Ninguno.

### Request Payload

Ninguno.

### Response 200 OK

```json
{
  "success": true,
  "message": "Historial eliminado exitosamente"
}
```

### Response 401

```json
{
  "success": false,
  "message": "No autorizado"
}
```

### Response 500

```json
{
  "success": false,
  "message": "Error al eliminar registros del historial"
}
```

### Reglas de negocio

* Solo se eliminan las entradas correspondientes al usuario que realiza la petición (extraído del token de autorización).

### Flujo Frontend → Backend (Ideal)

1. **Pantalla:** `ConfigFragment` (opción en configuración).
2. **Acción del usuario:** El usuario hace clic en el botón "Borrar mi historial de búsqueda".
3. **Datos que envía:** Cabecera de autorización Bearer.
4. **Datos que consume de la respuesta:** JSON de confirmación de eliminación exitosa.
5. **Comportamiento esperado:** Muestra un mensaje flotante (Toast) confirmando que el historial fue eliminado y actualiza la UI o vacía el listado cuando el usuario navegue a `HistoryFrangment`.

---

## Módulo: Notificaciones Push

### Endpoint: Registrar Token Push

* [x] Implementado
* [ ] Pendiente
* Método HTTP: POST
* Ruta:

```http
/api/notifications/register-token
```

### Descripción

Asocia el token único generado por el SDK de Firebase Cloud Messaging (FCM) para el dispositivo móvil con el usuario autenticado en la base de datos para habilitar el envío de alertas y notificaciones push.

### Headers requeridos

```json
{
  "Authorization": "Bearer {token}",
  "Content-Type": "application/json"
}
```

### Path Parameters

Ninguno.

### Query Parameters

Ninguno.

### Request Payload

```json
{
  "token": "fX2oW9yR8e8:APA91bF3b8c6...",
  "platform": "android"
}
```

#### Descripción de campos:

| Campo    | Tipo   | Requerido | Descripción                                                 |
| -------- | ------ | --------- | ----------------------------------------------------------- |
| token    | string | Sí        | Token de registro único de FCM provisto por Google Play.    |
| platform | string | Sí        | Sistema operativo del dispositivo móvil (Fijo a "android"). |

### Response 200 OK

```json
{
  "status": "success",
  "message": "Token registrado correctamente en el servidor",
  "data": []
}
```

### Response 400

```json
{
  "status": "error",
  "message": "El token provisto es nulo o inválido."
}
```

### Response 401

```json
{
  "status": "error",
  "message": "No autorizado"
}
```

### Response 500

```json
{
  "status": "error",
  "message": "Error interno al guardar token en base de datos"
}
```

### Reglas de negocio

* Si un token ya existía asociado a otro usuario en el mismo dispositivo, debe re-asociarse al nuevo usuario autenticado (evitando tokens huérfanos o envío de notificaciones cruzadas).

### Flujo Frontend → Backend

1. **Pantalla:** La petición se ejecuta de manera interna tras un inicio de sesión exitoso en `LoginFragment`, un registro exitoso en `RegisterFragment`, o de manera asíncrona cuando Firebase genera un nuevo token (`onNewToken`) en `MyFirebaseMessagingService`.
2. **Acción del usuario:** Acciones implícitas (Login/Registro/Actualización del token de la app).
3. **Datos que envía:** Token e identificador de plataforma "android".
4. **Datos que consume de la respuesta:** JSON de confirmación del estado del registro.
5. **Comportamiento esperado:** Al recibir el estado OK, queda confirmada la vinculación. Si no hay internet o falla, se guarda localmente en SharedPreferences bajo el prefijo `push_prefs` y clave `fcm_token` para reintentar el registro en la próxima carga de la app o login.

---

## Módulo: Tiendas Físicas

### Endpoint: Consultar Ubicación de Tiendas

* [ ] Implementado
* [x] Pendiente (Faltante / Propuesto)
* Método HTTP: GET
* Ruta:

```http
/api/stores
```

### Descripción

Recupera las coordenadas (latitud y longitud), el nombre y las direcciones físicas de las tiendas asociadas a un determinado vendedor para representarlas en el mapa interactivo de Google Maps. Actualmente, esta información se encuentra mockeada y hardcodeada en el archivo `MapConfig.kt` del cliente Android.

### Headers requeridos

```json
{
  "Authorization": "Bearer {token}",
  "Content-Type": "application/json"
}
```

### Path Parameters

Ninguno.

### Query Parameters

```json
{
  "seller_name": "Saga Falabella"
}
```

#### Descripción de parámetros:

| Parámetro   | Tipo   | Requerido | Descripción                                                        |
| ----------- | ------ | --------- | ------------------------------------------------------------------ |
| seller_name | string | No        | Filtra las ubicaciones asociadas a un vendedor (ej. Ripley, Saga). |

### Response 200 OK

```json
{
  "status": "success",
  "message": "Tiendas físicas obtenidas exitosamente",
  "data": [
    {
      "name": "Saga Falabella - Centro de Lima",
      "address": "Jirón de la Unión 610, Lima",
      "latitude": -12.047113,
      "longitude": -77.032223,
      "sellerName": "Saga Falabella"
    },
    {
      "name": "Saga Falabella - Las Begonias",
      "address": "Av. Begonias 550, San Isidro, Lima",
      "latitude": -12.091120,
      "longitude": -77.025340,
      "sellerName": "Saga Falabella"
    }
  ]
}
```

### Response 401

```json
{
  "status": "error",
  "message": "No autorizado"
}
```

### Response 500

```json
{
  "status": "error",
  "message": "Error interno al obtener geolocalizaciones"
}
```

### Reglas de negocio

* Si no se pasa el parámetro `seller_name`, debe retornar todas las tiendas físicas disponibles del catálogo.
* Si el vendedor solicitado no posee tiendas físicas registradas, debe responder con una lista vacía o un conjunto de tiendas recomendadas por defecto.

### Flujo Frontend → Backend (Ideal)

1. **Pantalla:** `StoreMapFragment` (abierto mediante el botón "Ver Tiendas" en `ProductDetailFragment`).
2. **Acción del usuario:** El usuario entra a ver el mapa de locales que distribuyen el producto.
3. **Datos que envía:** Parámetro `seller_name` en la query.
4. **Datos que consume de la respuesta:** Lista de ubicaciones con nombre, dirección, latitud y longitud.
5. **Comportamiento esperado:** Al recibir las tiendas, crea dinámicamente marcadores en el Google Map interactivo (`googleMap.addMarker`), mueve la cámara al primer local coincidente y anuncia la carga por voz mediante `AccessibilityHelper`.

---

# Resumen General

La siguiente tabla resume todos los endpoints documentados que la aplicación móvil utiliza o requiere para operar de manera completa e independiente de datos simulados locales:

| Método | Ruta                              | Módulo                      | Estado      |
| ------ | --------------------------------- | --------------------------- | ----------- |
| POST   | `/api/auth/register`              | Autenticación               | Implementado|
| POST   | `/api/auth/login`                 | Autenticación               | Implementado|
| POST   | `/api/products/identify`          | Productos e Identificación  | Implementado|
| GET    | `/api/products/voice`             | Productos e Identificación  | Implementado|
| GET    | `/api/products`                   | Productos e Identificación  | **Propuesto**|
| GET    | `/history`                        | Historial de Búsquedas      | Implementado|
| DELETE | `/api/history`                    | Historial de Búsquedas      | **Propuesto**|
| POST   | `/api/notifications/register-token`| Notificaciones Push         | Implementado|
| GET    | `/api/stores`                     | Tiendas Físicas             | **Propuesto**|

---

# Inconsistencias y Observaciones Detectadas en el Frontend

Para guiar el desarrollo de Backend de forma eficiente, se enumeran los siguientes hallazgos y brechas identificadas en el código del cliente Android:

1. **Falta de Prefijos en Historial (`/history`):** La ruta del historial de búsquedas (`GET /history`) no sigue el patrón unificado de la API que incluye `/api/` o `/api/v1/`. Esto causa un desvío de patrones en la configuración del backend. Se recomienda encarecidamente mover este endpoint a `/api/history` o `/api/v1/history`.
2. **Uso Incorrecto del Historial para Búsquedas:** En `ProductRepository.kt` (método `getProducts`), la búsqueda de productos en texto del `SearchFragment` se simula consumiendo el endpoint de historial `/history` y realizando un filtrado local de títulos en la app:
   ```kotlin
   val historyItems = ApiController.api.getHistory()
   val mapped = historyItems.map { history -> ... }
   // Filtrado local en el cliente
   mapped.filter { it.nombre.contains(query, ignoreCase = true) }
   ```
   Esto no es escalable y limita la búsqueda solo a los elementos analizados previamente por el usuario actual. Debe reemplazarse por el consumo directo del endpoint propuesto de catálogo `/api/products?query={query}`.
3. **Hardcoding de Tiendas Físicas (`MapConfig.kt`):** La base de datos de locales físicos está almacenada de manera estática en el cliente en `MapConfig.MOCK_STORES`. Se necesita migrar este modelo al backend a través de `/api/stores` para posibilitar el mantenimiento dinámico de sucursales sin requerir actualizaciones de la app.
4. **Campos por Defecto Mockeados en Repositorio:** El repositorio móvil maquilla y complementa la información cuando la API no provee todos los datos. Por ejemplo, al mapear elementos de `/history` a productos, asigna `"Desconocido"` como vendedor, `"Genérico"` como marca, y un precio ficticio de `0.0`. El backend debe proveer campos completos equivalentes a la clase `ProductAnalysis` en todas las rutas que retornen productos.
5. **Estructura Envelope Root (`Root<T>`):** El backend debe retornar sus respuestas estructuradas en el envoltorio JSON genérico de la clase `Root<T>` (`status`, `message`, `data`), excepto para `/history`, el cual actualmente espera un listado puro (`List<History>`). Se recomienda estandarizar `/history` para usar también la estructura `Root<List<History>>`.
