# ai/diagnosis.py

import os
import tempfile
import numpy as np
import cv2
from PIL import Image, ImageOps
from collections import namedtuple, defaultdict

from ai.teeth_detect import predict_teeth
from ai.disease_seg import predict_masks
from ai.valid import valid_teeth, valid_masks 
Segment = namedtuple('Segment', ['points', 'label'])

def get_row_from_label(label):
    try:
        n = int(label.split()[-1])
    except Exception:
        return "не определён"
    if 10 < n < 20:
        return "Верхний\nправый"
    elif 20 < n < 30:
        return "Верхний\nлевый"
    elif 30 < n < 40:
        return "Нижний\nлевый"
    elif 40 < n < 50:
        return "Нижний\nправый"
    elif n >= 50:
        return "Зачатки"
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

def to_interest_zone(image_path, teeth_segments, desired_size=256, extra_percent=0.08, debug_save_path=None, return_bbox=False):
    img = Image.open(image_path).convert('RGB')
    w, h = img.size

    # Собираем все x-координаты крайних точек зубов
    all_x = []
    for seg in teeth_segments:
        points = seg['points']
        all_x.extend([x for x, y in points])

    x_min, x_max = min(all_x), max(all_x)
    width_teeth = x_max - x_min
    extra_padding = int(width_teeth * extra_percent)
    x_min = max(0, x_min - extra_padding)
    x_max = min(w, x_max + extra_padding)
    img_cropped = img.crop((x_min, 0, x_max, h))

    # Паддинг по высоте для квадрата
    cw, ch = img_cropped.size
    pad_top = (cw - ch) // 2
    pad_bottom = cw - ch - pad_top
    img_padded = ImageOps.expand(img_cropped, border=(0, pad_top, 0, pad_bottom), fill=0)

    img_final = img_padded.resize((desired_size, desired_size), Image.BILINEAR)
    bbox = (x_min, 0, x_max, h)
    if debug_save_path:
        img_final.save(debug_save_path)
    if return_bbox:
        return img_final, bbox
    return img_final


def diagnose_image(image_path, overlap_threshold=0.15, conf_threshold=0.7):
    # Детекция зубов
    teeth = predict_teeth(image_path)
    teeth_labels = [tooth['label'] for tooth in teeth]
    results = []
    results.extend(teeth_fullness(teeth_labels))

    error_message, expected_teeth = valid_teeth(teeth, results)
    if error_message:
        return [error_message], []

    # Подготовка и сегментация масок
    cropped_image = to_interest_zone(image_path, teeth, desired_size=256)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        cropped_image.save(tmp.name)
        cropped_path = tmp.name
    masks_seg = predict_masks(cropped_path)

    early_return = valid_masks(teeth, masks_seg, results)
    if early_return:
        return early_return

    print("[DEBUG]: teeth =", teeth[:3]) 
    print("[DEBUG]: pathologies =", masks_seg["pathologies"][:3])
    print("[DEBUG]: extra =", masks_seg["extra"][:3])

    # Размерность для маски зуба
    if masks_seg["pathologies"]:
        first_mask = masks_seg["pathologies"][0]["mask"]
    elif masks_seg["extra"]:
        first_mask = masks_seg["extra"][0]["mask"]
    else:
        first_mask = None
    mask_shape = first_mask.shape if first_mask is not None else (256, 256) 

    # Проверка наличия патологий для каждого зуба
    for tooth in teeth:
        row = get_row_from_label(tooth['label'])
        pos = tooth_pos_in_row(tooth['label'])
        tooth_mask = np.zeros(mask_shape, dtype=np.uint8)
        pts = np.array([tooth['points']], dtype=np.int32)
        cv2.fillPoly(tooth_mask, pts, 1)
        for item in masks_seg["pathologies"]:
            overlap = (tooth_mask & item["mask"])
            area_tooth = tooth_mask.sum()
            area_overlap = overlap.sum()
            if area_tooth == 0:
                continue
            frac = area_overlap / area_tooth
            confidence = item.get("confidence", 1.0)
            if frac > overlap_threshold and confidence > conf_threshold:
                msg = (
                    f"Зуб {pos} ({row} ряд): "
                    f"{item['human_label']}, уверенность {confidence:.2f}"
                )
                results.append(msg)

    # Формируем полный список для визуализации
    segments = []
    for tooth in teeth:
        tooth_seg = dict(tooth)
        tooth_seg['is_tooth'] = True
        segments.append(tooth_seg)
    for item in masks_seg["pathologies"]:
        pathology_seg = dict(item)
        pathology_seg['is_pathology'] = True
        segments.append(pathology_seg)
    for item in masks_seg["extra"]:
        extra_seg = dict(item)
        extra_seg['is_extra'] = True
        segments.append(extra_seg)

    try:
        os.remove(croped_path)
    except Exception:
        pass

    return results, segments