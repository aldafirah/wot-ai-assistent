import cv2
import numpy as np
from typing import Dict, Any


def crop(frame, roi):
    x, y, w, h = roi
    return frame[y:y+h, x:x+w]


def detect_minimap(minimap_bgr, hsv_cfg):
    hsv = cv2.cvtColor(minimap_bgr, cv2.COLOR_BGR2HSV)
    enemy_low = np.array(hsv_cfg['enemy_low'])
    enemy_high = np.array(hsv_cfg['enemy_high'])
    ally_low = np.array(hsv_cfg['ally_low'])
    ally_high = np.array(hsv_cfg['ally_high'])

    enemy_mask = cv2.inRange(hsv, enemy_low, enemy_high)
    ally_mask = cv2.inRange(hsv, ally_low, ally_high)

    # морфология для удаления шума
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3,3))
    enemy_mask = cv2.morphologyEx(enemy_mask, cv2.MORPH_OPEN, k)
    ally_mask = cv2.morphologyEx(ally_mask, cv2.MORPH_OPEN, k)

    # контуры как точки
    def centers(mask):
        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        pts = []
        for c in cnts:
            if cv2.contourArea(c) < 4:
                continue
            M = cv2.moments(c)
            if M['m00']:
                cx = int(M['m10']/M['m00'])
                cy = int(M['m01']/M['m00'])
                pts.append((cx, cy))
        return pts

    enemies = centers(enemy_mask)
    allies = centers(ally_mask)

    # простая кластеризация
    def cluster(points, eps=18):
        clusters = []
        used = set()
        for i, p in enumerate(points):
            if i in used:
                continue
            group = [p]
            used.add(i)
            for j, q in enumerate(points):
                if j in used:
                    continue
                if (p[0]-q[0])**2 + (p[1]-q[1])**2 <= eps*eps:
                    used.add(j)
                    group.append(q)
            clusters.append(group)
        centers_list = [(
            int(sum(x for x,_ in g)/len(g)),
            int(sum(y for _,y in g)/len(g))
        ) for g in clusters]
        sizes = [len(g) for g in clusters]
        return centers_list, sizes

    enemy_centers, enemy_sizes = cluster(enemies)

    return {
        'enemy_points': enemies,
        'ally_points': allies,
        'enemy_clusters': enemy_centers,
        'enemy_cluster_sizes': enemy_sizes
    }


def detect_sixth_sense(crosshair_bgr, template_path: str):
    if not template_path:
        return False, 0.0
    try:
        tpl = cv2.imread(template_path, cv2.IMREAD_UNCHANGED)
        if tpl is None:
            return False, 0.0
        img = cv2.cvtColor(crosshair_bgr, cv2.COLOR_BGR2GRAY)
        # если шаблон с альфой — возьмём серый
        if tpl.shape[2] == 4:
            tpl = cv2.cvtColor(tpl, cv2.COLOR_BGRA2GRAY)
        else:
            tpl = cv2.cvtColor(tpl, cv2.COLOR_BGR2GRAY)
        res = cv2.matchTemplate(img, tpl, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(res)
        return max_val > 0.6, float(max_val)
    except Exception:
        return False, 0.0


def analyze_frame(frame_bgr, cfg) -> Dict[str, Any]:
    rois = cfg['rois']
    state = {}

    # Миникарта
    mini = crop(frame_bgr, rois['minimap'])
    mini_info = detect_minimap(mini, cfg['minimap_hsv'])
    state.update(mini_info)

    # Лампочка
    cross = crop(frame_bgr, rois['crosshair'])
    on, score = detect_sixth_sense(cross, cfg['assets'].get('sixth_sense_template', ''))
    state['sixth_sense'] = on
    state['sixth_sense_score'] = score

    # OCR (опционально)
    try:
        import easyocr
        reader = analyze_frame._reader  # кэш
    except Exception:
        reader = None
    if reader is None:
        try:
            import easyocr
            analyze_frame._reader = easyocr.Reader(['en', 'ru'], gpu=False)
            reader = analyze_frame._reader
        except Exception:
            reader = None
    state['hp'] = None
    state['speed'] = None
    if reader is not None:
        status = crop(frame_bgr, rois['status'])
        gray = cv2.cvtColor(status, cv2.COLOR_BGR2GRAY)
        txt = ' '.join(reader.readtext(gray, detail=0))
        # грубый парсинг чисел
        import re
        nums = re.findall(r"\d+", txt)
        if nums:
            # эвристика: предполагаем первое — HP, последнее — скорость
            state['hp'] = int(nums[0])
            try:
                state['speed'] = int(nums[-1])
            except Exception:
                state['speed'] = None
        state['status_text'] = txt
    else:
        state['status_text'] = ''

    # Производные
    state['enemy_count'] = len(state['enemy_points'])
    state['ally_count'] = len(state['ally_points'])
    state['enemy_max_cluster'] = max(state['enemy_cluster_sizes'], default=0)
    return state
