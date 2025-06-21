# ai/disease_seg.py

import os
import csv
import torch
from torchvision import transforms
from PIL import Image
import numpy as np
import segmentation_models_pytorch as smp
import cv2

from ai.unet_data.module import create_unet
from ai.classes import CLASSES, PATHOLOGIES, EXTRA, RAW_TO_HUMAN

# Подгрузка весов и инициализация модели
WEIGHTS_PATH = "ai/unet_data/u-net_weights.pth"
NUM_CLASSES = len(CLASSES)


device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = create_unet(num_classes=NUM_CLASSES).to(device)

model.load_state_dict(torch.load(WEIGHTS_PATH, map_location=device))
model.eval()

transform = transforms.Compose([
    transforms.Resize((256,256), interpolation=transforms.InterpolationMode.BILINEAR),
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
    print(f"[DEBUG] Обрабатываю изображение: {image_path}")
    image = Image.open(image_path).convert('RGB')
    input_tensor = transform(image).unsqueeze(0).to(device)
    print(f"[DEBUG] input_tensor shape: {input_tensor.shape}")

    with torch.no_grad():
        output = model(input_tensor)
        print(f"[DEBUG] Output shape: {output.shape}")
        probs = torch.softmax(output, dim=1)
        masks = torch.argmax(probs, dim=1).cpu().numpy()[0]
        print(f"[DEBUG] masks unique: {np.unique(masks)}")

    results = {"pathologies": [], "extra": []}

    for class_idx in range(1, len(CLASSES)):
        mask = (masks == class_idx).astype(np.uint8)
        pixels = mask.sum()
        print(f"[DEBUG] Class {class_idx} ({CLASSES[class_idx]}): пикселей = {pixels}")
        if pixels == 0:
            continue

        label = CLASSES[class_idx]
        item = {
            "class_idx": class_idx,
            "label": label,
            "human_label": RAW_TO_HUMAN[label],
            "mask": mask,
            "contour": mask_to_contour(mask),
        }
        if label in PATHOLOGIES:
            results["pathologies"].append(item)
        else:
            results["extra"].append(item)

    print(f"[DEBUG] Обнаружено pathologies: {len(results['pathologies'])}, extra: {len(results['extra'])}")
    return results