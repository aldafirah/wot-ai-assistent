import argparse
import yaml
import cv2
from capture import make_source


class RoiCalibrator:
    def __init__(self, frame):
        self.frame = frame
        self.clone = frame.copy()
        self.rois = {}
        self.drawing = False
        self.ix = self.iy = 0
        self.curr_key = None
        cv2.namedWindow('calibrate', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('calibrate', 960, 540)
        cv2.setMouseCallback('calibrate', self.mouse)

    def mouse(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN and self.curr_key is not None:
            self.drawing = True
            self.ix, self.iy = x, y
        elif event == cv2.EVENT_MOUSEMOVE and self.drawing:
            img = self.clone.copy()
            cv2.rectangle(img, (self.ix, self.iy), (x, y), (0, 255, 0), 2)
            cv2.imshow('calibrate', img)
        elif event == cv2.EVENT_LBUTTONUP and self.drawing:
            self.drawing = False
            x0, y0 = min(self.ix, x), min(self.iy, y)
            w, h = abs(x - self.ix), abs(y - self.iy)
            self.rois[self.curr_key] = [x0, y0, w, h]
            self.clone = self.frame.copy()
            cv2.rectangle(self.clone, (x0, y0), (x0 + w, y0 + h), (0, 255, 0), 2)
            cv2.putText(self.clone, self.curr_key, (x0, y0 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.imshow('calibrate', self.clone)

    def run(self):
        instructions = '1-minimap  2-status  3-damage_log  4-crosshair   S-сохранить  Q-выход'
        disp = self.clone.copy()
        cv2.putText(disp, instructions, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.imshow('calibrate', disp)
        while True:
            k = cv2.waitKey(0) & 0xFF
            if k in (ord('q'), ord('Q'), 27):
                break
            if k in (ord('1'),):
                self.curr_key = 'minimap'
            elif k in (ord('2'),):
                self.curr_key = 'status'
            elif k in (ord('3'),):
                self.curr_key = 'damage_log'
            elif k in (ord('4'),):
                self.curr_key = 'crosshair'
            elif k in (ord('s'), ord('S')):
                return self.rois
        return self.rois


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', default='config.yaml')
    ap.add_argument('--source', default='window')
    ap.add_argument('--match-by', default='process_name', help='process_name|pid|title')
    ap.add_argument('--process-name', default='WorldOfTanks.exe')
    ap.add_argument('--pid', type=int, default=None)
    ap.add_argument('--window-title', default='World of Tanks')
    args = ap.parse_args()

    cfg = {
        'source': args.source,
        'screen_region': [0, 0, 1920, 1080],
        'camera_index': 0,
        'url': '',
        'window': {
            'match_by': args.match_by,
            'process_name': args.process_name,
            'pid': args.pid,
            'title': args.window_title,
            'match_mode': 'contains',
            'prefer_client_area': True,
            'fps_limit': 0,
            'allow_fallback_to_screen': False
        }
    }

    src = make_source(cfg)
    ok, frame = src.read()
    src.release()
    if not ok or frame is None:
        print('Не удалось получить кадр. Проверь процесс/окно WoT и режим Borderless.')
        return

    calib = RoiCalibrator(frame)
    rois = calib.run()
    cv2.destroyAllWindows()

    try:
        with open(args.config, 'r', encoding='utf-8') as f:
            full = yaml.safe_load(f)
    except FileNotFoundError:
        full = {}

    full['source'] = 'window'
    full['window'] = cfg['window']
    full['rois'] = rois

    with open('config.yaml', 'w', encoding='utf-8') as f:
        yaml.safe_dump(full, f, allow_unicode=True, sort_keys=False)
    print('Сохранено в config.yaml')


if __name__ == '__main__':
    main()
