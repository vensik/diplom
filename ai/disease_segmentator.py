# ai/disease_segmentator.py

import os
import csv
import torch
from torchvision import transforms
from PIL import Image
import numpy as np
import segmentation_models_pytorch as smp
import cv2

# Список классов по индексу
CLASSES = [
    "background",       # 0
    "Periodontit",      # 1
    # "artefact",         # 2
    "bracket",          # 3
    "caries",           # 4
    "crown",            # 5
    "cyst",             # 6
    "eights",           # 7
    "filling",          # 8
    # "implant",          # 9
    # "mini implant",     # 10
    "missing teeth",    # 11
    # "radix",            # 12
    # "retailer",         # 13
    "sealed channel",   # 14
    "supplemental"      # 15
]

PATHOLOGIES = [
    "Periodontit",
    "caries",
    "cyst",
    "radix",
    "supplemental",
    "missing teeth",
]
EXTRA = set(CLASSES) - set(PATHOLOGIES) - {"background"}

RAW_TO_HUMAN = {
    "background": "Фон",
    "Periodontit": "Периодонтит",
    "artefact": "Артефакт",
    "bracket": "Брекеты",
    "caries": "Кариес",
    "crown": "Коронка",
    "cyst": "Киста",
    "eights": "Зубы мудрости",
    "filling": "Пломбирование",
    "implant": "Имплант",
    "mini implant": "Мини-имплант",
    "missing teeth": "Отсутствие зуба",
    "radix": "Фрагмент зуба",
    "retailer": "Ретейнеры",
    "sealed channel": "Обтурация канала",
    "supplemental": "Сверхкомплектный зуб"
}

# Подгрузка весов и инициализация модели
WEIGHTS_PATH = "ai/unet/results/train_3/best.pth"
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

model = smp.UnetPlusPlus(
    encoder_name="efficientnet-b3",
    encoder_weights=None,
    in_channels=3,
    classes=len(CLASSES)
).to(device)
model.load_state_dict(torch.load(WEIGHTS_PATH, map_location=device))
model.eval()

transform = transforms.Compose([
    transforms.Resize((256, 256)),
    transforms.ToTensor()
])

def mask_to_contour(mask):
    mask_uint8 = (mask * 255).astype(np.uint8)
    contours, _ = cv2.findContours(mask_uint8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return []
    cnt = max(contours, key=cv2.contourArea)
    return [(int(pt[0][0]), int(pt[0][1])) for pt in cnt]

# Основная функция сегменатации
def predict_masks(image_path):
    image = Image.open(image_path).convert('RGB')
    input_tensor = transform(image).unsqueeze(0).to(device)

    with torch.no_grad():
        output = model(input_tensor)
        probs = torch.softmax(output, dim=1)
        masks = torch.argmax(probs, dim=1).cpu().numpy()[0] 

    results = {"pathologies": [], "extra": []}

    for class_idx in range(1, len(CLASSES)):
        mask = (masks == class_idx).astype(np.uint8)
        if mask.sum() == 0:
            continue

        label = CLASSES[class_idx]
        item = {
            "class_idx": class_idx,
            "label": label,
            "human_label": RAW_TO_HUMAN[label],
            "mask": mask,
            "contour": mask_to_contour(mask)
        }
        if label in PATHOLOGIES:
            results["pathologies"].append(item)
        else:
            results["extra"].append(item)

    return results