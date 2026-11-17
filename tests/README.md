# Проверка ChArUco

Статическому сайту не нужны зависимости сборки. Для регрессионной проверки нужны Node.js с `playwright`, Chromium (`/usr/bin/chromium`), Python с `opencv-contrib-python-headless`, `cairosvg`, `pymupdf`.

Из корня репозитория запустите `python -m http.server 8080`, затем в другом терминале:

```sh
node tests/charuco-browser.cjs
python tests/charuco-opencv.py
```

`TEST_BASE_URL` меняет адрес сервера; `TEST_OUTPUT` — каталог результатов (по умолчанию `work/charuco-check`).

Проверяются чётные/нечётные размеры доски, начальный ID, 250 уникальных маркеров, запрет неполных досок, сохранение физического размера большого листа, прямой PDF и браузерная печать A4. OpenCV распознаёт все ID и сравнивает рисунок с `CharucoBoard` (современный шаблон, `setLegacyPattern(False)`). Незначительные расхождения пикселей на границах допускаются из-за растеризации SVG.
