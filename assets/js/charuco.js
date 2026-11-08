(() => {
  const D = window.ARUCO_DICTS;
  const q = id => document.getElementById(id);
  const MARKER_TO_SQUARE_RATIO = 0.7;
  const ui = {
    dict: q("charucoDict"), sx: q("squaresX"), sy: q("squaresY"), square: q("squareMm"), start: q("startId"),
    preview: q("charucoPreview"), status: q("charucoStatus"), code: q("charucoCode"),
    download: q("downloadCharuco"), print: q("printCharuco")
  };

  function markerGroup(dictName, id, x, y, size) {
    const d = D[dictName], n = d.size, bits = d.markers[id], total = n + 2, module = size / total;
    let svg = `<g><rect x="${x}" y="${y}" width="${size}" height="${size}" fill="#000"/>`;
    for (let row = 0; row < n; row++) for (let col = 0; col < n; col++) {
      if (bits[row * n + col] === "1") {
        svg += `<rect x="${x + (col + 1) * module}" y="${y + (row + 1) * module}" width="${module}" height="${module}" fill="#fff"/>`;
      }
    }
    return svg + "</g>";
  }

  function values() {
    const dictName = ui.dict.value, d = D[dictName];
    const sx = Math.max(3, Math.min(16, parseInt(ui.sx.value || 5, 10)));
    const sy = Math.max(3, Math.min(20, parseInt(ui.sy.value || 7, 10)));
    const square = Math.max(10, Math.min(80, parseFloat(ui.square.value || 35)));
    const marker = square * MARKER_TO_SQUARE_RATIO;
    const start = Math.max(0, Math.min(d.count - 1, parseInt(ui.start.value || 0, 10)));
    ui.sx.value = sx;
    ui.sy.value = sy;
    ui.square.value = square;
    ui.start.value = start;
    return {dictName, d, sx, sy, square, marker, start, width: sx * square, height: sy * square};
  }

  function boardSvg(v, includeFooter = false) {
    const footerH = includeFooter ? 8 : 0, totalHeight = v.height + footerH;
    let svg = `<svg class="charuco-board" xmlns="http://www.w3.org/2000/svg" width="${v.width}mm" height="${totalHeight}mm" viewBox="0 0 ${v.width} ${totalHeight}" shape-rendering="crispEdges">`;
    svg += `<rect width="${v.width}" height="${totalHeight}" fill="#fff"/>`;
    let id = v.start, count = 0;
    for (let row = 0; row < v.sy; row++) for (let col = 0; col < v.sx; col++) {
      const x = col * v.square, y = row * v.square;
      if ((row + col) % 2 === 0) {
        svg += `<rect x="${x}" y="${y}" width="${v.square}" height="${v.square}" fill="#000"/>`;
      } else if (id < v.d.count) {
        const offset = (v.square - v.marker) / 2;
        svg += markerGroup(v.dictName, id, x + offset, y + offset, v.marker);
        id++;
        count++;
      }
    }
    if (includeFooter) {
      svg += `<text x="${v.width / 2}" y="${totalHeight - 2.2}" text-anchor="middle" font-family="Arial,sans-serif" font-size="3" fill="#555">aruco.ru</text>`;
    }
    return {svg: svg + "</svg>", count};
  }

  function build() {
    const v = values(), board = boardSvg(v, false);
    const squareM = (v.square / 1000).toFixed(6), markerM = (v.marker / 1000).toFixed(6);
    const idsCode = v.start === 0 ? "" : `\nimport numpy as np\nmarker_count = ${board.count}\nids = np.arange(${v.start}, ${v.start + board.count}, dtype=np.int32)\n`;
    const boardArgs = v.start === 0
      ? `(${v.sx}, ${v.sy}), ${squareM}, ${markerM}, dictionary`
      : `(${v.sx}, ${v.sy}), ${squareM}, ${markerM}, dictionary, ids`;
    const code = `import cv2${idsCode}\naruco = cv2.aruco\ndictionary = aruco.getPredefinedDictionary(aruco.${v.dictName})\nboard = aruco.CharucoBoard(${boardArgs})\nif hasattr(board, "setLegacyPattern"):\n    board.setLegacyPattern(False)  # шаблон OpenCV 4.6+\nimage = board.generateImage((${v.sx * 250}, ${v.sy * 250}), marginSize=0, borderBits=1)\ncv2.imwrite("charuco_board.png", image)\n`;
    return {...v, ...board, code};
  }

  function render() {
    const result = build();
    ui.preview.innerHTML = result.svg;
    ui.code.textContent = result.code;
    const fitsA4 = result.width <= 194 && result.height <= 273;
    ui.status.innerHTML = `${result.sx}×${result.sy} клеток · доска ${result.width}×${result.height} мм · клетка ${result.square} мм · ${result.count} маркеров<br><strong>${fitsA4 ? "Помещается на A4 при масштабе 100%." : "Не помещается на A4 без уменьшения — выберите A3 или уменьшите клетку."}</strong>`;
    window.arucoGoal?.("charuco_generate", {dict: result.dictName, squares_x: result.sx, squares_y: result.sy, square_mm: result.square});
  }

  ui.download.addEventListener("click", () => {
    const result = build(), exportSvg = boardSvg(result, true).svg;
    const blob = new Blob([exportSvg], {type: "image/svg+xml;charset=utf-8"});
    const url = URL.createObjectURL(blob), link = document.createElement("a");
    link.href = url;
    link.download = `charuco_${result.sx}x${result.sy}_${result.dictName}.svg`;
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    window.arucoGoal?.("charuco_svg", {dict: result.dictName});
  });
  ui.print.addEventListener("click", () => {
    window.arucoGoal?.("charuco_print", {dict: ui.dict.value});
    window.print();
  });
  ["charucoDict", "squaresX", "squaresY", "squareMm", "startId"].forEach(id => q(id).addEventListener("change", render));
  render();
})();
