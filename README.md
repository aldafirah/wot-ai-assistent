# WoT Live AI Assistant (v0.1)

Лайв‑коуч для World of Tanks: смотрит **твой** видеопоток (экран/OBS/RTMP), читает HUD (миникарта, лог урона, статус), и выдаёт **тактические подсказки** в оверлее. Есть сбор датасета и простое дообучение на твоих VOD’ах.

> Дизайн цели: **никакой автоматизации управления** — только анализ и советы в отдельном окне/оверлее, чтобы не нарушать ToS.

---

## Возможности v0.1

* Источники видео: экранная область (MSS), OBS Virtual Camera, RTMP/HLS (через OpenCV).
* Калибровка ROI (области интереса): `minimap`, `status`, `damage_log`, `crosshair`.
* Миникарта: детекция союзных/вражеских маркеров по цвету (HSV), кластеризация близких меток.
* «Лампочка» (Sixth Sense): шаблон‑матчинг (подставь свой шаблон PNG).
* OCR (опционально, EasyOCR): парсинг HP/скорости/таймера.
* Эвристики совета: «откатись/давим фланг/бережём ХП/не пикать под численным перевесом рядом».
* Оверлей с подсказками и FPS; запись кадров в датасет; скрипт дообучения YOLOv8 для HUD‑иконок.

---

## Быстрый старт

1. **Установка**

   ```bash
   python -m venv .venv && source .venv/bin/activate  # или .venv\Scripts\activate в Windows
   pip install -r requirements.txt
   ```
2. **Калибровка ROI** (под свой HUD):

   ```bash
   python calibrate.py --source screen
   ```

   Наведи мышкой и выдели прямоугольники: 1 — minimap, 2 — status, 3 — damage_log, 4 — crosshair, S — сохранить.
3. **Запуск ассистента**:

   ```bash
   python main.py --config config.yaml --source screen
   ```

   Горячие клавиши: `Q` — выход, `D` — показать/скрыть отладку, `R` — запись датасета.

> Альтернатива: OBS → **Start Virtual Camera**, затем `--source camera --camera-index 0`.

---

## Структура проекта

```
.
├─ requirements.txt
├─ config.example.yaml   # cкопируй в config.yaml и подправь
├─ main.py               # главный цикл: захват → перцепция → политика → оверлей
├─ capture.py            # источники видео (экран, камера, RTMP/HLS)
├─ calibrate.py          # интерактивная разметка ROI
├─ perception.py         # миникарта/лампочка/OCR
├─ policy.py             # генерация советов
├─ overlay.py            # рисование подсказок/отладка
├─ utils.py              # служебные штуки (FPS, безопасные импорты)
├─ collect.py            # запись кадров и ROI в датасет
├─ train_hud.py          # дообучение YOLOv8 на твоих VOD’ах (необязательно)
└─ assets/
   └─ sixth_sense.png    # шаблон лампочки (положи сюда свой)
```

---

## requirements.txt

```txt
opencv-python
numpy
mss
pyyaml
scikit-image
scikit-learn
# Опционально (для OCR и дообучения):
# easyocr
# ultralytics
```

> `easyocr` тянет PyTorch; ставь, если нужен OCR. `ultralytics` — если будешь дообучать детектор HUD.

---

## config.example.yaml

```yaml
source: screen  # screen | camera | rtmp | hls
screen_region: [0, 0, 1920, 1080]  # x, y, w, h для захвата экрана
camera_index: 0
url: "rtmp://localhost/live/wot"  # для rtmp/hls

rois:
  minimap:   [1500, 780, 380, 300]
  status:    [20, 940, 600, 120]
  damage_log: [1200, 100, 600, 300]
  crosshair: [890, 470, 140, 140]

ui:
  overlay_scale: 1.0
  show_debug: true
  speak: false  # можешь озвучку прикрутить позже

minimap_hsv:
  enemy_low:  [0, 120, 120]
  enemy_high: [10, 255, 255]
  ally_low:   [35, 120, 120]
  ally_high:  [85, 255, 255]
  # при необходимости добавь красный диапазон [170..180] для красного кольца

assets:
  sixth_sense_template: "assets/sixth_sense.png"

recording:
  out_dir: "dataset"
  save_every_n_frames: 30
```

> Калибратор заполнит `rois` и `screen_region` автоматически и сохранит в `config.yaml`.
