# Набор Python-скриптов ArUco.ru

Установите зависимости из корня распакованного архива:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
python -m pip install -r requirements.txt
```

Файлы находятся в папке `code`. Подробный порядок запуска, системы координат и
правила измерения маркеров описаны в `code/README.md`.

Рекомендуемый полный цикл:

```text
07_capture_calibration_images.py
→ 06_charuco_calibration.py
→ 08_validate_calibration.py
→ 09_marker_pose_live.py
→ 10_calibrate_camera_mount.py
→ 11_marker_pose_world.py
```

Документация:

- https://aruco.ru/learn/charuco-calibration/
- https://aruco.ru/learn/pose-estimation/
