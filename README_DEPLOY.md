# ArUco.ru — готовая статическая версия

## Что внутри

- главная `aruco.ru/`
- `/generator/` — генератор ArUco с SVG/PNG и печатью
- `/detector/` — учебный браузерный сканер с камерой/загрузкой картинки
- `/charuco/` — генератор ChArUco + Python-код
- `/learn/` — 6 учебных материалов
- `/examples/` — 6 Python-примеров
- `/about/`, `/sources/`, `/privacy/`
- `robots.txt`, `sitemap.xml`, canonical, Schema.org
- Яндекс Метрика 111624278
- `.htaccess` для HTTPS/non-www, 404 и базовых заголовков

## Установка

Скопировать СОДЕРЖИМОЕ папки `aruco_ru_ready` в корень домена `aruco.ru`.

Структура должна получиться такой:

    public_html/
      index.html
      .htaccess
      robots.txt
      sitemap.xml
      assets/
      generator/
      detector/
      charuco/
      learn/
      examples/
      about/
      sources/
      privacy/

Камера браузера работает на HTTPS (или localhost).

## После загрузки

1. Открыть:
   - https://aruco.ru/
   - https://aruco.ru/generator/
   - https://aruco.ru/detector/
   - https://aruco.ru/charuco/
2. Проверить мобильную версию.
3. Добавить `https://aruco.ru/sitemap.xml` в Яндекс Вебмастер и Google Search Console.
4. Создать цели из `METRIKA_GOALS.md`.
5. Проверить Метрику через Network-фильтр `mc.yandex.ru`.

## Важное ограничение браузерного сканера

Сканер на `/detector/` — учебный: он не ищет произвольный квадрат во всём изображении.
Маркер нужно совместить с жёлтой рамкой и держать примерно фронтально.
Для настоящего CV-проекта используйте Python/OpenCV — пример находится в `/examples/`.

## Дальнейший план

Следующая очередь:
- полноценный поиск квадратов/перспективное выравнивание в браузере;
- визуализатор pose;
- мастер калибровки камеры;
- ArUco + ROS 2;
- реальные кейсы на ROSIKBOT;
- статьи и видео с РоботИКС.
