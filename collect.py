import argparse
import os
import time
import yaml
import cv2
from capture import make_source


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', default='config.yaml')
    ap.add_argument('--out', default='dataset')
    ap.add_argument('--interval', type=float, default=1.0)
    args = ap.parse_args()

    with open(args.config, 'r', encoding='utf-8') as f:
        cfg = yaml.safe_load(f)

    os.makedirs(args.out, exist_ok=True)
    src = make_source(cfg)

    try:
        while True:
            ok, frame = src.read()
            if not ok:
                time.sleep(0.01)
                continue
            ts = int(time.time()*1000)
            cv2.imwrite(f"{args.out}/frame_{ts}.jpg", frame)
            # сохраним ROI
            for name, roi in cfg['rois'].items():
                x, y, w, h = roi
                crop = frame[y:y+h, x:x+w]
                cv2.imwrite(f"{args.out}/frame_{ts}_{name}.jpg", crop)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        pass
    finally:
        src.release()


if __name__ == '__main__':
    main()
