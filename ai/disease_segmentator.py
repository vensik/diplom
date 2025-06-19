# ai/disease_segmentator.py

import os
import csv
import torch
from torchvision import transforms
from PIL import Image
import numpy as np
import segmentation_models_pytorch as smp
import cv2

from ai.unet.module import UNet
from ai.classes import CLASSES, PATHOLOGIES, EXTRA, RAW_TO_HUMAN

# Подгрузка весов и инициализация модели
WEIGHTS_PATH = "ai/unet/u-net_weights.pth"
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
NUM_CLASSES = len(CLASSES)

# model = smp.UnetPlusPlus(
#     encoder_name="efficientnet-b3",
#     encoder_weights=None,
#     in_channels=3,
#     classes=NUM_CLASSES
# ).to(device)
model = UNet(num_classes=NUM_CLASSES)
model.to(device)

model.load_state_dict(torch.load(WEIGHTS_PATH, map_location=device))
model.eval()

transform = transforms.Compose([
    transforms.RandomResizedCrop(
        size=(256, 256),   
        scale=(1.0, 1.1),     
        ratio=(1.0, 1.0),     
        interpolation=transforms.InterpolationMode.BILINEAR
    ),
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
            # "contour": mask_to_contour(mask), # если используешь
        }
        if label in PATHOLOGIES:
            results["pathologies"].append(item)
        else:
            results["extra"].append(item)

    print(f"[DEBUG] Обнаружено pathologies: {len(results['pathologies'])}, extra: {len(results['extra'])}")
    return results