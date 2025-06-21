# ai/valid.py

def valid_teeth(teeth, teeth_fullness_result):
    if not teeth:
        return "[Ошибка] Зубы не обнаружены. Пожалуйста, загрузите корректный снимок с видимыми зубами.", 0

    # Определяем максимальное количество зубов (сменный/постоянный прикус)
    if "Прикус: Сменный" in teeth_fullness_result[0]:
        max_teeth = 52
    else:
        max_teeth = 32

    # Считаем отсутствующие зубы по списку missing
    missing_count = 0
    for line in teeth_fullness_result:
        if line.startswith("В ряду"):
            parts = line.split(":")
            if len(parts) > 1:
                missing = [s.strip() for s in parts[1].split(",") if s.strip().isdigit()]
                missing_count += len(missing)
    expected_teeth = max_teeth - missing_count if (max_teeth - missing_count) > 0 else 1

    found_percent = len(teeth) / expected_teeth

    if found_percent < 0.7:
        return (
            f"[Ошибка] Слишком мало зубов ({len(teeth)} из {expected_teeth} c учетом целостности зубного ряда, {found_percent*100:.1f}%). "
            "Пожалуйста, загрузите корректный снимок с видимыми зубами.",
            expected_teeth,
        )

    return None, expected_teeth

def valid_masks(teeth, disease_masks, results=None):
    if results is None:
        results = []
    if not disease_masks["pathologies"] and not disease_masks["extra"]:
        results.append("[Ошибка] Модуль не смог обнаружить следы лечения или патологии.")
        segments = [dict(tooth, is_tooth=True) for tooth in teeth]
        return results, segments

    if not disease_masks["pathologies"] and disease_masks["extra"]:
        results.append(
            "Патологии не обнаружены. Все зубы в норме. "
            "!Рекомендуется ручная проверка во избежание ошибок!"
        )
        segments = [dict(tooth, is_tooth=True) for tooth in teeth]
        segments += [dict(item, is_extra=True) for item in disease_masks["extra"]]
        return results, segments

    return None