import argparse
import time
import yaml
import cv2
import numpy as np
from utils import FpsMeter
from capture import make_source
from perception import analyze_frame
from overlay import draw_overlay
from policy import make_advice


def load_config(path: str):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', default='config.yaml')
    ap.add_argument('--source', default=None, help='window|screen|camera|rtmp|hls (переопределяет config)')
    ap.add_argument('--camera-index', type=int, default=None)
    ap.add_argument('--url', type=str, default=None)
    ap.add_argument('--window-title', type=str, default=None, help='подстрока заголовка окна для source=window')
    ap.add_argument('--debug', action='store_true')
    args = ap.parse_args()

    cfg = load_config(args.config)
    if args.source:
        cfg['source'] = args.source
    if args.camera_index is not None:
        cfg['camera_index'] = args.camera_index
    if args.url:
        cfg['url'] = args.url
    if args.window_title:
        cfg.setdefault('window', {})['title'] = args.window_title
    if args.debug:
        cfg.setdefault('ui', {})['show_debug'] = True

    # подготовим окно заранее — так оно появится гарантированно
    cv2.namedWindow('WoT Assistant', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('WoT Assistant', 960, 540)

    src = make_source(cfg)
    fps = FpsMeter()

    print("[WoT Assistant] Запуск… Q — выход, D — отладка, R — датасет, V — запись MP4")
    debug = cfg.get('ui', {}).get('show_debug', False)
    recording = False
    rec_cfg = cfg.get('recording', {})
    every_n = int(rec_cfg.get('save_every_n_frames', 30))
    out_dir = rec_cfg.get('out_dir', 'dataset')
    frame_idx = 0

    # Видео запись
    vcfg = cfg.get('video', {}) or {}
    video_enabled = bool(vcfg.get('enabled', False))
    video_path = vcfg.get('path', 'captures/wot_capture.mp4')
    video_fourcc = vcfg.get('fourcc', 'mp4v')
    video_fps = int(vcfg.get('fps', 60))
    record_overlay = bool(vcfg.get('record_overlay', False))
    writer = None
    wrote_size = None

    try:
        while True:
            ok, frame = src.read()
            if not ok or frame is None:
                print('[WoT Assistant] Нет кадра… (проверь окно игры/режим Borderless)')
                time.sleep(0.05)
                continue

            state = analyze_frame(frame, cfg)
            advice_txt = make_advice(state)

            shown = draw_overlay(frame, state, advice_txt, cfg, fps.tick())
            cv2.imshow('WoT Assistant', shown)

            # dataset (jpg)
            frame_idx += 1
            if recording and frame_idx % every_n == 0:
                import os
                os.makedirs(out_dir, exist_ok=True)
                ts = int(time.time() * 1000)
                cv2.imwrite(f"{out_dir}/frame_{ts}.jpg", frame)
                for name, roi in cfg['rois'].items():
                    x, y, w, h = roi
                    crop = frame[y:y + h, x:x + w].copy()
                    cv2.imwrite(f"{out_dir}/frame_{ts}_{name}.jpg", crop)

            # video (mp4)
            if video_enabled:
                cur = shown if record_overlay else frame
                h, w = cur.shape[:2]
                if (writer is None) or wrote_size != (w, h):
                    import os
                    os.makedirs(os.path.dirname(video_path), exist_ok=True) if os.path.dirname(video_path) else None
                    fourcc = cv2.VideoWriter_fourcc(*video_fourcc)
                    writer = cv2.VideoWriter(video_path, fourcc, video_fps, (w, h))
                    wrote_size = (w, h)
                    print(f"[video] запись -> {video_path} @ {video_fps}fps, size={w}x{h}, overlay={record_overlay}")
                writer.write(cur)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord('q'), ord('Q'), 27):
                break
            elif key in (ord('d'), ord('D')):
                debug = not debug
                cfg['ui']['show_debug'] = debug
            elif key in (ord('r'), ord('R')):
                recording = not recording
                print('[dataset]', 'REC ON' if recording else 'rec off')
            elif key in (ord('v'), ord('V')):
                video_enabled = not video_enabled
                print('[video]', 'REC ON' if video_enabled else 'rec off')

    finally:
        src.release()
        if writer is not None:
            writer.release()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
