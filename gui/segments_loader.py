import json
from collections import namedtuple

Segment = namedtuple('Segment', ['points', 'label'])

def load_segments(path='gui/segments.json'):
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    segments = []
    for item in data:
        segments.append(Segment(points=item['points'], label=item['label']))
    return segments
