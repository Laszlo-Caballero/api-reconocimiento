"""Test del pipeline de habitaciones con debug."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cv2, numpy as np
from modules.floorplan.graph_builder import GraphBuilder
from modules.floorplan.floorplan_service import FloorplanService

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images", "floorplan")
debug = os.path.join(out, "debug")

# Plano sintetico: fondo claro, paredes oscuras, puertas
img = np.ones((500, 700, 3), dtype=np.uint8) * 210
cv2.rectangle(img, (20, 20), (680, 480), (50, 50, 50), 4)
cv2.line(img, (20, 250), (680, 250), (50, 50, 50), 4)
cv2.line(img, (250, 20), (250, 250), (50, 50, 50), 4)
cv2.line(img, (450, 20), (450, 250), (50, 50, 50), 4)
cv2.line(img, (350, 250), (350, 480), (50, 50, 50), 4)
# Puertas
cv2.line(img, (250, 100), (250, 140), (210, 210, 210), 6)
cv2.line(img, (450, 120), (450, 160), (210, 210, 210), 6)
cv2.line(img, (100, 250), (150, 250), (210, 210, 210), 6)
cv2.line(img, (400, 250), (440, 250), (210, 210, 210), 6)
cv2.line(img, (350, 350), (350, 400), (210, 210, 210), 6)
cv2.line(img, (550, 250), (600, 250), (210, 210, 210), 6)
# Flechas de color
cv2.arrowedLine(img, (130, 70), (200, 70), (0, 200, 0), 2)
cv2.circle(img, (500, 100), 12, (0, 0, 200), -1)

os.makedirs(out, exist_ok=True)
cv2.imwrite(os.path.join(out, "test_input.png"), img)

builder = GraphBuilder(open_space_threshold=40, min_room_area=500, door_close_kernel=31, debug_dir=debug)
result = builder.build_graph(img)

s = result["summary"]
print(f"Nodos: {s['total_nodes']} (rooms={s['rooms']}, corr={s['corridors']}, open={s['open_spaces']})")
print(f"Aristas: {s['total_edges']}")
for n in result["nodes"]:
    print(f"  N{n['id']} ({n['type']}) @ ({n['x']},{n['y']}) r={n['radius']}")
for e in result["edges"]:
    print(f"  E: {e['source']}<->{e['target']} w={e['weight']}")

svc = FloorplanService()
svc._generate_visualization(img, result, os.path.join(out, "test_result.png"))
print(f"\nDebug images in: {debug}")
print("DONE")
