"""
Пример дообучения YOLOv8 на HUD‑иконках/событиях.
Подготовь data.yaml в формате Ultralytics (путь к train/val и списку классов),
аннотируй иконки (например, лампочка, арт-засвет, маркеры техники на миникарте, и т.д.).
"""
import argparse


def main():
    try:
        from ultralytics import YOLO
    except Exception:
        print('Установи ultralytics: pip install ultralytics')
        return
    ap = argparse.ArgumentParser()
    ap.add_argument('--model', default='yolov8n.pt')
    ap.add_argument('--data', required=True, help='путь к data.yaml')
    ap.add_argument('--epochs', type=int, default=50)
    args = ap.parse_args()

    model = YOLO(args.model)
    model.train(data=args.data, epochs=args.epochs, imgsz=640, project='runs/hud', name='yolov8-hud')


if __name__ == '__main__':
    main()
