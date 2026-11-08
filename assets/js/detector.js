(() => {
  const dictionaries = window.ARUCO_DICTS;
  const byId = id => document.getElementById(id);
  const video = byId('video');
  const canvas = byId('cameraCanvas');
  const context = canvas.getContext('2d', {willReadFrequently: true});
  const dictionarySelect = byId('scanDict');
  const status = byId('scanStatus');
  const foundList = byId('foundMarkers');
  const startButton = byId('startCamera');
  const switchButton = byId('switchCamera');
  const stopButton = byId('stopCamera');
  const fileInput = byId('imageInput');
  const candidateToggle = byId('showCandidates');

  let stream = null;
  let running = false;
  let facing = 'environment';
  let animationId = 0;
  let lastFrameTime = 0;
  let lastReported = '';
  let detector = null;
  let staticImageUrl = '';

  const rotate90 = (bits, size) => {
    const rotated = new Array(size * size);
    for (let row = 0; row < size; row++) {
      for (let column = 0; column < size; column++) {
        rotated[column * size + size - row - 1] = bits[row * size + column];
      }
    }
    return rotated;
  };

  function matchDictionary(matrix) {
    const dictionary = dictionaries[dictionarySelect.value];
    const size = dictionary.size;
    let bits = matrix.flat();
    let best = null;

    for (let rotation = 0; rotation < 4; rotation++) {
      const value = bits.join('');
      for (let id = 0; id < dictionary.count; id++) {
        const reference = dictionary.markers[id];
        let distance = 0;
        for (let index = 0; index < reference.length; index++) {
          if (value[index] !== reference[index]) distance++;
          if (best && distance >= best.distance) break;
        }
        if (!best || distance < best.distance) best = {id, distance, rotation};
      }
      bits = rotate90(bits, size);
    }

    const maximumDistance = Math.max(1, Math.floor(size * size * 0.08));
    return best && best.distance <= maximumDistance ? best : null;
  }

  function createDetector() {
    detector = new AR.Detector({dictionaryName: 'ARUCO'});
    const size = dictionaries[dictionarySelect.value].size;
    detector.dictionary = {markSize: size + 2, find: matchDictionary};
  }

  function fitCanvas(width, height) {
    const maximumSide = 760;
    const scale = Math.min(1, maximumSide / Math.max(width, height));
    canvas.width = Math.max(2, Math.round(width * scale));
    canvas.height = Math.max(2, Math.round(height * scale));
  }

  function polygonArea(corners) {
    let area = 0;
    for (let index = 0; index < corners.length; index++) {
      const next = corners[(index + 1) % corners.length];
      area += corners[index].x * next.y - next.x * corners[index].y;
    }
    return Math.abs(area / 2);
  }

  function drawPolygon(corners, color, width) {
    context.beginPath();
    context.moveTo(corners[0].x, corners[0].y);
    corners.slice(1).forEach(corner => context.lineTo(corner.x, corner.y));
    context.closePath();
    context.lineWidth = width;
    context.strokeStyle = color;
    context.stroke();
  }

  function drawMarker(marker) {
    const corners = marker.corners;
    drawPolygon(corners, '#20e679', Math.max(3, canvas.width / 180));
    corners.forEach((corner, index) => {
      context.beginPath();
      context.arc(corner.x, corner.y, Math.max(4, canvas.width / 130), 0, Math.PI * 2);
      context.fillStyle = index === 0 ? '#ffcc29' : '#20e679';
      context.fill();
    });

    const label = `ID ${marker.id}`;
    const fontSize = Math.max(16, Math.round(canvas.width / 32));
    context.font = `900 ${fontSize}px system-ui, sans-serif`;
    const padding = Math.round(fontSize * 0.45);
    const textWidth = context.measureText(label).width;
    const x = Math.max(4, Math.min(corners[0].x, canvas.width - textWidth - padding * 2 - 4));
    const y = Math.max(fontSize + padding, corners[0].y - 8);
    context.fillStyle = '#20e679';
    context.fillRect(x, y - fontSize - padding, textWidth + padding * 2, fontSize + padding * 1.45);
    context.fillStyle = '#07160e';
    context.fillText(label, x + padding, y - padding * 0.35);
  }

  function drawCandidates() {
    if (!candidateToggle.checked || !detector) return;
    detector.candidates.forEach(candidate => drawPolygon(candidate, 'rgba(255,204,41,.6)', 1.5));
  }

  function renderResults(markers) {
    if (!markers.length) {
      foundList.innerHTML = '<p class="empty-result">Маркеры пока не найдены.</p>';
      status.textContent = running
        ? 'Ищем маркеры во всём кадре. Покажите камере распечатанный или открытый на другом экране маркер.'
        : 'На изображении не найдено маркеров выбранного словаря.';
      status.classList.remove('success');
      return;
    }

    markers.sort((first, second) => polygonArea(second.corners) - polygonArea(first.corners));
    foundList.innerHTML = markers.map(marker =>
      `<div class="found-marker"><span>${dictionarySelect.value}</span><strong>ID ${marker.id}</strong><small>ошибок битов: ${marker.hammingDistance}</small></div>`
    ).join('');
    status.textContent = markers.length === 1
      ? `Маркер найден: ID ${markers[0].id}.`
      : `Найдено маркеров: ${markers.length}.`;
    status.classList.add('success');

    const reportKey = markers.map(marker => marker.id).sort((a, b) => a - b).join(',');
    if (reportKey !== lastReported) {
      lastReported = reportKey;
      window.arucoGoal?.('marker_detected', {dict: dictionarySelect.value, ids: reportKey, count: markers.length});
    }
  }

  function detectCurrentFrame() {
    const image = context.getImageData(0, 0, canvas.width, canvas.height);
    const markers = detector.detect(image);
    drawCandidates();
    markers.forEach(drawMarker);
    renderResults(markers);
  }

  function loop(time) {
    if (!running) return;
    animationId = requestAnimationFrame(loop);
    if (!video.videoWidth || time - lastFrameTime < 90) return;
    lastFrameTime = time;
    if (canvas.width === 2 || Math.abs(canvas.width / canvas.height - video.videoWidth / video.videoHeight) > 0.02) {
      fitCanvas(video.videoWidth, video.videoHeight);
    }

    context.save();
    if (facing === 'user') {
      context.translate(canvas.width, 0);
      context.scale(-1, 1);
    }
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    context.restore();
    detectCurrentFrame();
  }

  function stopCamera(updateStatus = true) {
    running = false;
    cancelAnimationFrame(animationId);
    if (stream) stream.getTracks().forEach(track => track.stop());
    stream = null;
    video.srcObject = null;
    if (updateStatus) status.textContent = 'Камера остановлена.';
  }

  async function startCamera() {
    stopCamera(false);
    lastReported = '';
    status.textContent = 'Запрашиваем доступ к камере…';
    status.classList.remove('success');
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        video: {facingMode: {ideal: facing}, width: {ideal: 1280}, height: {ideal: 720}},
        audio: false
      });
      video.srcObject = stream;
      await video.play();
      fitCanvas(video.videoWidth, video.videoHeight);
      const settings = stream.getVideoTracks()[0]?.getSettings?.() || {};
      if (settings.facingMode) facing = settings.facingMode;
      switchButton.textContent = facing === 'environment' ? 'На фронтальную' : 'На заднюю';
      running = true;
      animationId = requestAnimationFrame(loop);
      window.arucoGoal?.('detector_camera_start', {facing});
    } catch (error) {
      status.textContent = `Не удалось открыть камеру: ${error.name || 'ошибка'}. Проверьте разрешение браузера; камера работает только по HTTPS или на localhost.`;
    }
  }

  startButton.addEventListener('click', startCamera);
  stopButton.addEventListener('click', () => stopCamera(true));
  switchButton.addEventListener('click', async () => {
    facing = facing === 'environment' ? 'user' : 'environment';
    await startCamera();
    window.arucoGoal?.('detector_camera_switch', {facing});
  });
  dictionarySelect.addEventListener('change', () => {
    createDetector();
    lastReported = '';
  });
  fileInput.addEventListener('change', () => {
    const file = fileInput.files?.[0];
    if (!file) return;
    stopCamera(false);
    if (staticImageUrl) URL.revokeObjectURL(staticImageUrl);
    staticImageUrl = URL.createObjectURL(file);
    const image = new Image();
    image.onload = () => {
      fitCanvas(image.naturalWidth, image.naturalHeight);
      context.drawImage(image, 0, 0, canvas.width, canvas.height);
      lastReported = '';
      detectCurrentFrame();
      URL.revokeObjectURL(staticImageUrl);
      staticImageUrl = '';
      window.arucoGoal?.('detector_image_load', {type: file.type || ''});
    };
    image.onerror = () => { status.textContent = 'Не удалось прочитать изображение.'; };
    image.src = staticImageUrl;
  });

  canvas.width = 2;
  canvas.height = 2;
  createDetector();
})();
