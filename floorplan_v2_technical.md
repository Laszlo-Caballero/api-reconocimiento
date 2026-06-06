# Documentación Técnica: Pipeline Floorplan V2

Este documento detalla la arquitectura técnica del pipeline híbrido implementado en la clase `FloorPan` en [floopan.py](file:///c:/Users/laszlo/Downloads/uni/inteligencia%20y%20machin/api-productos/modules/floorplan_v2/floopan.py), que combina visión artificial convencional con OpenCV y el modelo multimodal de inteligencia artificial **Qwen2.5-VL 7B** a través de Ollama.

---

## 1. Arquitectura Híbrida del Sistema

El procesamiento del plano de planta se divide en dos fases complementarias:
1. **Detección Geométrica (OpenCV)**: Responsable de extraer con precisión de pixel las fronteras físicas del espacio (paredes) y delimitar los cuartos (contornos/centroides/áreas). La visión clásica es excelente para detectar límites físicos exactos, pero carece de comprensión semántica.
2. **Clasificación Semántica y Relaciones (Qwen2.5-VL 7B)**: A partir del plano visualizado y los centroides/delimitadores de OpenCV, el modelo de IA deduce el nombre del espacio (ej: *"Oficina 102"*), clasifica su tipo funcional y determina las conexiones de adyacencia (puertas transitables).

---

## 2. Detalle de Funciones (`FloorPan`)

A continuación se describe el funcionamiento detallado de cada método implementado en la clase:

### `preprocess_image(self, image: Image.Image)`
* **Objetivo**: Extraer la máscara binaria completa de paredes del plano.
* **Algoritmo**:
  1. Convierte la imagen PIL a formato BGR de OpenCV y extrae su espacio de color HSV y escala de grises.
  2. **Detección de paredes exteriores**: Filtra el canal HSV bajo un rango de color verde (`lower_green = [38, 70, 100]` a `upper_green = [85, 255, 255]`) para aislar los muros verdes exteriores.
  3. **Detección de paredes internas**: Filtra las tonalidades grises en base al valor de intensidad de brillo en gris (`90` a `205`), excluyendo la máscara verde para evitar redundancias.
  4. **Unión y Cierre**: Aplica una operación lógica `OR` para consolidar ambas máscaras y realiza un cierre morfológico (`MORPH_CLOSE`) con un kernel elíptico de $4\times4$ para unir brechas y discontinuidades de las paredes, finalizando con una dilatación para engrosarlas levemente.

---

### `detect_rooms(self, walls_mask: np.ndarray, original_img: np.ndarray) -> list`
* **Objetivo**: Detectar las regiones transitables delimitadas y cerradas.
* **Algoritmo**:
  1. Invierte la máscara de paredes (`bitwise_not`) para obtener las zonas transitables como blanco (255).
  2. Erosiona la imagen del interior para separar habitaciones que comparten bordes o umbrales de puerta muy finos.
  3. Aplica `cv2.findContours` para extraer todos los contornos cerrados del interior del plano.
  4. **Filtrado de contornos**:
     * **Área**: Debe ser $\ge 0.3\%$ y $\le 50\%$ del área total de la imagen para omitir ruido de pixeles o capturar el plano completo como una sola habitación.
     * **Márgenes**: Excluye contornos que toquen el borde físico de la imagen (distancia $< 15$ px) para evitar la detección de zonas exteriores o parqueos.
     * **Aspect Ratio**: Descarta contornos con una relación de aspecto de caja delimitadora superior a `8` (lo que indica pasillos/líneas extremadamente largas que representan ruido).
     * **Deduplicación**: Agrupa centroides cuya distancia euclidiana sea inferior a `50` px para consolidar detecciones solapadas.
  5. Aplica `cv2.approxPolyDP` para simplificar la geometría de cada contorno a un polígono regular.

---

### `classify_rooms_with_ai(self, image_bytes: bytes, rooms_data: list) -> dict`
* **Objetivo**: Clasificar semánticamente las regiones a través de Qwen2.5-VL.
* **Flujo**:
  1. Compila un resumen estructurado en formato JSON con el identificador (`id`), área en píxeles (`area_px`), centroide (`centroid`) y caja delimitadora (`bbox`) de cada región detectada por OpenCV.
  2. Envía este JSON junto con los bytes crudos de la imagen original al modelo local `qwen2.5vl:7b` en Ollama.
  3. El prompt instruye específicamente al modelo a relacionar las coordenadas de cada región con la imagen visual, asignar nombres en español, determinar las conexiones físicas inmediatas (puertas) y estimar los metros cuadrados reales (`estimated_sqm`).
  4. Se configuran opciones deterministas (`temperature = 0.05`) para evitar variabilidad en el JSON de respuesta.
  5. **Mecanismo de Fallback**: Si el modelo no clasifica o devuelve alguna región omitida, se ejecuta un rellenado automático de respaldo conservando el metraje proporcional a su área en píxeles.

---

### `build_floor_graph(self, rooms_cv: list, rooms_ai: dict) -> nx.Graph`
* **Objetivo**: Generar la estructura topológica final en un grafo de NetworkX.
* **Flujo**:
  1. Inicializa un grafo vacío `nx.Graph`.
  2. Registra cada habitación como un nodo indexado por su `id`, adjuntando las propiedades de OpenCV (centroide, área de pixeles, bounding box) y las propiedades semánticas de la IA (nombre, tipo, sqm).
  3. Agrega las aristas correspondientes a las conexiones de puertas deducidas por Qwen2.5-VL.
  4. **Algoritmo de Proximidad Física (Fallback)**: Calcula una distancia umbral dinámica correspondiente al 70% de la distancia promedio de todos los centroides del plano. Si dos nodos se encuentran a una distancia menor a este umbral y no poseen una conexión de puerta, se agrega una conexión de tipo `proximity` para garantizar la conectividad de pasillos adyacentes.

---

### `overlay_on_image(self, original_img: np.ndarray, rooms_cv: list, G: nx.Graph) -> np.ndarray`
* **Objetivo**: Dibujar y renderizar el grafo y las clasificaciones sobre la imagen del plano.
* **Flujo**:
  1. Dibuja los contornos cerrados de cada cuarto con un relleno semitransparente (`cv2.addWeighted` a un 28% de opacidad) utilizando el color predefinido para su tipo funcional.
  2. Dibuja líneas BGR para las aristas del grafo:
     * **Naranja** `(0, 140, 255)`: Puertas de paso directo.
     * **Cian** `(40, 200, 220)`: Proximidad o adyacencia espacial.
  3. Renderiza círculos concéntricos en cada centroide y escribe una etiqueta con el nombre del espacio centrado dentro de una caja rectangular negra de contraste.

---

## 3. Modelo de Inteligencia Artificial: Qwen2.5-VL 7B

El sistema utiliza **Qwen2.5-VL 7B**, un modelo fundacional de visión-lenguaje desarrollado por Alibaba.

### Ventajas de su uso en este Pipeline:
1. **Comprensión Espacial Multimodal**: Acepta entradas visuales (imágenes) y textuales simultáneamente, lo que le permite entender directamente las coordenadas relativas del bounding box del plano arquitectónico y asociarlas con la distribución espacial que observa en la imagen.
2. **Detección de Conectividad**: A diferencia de los modelos OCR convencionales, Qwen2.5-VL puede inferir visualmente qué cuartos están conectados mediante puertas y aberturas al examinar la imagen, lo que posibilita la generación del grafo de evacuación.
3. **Ejecución Local**: Funciona directamente sobre la instancia local de **Ollama** (`qwen2.5vl:7b`), eliminando latencias de red externa y garantizando la confidencialidad de los planos de planta del usuario.
