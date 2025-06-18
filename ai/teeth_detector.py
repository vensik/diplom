# ai/teeth_detector.py

import os
import yaml
from collections import namedtuple
from ultralytics import YOLO

# Полный список классов
yaml_path = "ai/yolo/dataset/data.yaml"
with open(yaml_path, "r", encoding="utf-8") as f:
    data_yaml = yaml.safe_load(f)
CLASS_NAMES = data_yaml["names"]  

# Загрузка модели YOLO сегментации
model = YOLO("ai/yolo/results/train/weights/best.pt")

def predict_teeth(image_path):
    try:
        # Проверка существования файла
        if not os.path.exists(image_path):
            return "Файл не найден", []

        # Выполнение предсказания
        results = model(image_path)[0]
        
        print("YOLO result names:", getattr(results, 'names', None))
        print("YOLO boxes.cls:", getattr(results.boxes, 'cls', None))
        print("YOLO boxes.conf:", getattr(results.boxes, 'conf', None))
        print("YOLO masks.xy:", getattr(getattr(results, 'masks', None), 'xy', None))

        # Обработка случая без обнаружений
        if not hasattr(results, 'masks') or results.masks is None:
            return []
        
        segments = []
        conf_scores = []
        if results.boxes.conf is not None:
            conf_scores = results.boxes.conf.cpu().numpy().tolist()

        for i, (mask, cls) in enumerate(zip(results.masks.xy, results.boxes.cls)):
            try:
                points = [(int(x), int(y)) for x, y in mask]
                if len(points) < 3:
                    continue
                label = CLASS_NAMES[int(cls)]
                conf = float(conf_scores[i]) if i < len(conf_scores) else 0.0
                if label.lower().startswith('tooth'):
                    segments.append({'points': points, 'label': label})
            except Exception as mask_error:
                print(f"Ошибка обработки маски {i}: {mask_error}")
                continue

        unique_segments = {}
        for seg in segments:
            lbl = seg['label']
            conf = seg.get('confidence', 0.0)
            if lbl not in unique_segments or conf > unique_segments[lbl].get('confidence', 0.0):
                unique_segments[lbl] = seg
        return list(unique_segments.values())
        
    except Exception as e:
        print(f"Ошибка при анализе изображения: {str(e)}")
        return []