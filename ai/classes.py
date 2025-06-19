# Список классов по индексу
CLASSES = [
    "background",       # 0
    "Periodontit",      # 1
    "artefact",         # 2
    "bracket",          # 3
    "caries",           # 4
    "crown",            # 5
    "cyst",             # 6
    "eights",           # 7
    "filling",          # 8
    "implant",          # 9
    "mini implant",     # 10
    "missing teeth",    # 11
    "radix",            # 12
    "retailer",         # 13
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