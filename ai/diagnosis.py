#ai/diagnosis.py

import numpy as np
import cv2
from ai.teeth_detector import predict_teeth
from collections import namedtuple
Segment = namedtuple('Segment', ['points', 'label'])
# from ai.disease_segmentator import predict_masks

def get_row_from_label(label):
    try:
        n = int(label.split()[-1])
    except Exception:
        return "не определён"

    if 10 < n < 20:
        return "верхний правый"
    elif 20 < n < 30:
        return "верхний левый"
    elif 30 < n < 40:
        return "нижний левый"
    elif 40 < n < 50:
        return "нижний правый"
    elif number >= 50:
        return "зачаток"
    return "не определён"
    
def tooth_pos_in_row(label):
    number = label.split()[-1]
    return number[-1]

def diagnose_image(image_path, overlap_threshold=0.15, conf_threshold=0.5):
    teeth = predict_teeth(image_path)
    disease_masks = predict_masks(image_path)
    results = []

    print("DIAGNOSE_IMAGE: teeth =", teeth[:3]) 
    if not teeth:
        results = ["Объекты не обнаружены"]
        return results, []

    if not disease_masks:
            for tooth in teeth:
                row = get_row_from_label(tooth['label'])
                pos = tooth_pos_in_row(tooth['label'])
                msg = f"Зуб {pos} ({row} ряд): обнаружен"
                results.append(msg)
            return results, teeth

    for tooth in teeth:
        # создаём маску зуба
        first_mask = next(iter(disease_masks.values()))['mask']
        mask_shape = first_mask.shape
        tooth_mask = np.zeros(mask_shape, dtype=np.uint8)
        pts = np.array([tooth['points']], dtype=np.int32)
        cv2.fillPoly(tooth_mask, pts, 1)
        # проверяем каждую болезнь
        for disease, data in disease_masks.items():
            overlap = (tooth_mask & data['mask'])
            area_tooth = tooth_mask.sum()
            area_overlap = overlap.sum()
            if area_tooth == 0:
                continue
            frac = area_overlap / area_tooth
            if frac > overlap_threshold and data['confidence'] > conf_threshold:
                row = get_row_from_label(tooth['label'])
                pos = tooth_pos_in_row(tooth['label'])
                msg = (
                    f"Зуб {pos} ({row} ряд): "
                    f"{disease}, уверенность {data['confidence']:.2f}"
                )
                results.append(msg)
    return results, teeth

def predict_masks(image_path):
    return {}  # пустой словарь