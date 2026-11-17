(() => {
  const D = window.ARUCO_DICTS;
  const q = id => document.getElementById(id);
  const MARKER_TO_SQUARE_RATIO = 0.7;
  const ui = {
    dict: q("charucoDict"), sx: q("squaresX"), sy: q("squaresY"), square: q("squareMm"), start: q("startId"),
    preview: q("charucoPreview"), status: q("charucoStatus"), code: q("charucoCode"),
    download: q("downloadCharuco"), print: q("printCharuco"), pdf: q("pdfCharuco"), paper: q("charucoPaper"), margin: q("charucoMargin")
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
    const sx = Number(ui.sx.value), sy = Number(ui.sy.value);
    const square = Number(ui.square.value), start = Number(ui.start.value);
    if (!Number.isInteger(sx) || !Number.isInteger(sy) || sx < 2 || sy < 2 || sx > 500 || sy > 500)
      throw new Error("Количество клеток по каждой стороне: целое число от 2 до 500.");
    if (!Number.isFinite(square) || square <= 0 || square > 10000)
      throw new Error("Размер клетки должен быть больше 0 и не больше 10 000 мм.");
    const count = Math.floor(sx * sy / 2);
    if (count > d.count) throw new Error(`Нужно ${count} уникальных маркеров, а в словаре ${d.count}. Уменьшите количество клеток.`);
    if (!Number.isInteger(start) || start < 0 || start + count > d.count)
      throw new Error(`Нужно ${count} уникальных маркеров. В словаре ${d.count}; начальный ID должен быть от 0 до ${d.count - count}. Уменьшите число клеток или уменьшите начальный ID.`);
    const marker = square * MARKER_TO_SQUARE_RATIO;
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
    const squareM = String(v.square / 1000), markerM = String(v.marker / 1000);
    const idsCode = v.start === 0 ? "" : `\nimport numpy as np\nmarker_count = ${board.count}\nids = np.arange(${v.start}, ${v.start + board.count}, dtype=np.int32)\n`;
    const boardArgs = v.start === 0
      ? `(${v.sx}, ${v.sy}), ${squareM}, ${markerM}, dictionary`
      : `(${v.sx}, ${v.sy}), ${squareM}, ${markerM}, dictionary, ids`;
    const code = `import cv2${idsCode}\naruco = cv2.aruco\ndictionary = aruco.getPredefinedDictionary(aruco.${v.dictName})\nboard = aruco.CharucoBoard(${boardArgs})\nif hasattr(board, "setLegacyPattern"):\n    board.setLegacyPattern(False)  # шаблон OpenCV 4.6+\nimage = board.generateImage((${v.sx * 250}, ${v.sy * 250}), marginSize=0, borderBits=1)\ncv2.imwrite("charuco_board.png", image)\n`;
    return {...v, ...board, code};
  }

  function pageLayout(v) {
    const margin = Number(ui.margin.value);
    if (!Number.isFinite(margin) || margin < 5 || margin > 100) throw new Error("Поля: от 5 до 100 мм.");
    const paper = ui.paper.value;
    const width = paper === "custom" ? v.width + 2 * margin : paper === "a3" ? 297 : 210;
    const height = paper === "custom" ? Math.max(width, v.height + 2 * margin + 10) : paper === "a3" ? 420 : 297;
    return {width, height, margin, fits: v.width <= width - 2 * margin + 1e-8 && v.height <= height - 2 * margin - 10 + 1e-8};
  }

  function render() {
    try {
      const result = build(), page = pageLayout(result);
      ui.preview.innerHTML = result.svg;
      ui.code.textContent = result.code;
      ui.status.textContent = `${result.sx}×${result.sy} клеток · доска ${+result.width.toFixed(3)}×${+result.height.toFixed(3)} мм · маркер ${+result.marker.toFixed(3)} мм · ${result.count} маркеров. ` +
        (page.fits ? `Лист ${+page.width.toFixed(3)}×${+page.height.toFixed(3)} мм, поля ${page.margin} мм. Печатайте в масштабе 100%.` : "Доска не помещается: выберите больший лист, лист по размеру доски или уменьшите клетку. Масштаб не меняется.");
      ui.download.disabled = false;
      ui.pdf.disabled = ui.print.disabled = !page.fits;
      return {result, page};
    } catch (error) {
      ui.status.textContent = error.message;
      ui.preview.replaceChildren();
      ui.code.textContent = "Исправьте параметры доски.";
      ui.download.disabled = ui.pdf.disabled = ui.print.disabled = true;
      return null;
    }
  }

  // A vector PDF: dimensions and every rectangle use physical millimetres.
  function pdfBlob(v, page) {
    const unit = Math.max(1, Math.max(page.width, page.height) / 5000);
    const pt = mm => mm * 72 / 25.4 / unit;
    const f = n => Number(n.toFixed(6));
    const x0 = (page.width - v.width) / 2, y0 = page.margin;
    let stream = "q\n";
    const svg = new DOMParser().parseFromString(v.svg, "image/svg+xml");
    for (const rect of svg.querySelectorAll("rect")) {
      const n = name => Number(rect.getAttribute(name) || 0);
      stream += `${rect.getAttribute("fill") === "#000" ? 0 : 1} g ${f(pt(x0 + n("x")))} ${f(pt(page.height - y0 - n("y") - n("height")))} ${f(pt(n("width")))} ${f(pt(n("height")))} re f\n`;
    }
    stream += `Q\nBT /F1 ${f(9 / unit)} Tf 0.35 g ${f(pt(page.width / 2 - 8))} ${f(pt(page.margin))} Td (aruco.ru) Tj ET\n`;
    const objects = ["<< /Type /Catalog /Pages 2 0 R >>", "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
      `<< /Type /Page /Parent 2 0 R /UserUnit ${f(unit)} /MediaBox [0 0 ${f(pt(page.width))} ${f(pt(page.height))}] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>`,
      "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>", `<< /Length ${stream.length} >>\nstream\n${stream}endstream`];
    let pdf = "%PDF-1.6\n", offsets = [0];
    objects.forEach((obj, i) => { offsets.push(pdf.length); pdf += `${i + 1} 0 obj\n${obj}\nendobj\n`; });
    const xref = pdf.length;
    pdf += `xref\n0 6\n0000000000 65535 f \n` + offsets.slice(1).map(n => `${String(n).padStart(10, "0")} 00000 n \n`).join("") + `trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n${xref}\n%%EOF\n`;
    return new Blob([pdf], {type: "application/pdf"});
  }

  function download(blob, filename) {
    const url = URL.createObjectURL(blob), link = document.createElement("a");
    link.href = url; link.download = filename; link.click();
    setTimeout(() => URL.revokeObjectURL(url), 10000);
  }
  ui.pdf.addEventListener("click", () => {
    const state = render();
    if (state?.page.fits) download(pdfBlob(state.result, state.page), `charuco_${state.result.sx}x${state.result.sy}.pdf`);
  });
  function preparePrint() {
    const state = render();
    let pages = q("charucoPrintPage");
    if (!pages) { pages = document.createElement("section"); pages.id = "charucoPrintPage"; document.body.appendChild(pages); }
    pages.replaceChildren();
    if (!state?.page.fits) return;
    const {result, page} = state;
    let style = q("charucoPageStyle");
    if (!style) { style = document.createElement("style"); style.id = "charucoPageStyle"; document.head.appendChild(style); }
    style.textContent = `@page charuco-sheet {size:${page.width}mm ${page.height}mm;margin:0}`;
    pages.style.cssText = `width:${page.width}mm;height:${page.height}mm;padding:${page.margin}mm;`;
    pages.innerHTML = result.svg + '<div class="charuco-print-footer">aruco.ru</div>';
  }
  window.addEventListener("beforeprint", preparePrint);

  ui.download.addEventListener("click", () => {
    const state = render();
    if (!state) return;
    const result = state.result, exportSvg = boardSvg(result, true).svg;
    const blob = new Blob([exportSvg], {type: "image/svg+xml;charset=utf-8"});
    const url = URL.createObjectURL(blob), link = document.createElement("a");
    link.href = url;
    link.download = `charuco_${result.sx}x${result.sy}_${result.dictName}.svg`;
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    window.arucoGoal?.("charuco_svg", {dict: result.dictName});
  });
  ui.print.addEventListener("click", () => {
    if (!render()?.page.fits) return;
    preparePrint();
    window.arucoGoal?.("charuco_print", {dict: ui.dict.value});
    window.print();
  });
  ["charucoDict", "squaresX", "squaresY", "squareMm", "startId", "charucoPaper", "charucoMargin"].forEach(id => q(id).addEventListener("change", () => {
    const state = render();
    if (state) window.arucoGoal?.("charuco_generate", {dict: state.result.dictName, squares_x: state.result.sx, squares_y: state.result.sy, square_mm: state.result.square});
  }));
  render();
})();
