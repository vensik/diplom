# ai/diagnosis.py

import numpy as np
import cv2
from ai.teeth_detector import predict_teeth
from collections import namedtuple, defaultdict
Segment = namedtuple('Segment', ['points', 'label'])
from ai.disease_segmentator import predict_masks

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
    elif n >= 50:
        return "зачаток"
    return "не определён"
    
def tooth_pos_in_row(label):
    number = label.split()[-1]
    return number[-1]

PERM_TO_BUD_ROW = {1: 5, 2: 6, 3: 7, 4: 8}
BUD_TO_PERM_ROW = {v: k for k, v in PERM_TO_BUD_ROW.items()}

PERM_TO_BUD_TOOTH = {1: 5, 2: 4, 3: 3, 4: 2, 5: 1, 6: 6, 7: 7}

def get_bud_number(row, tooth):
    bud_row = PERM_TO_BUD_ROW.get(row)
    bud_tooth = PERM_TO_BUD_TOOTH.get(tooth)
    if bud_row and bud_tooth:
        return bud_row, bud_tooth
    return None, None

def teeth_fullness(teeth_labels):
    rows_teeth = defaultdict(list)
    for label in teeth_labels:
        try:
            num = int(label.split()[-1])
        except Exception:
            continue
        row_idx = num // 10
        tooth_idx = num % 10
        rows_teeth[row_idx].append(tooth_idx)

    results = []
    main_rows = [1, 2, 3, 4]
    bud_rows = [5, 6, 7, 8]
    has_buds = any(rows_teeth.get(i) for i in bud_rows)
    missing_teeth_messages = []

    if has_buds:
        # СМЕННЫЙ ПРИКУС
        results.append("Прикус: Сменный")
        for row_idx in main_rows:
            present = set(t for t in rows_teeth.get(row_idx, []) if t != 8)
            missing = []
            for i in range(1, 8):
                if i not in present:
                    bud_row, bud_tooth = get_bud_number(row_idx, i)
                    buds = set(rows_teeth.get(bud_row, []))
                    if bud_tooth and bud_tooth in buds:
                        continue
                    missing.append(str(i))
            if missing:
                missing_teeth_messages.append(
                    f"В ряду {row_idx} отсутствуют зубы: {', '.join(missing)}"
                )
    else:
        # ПОСТОЯННЫЙ ПРИКУС
        results.append("Прикус: Постоянный")
        for row_idx in main_rows:
            present = set(t for t in rows_teeth.get(row_idx, []) if t != 8)
            missing = [str(i) for i in range(1, 8) if i not in present]
            if missing:
                missing_teeth_messages.append(
                    f"В ряду {row_idx} отсутствуют зубы: {', '.join(missing)}"
                )

    if missing_teeth_messages:
        results.append("Неполный набор зубов:")
        results.extend(missing_teeth_messages)
    else:
        results.append("Полный набор зубов")
    return results


def diagnose_image(image_path, overlap_threshold=0.15, conf_threshold=0.5):
    teeth = predict_teeth(image_path)
    disease_masks = predict_masks(image_path)
    results = []

    print("DIAGNOSE_IMAGE: teeth =", teeth[:3]) 

    if not teeth:
        results = ["Объекты не обнаружены"]
        return results, []

    teeth_labels = [tooth['label'] for tooth in teeth]
    results.extend(teeth_fullness(teeth_labels))

    if not disease_masks["pathologies"]:
        return results, teeth

    first_mask = disease_masks["pathologies"][0]["mask"]
    mask_shape = first_mask.shape

    for tooth in teeth:
        row = get_row_from_label(tooth['label'])
        pos = tooth_pos_in_row(tooth['label'])

        tooth_mask = np.zeros(mask_shape, dtype=np.uint8)
        pts = np.array([tooth['points']], dtype=np.int32)
        cv2.fillPoly(tooth_mask, pts, 1)
        # проверяем каждую болезнь
        for item in disease_masks["pathologies"]:
            overlap = (tooth_mask & item["mask"])
            area_tooth = tooth_mask.sum()
            area_overlap = overlap.sum()
            if area_tooth == 0:
                continue
            frac = area_overlap / area_tooth
            confidence = item.get("confidence", 1.0)
            if frac > overlap_threshold and confidence > conf_threshold:
                pos = tooth_pos_in_row(tooth['label'])
                msg = (
                    f"Зуб {pos} ({row} ряд): "
                    f"{item['human_label']}, уверенность {confidence:.2f}"
                )
                results.append(msg)

    return results, teeth
