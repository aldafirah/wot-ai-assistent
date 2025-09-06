import cv2


def draw_overlay(frame, state, advice_lines, cfg, fps):
    out = frame.copy()
    h, w = out.shape[:2]

    # Полупрозрачная подложка под советы
    box_w = min(600, int(w*0.5))
    box_h = 28 * (len(advice_lines) + 2)
    overlay = out.copy()
    cv2.rectangle(overlay, (10, 10), (10+box_w, 10+box_h), (0, 0, 0), -1)
    alpha = 0.45
    cv2.addWeighted(overlay, alpha, out, 1-alpha, 0, out)

    y = 40
    cv2.putText(out, f"WoT Assistant  |  FPS:{fps:.1f}", (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2)
    y += 30

    # Советы
    for line in advice_lines:
        cv2.putText(out, line, (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,255), 2)
        y += 28

    # Отладка миникарты: точки врагов/союзников
    if cfg['ui'].get('show_debug', False):
        # рисуем точки в ROI миникарты
        x, y0, w0, h0 = cfg['rois']['minimap']
        cv2.rectangle(out, (x, y0), (x+w0, y0+h0), (255,255,255), 1)
        for (cx, cy) in state.get('enemy_points', []):
            cv2.circle(out, (x+cx, y0+cy), 3, (0,0,255), -1)
        for (cx, cy) in state.get('ally_points', []):
            cv2.circle(out, (x+cx, y0+cy), 3, (0,255,0), -1)
        # статус/кроссхэйр рамки
        for name in ('status','damage_log','crosshair'):
            rx, ry, rw, rh = cfg['rois'][name]
            cv2.rectangle(out, (rx, ry), (rx+rw, ry+rh), (255,255,0), 1)

    return out
