(() => {
  "use strict";

  const UI = {
    dict: document.getElementById("dict"),
    idFrom: document.getElementById("idFrom"),
    idTo: document.getElementById("idTo"),
    copies: document.getElementById("copies"),
    outerMm: document.getElementById("outerMm"),
    blackMm: document.getElementById("blackMm"),
    whiteBorderValue: document.getElementById("whiteBorderValue"),
    showId: document.getElementById("showId"),
    cutLine: document.getElementById("cutLine"),
    labels: document.getElementById("labels"),
    sheet: document.getElementById("markerSheet"),
    status: document.getElementById("status"),
    generateBtn: document.getElementById("generateBtn"),
    printBtn: document.getElementById("printBtn")
  };

  let sizeEditSource = "outer";
  const clamp = (n, min, max) => Math.max(min, Math.min(max, n));
  const round2 = n => Math.round(n * 100) / 100;
  const cleanNumber = n => String(Number(round2(n).toFixed(2)));

  // Формула из переданного рабочего генератора: чёрный квадрат содержит код
  // и чёрную рамку, внешний размер — ещё по одному белому модулю с каждой стороны.
  function sizeRatio() {
    const dict = window.ARUCO_DICTS[UI.dict.value];
    return (dict.size + 4) / (dict.size + 2);
  }

  function updateWhiteBorder() {
    const border = Math.max(0, (Number(UI.outerMm.value) - Number(UI.blackMm.value)) / 2);
    UI.whiteBorderValue.textContent = border.toFixed(border % 1 ? 1 : 0);
  }

  function linkedSizesFromOuter() {
    const outer = clamp(parseFloat(UI.outerMm.value || 60), 20, 140);
    UI.outerMm.value = cleanNumber(outer);
    UI.blackMm.value = cleanNumber(outer / sizeRatio());
    updateWhiteBorder();
  }

  function linkedSizesFromBlack() {
    const black = clamp(parseFloat(UI.blackMm.value || 45), 10, 120);
    UI.blackMm.value = cleanNumber(black);
    UI.outerMm.value = cleanNumber(clamp(black * sizeRatio(), 20, 140));
    updateWhiteBorder();
  }

  function resyncSizes() {
    if (sizeEditSource === "black") linkedSizesFromBlack();
    else linkedSizesFromOuter();
  }

  function markerSvg(dictName, id) {
    const dict = window.ARUCO_DICTS[dictName];
    const n = dict.size;
    const bits = dict.markers[id];
    const total = n + 2;
    let svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${total} ${total}" shape-rendering="crispEdges" aria-label="${dictName} ID ${id}">`;
    svg += `<rect width="${total}" height="${total}" fill="#000"/>`;
    for (let row = 0; row < n; row++) for (let col = 0; col < n; col++) {
      if (bits[row * n + col] === "1") {
        svg += `<rect x="${col + 1}" y="${row + 1}" width="1" height="1" fill="#fff"/>`;
      }
    }
    return svg + "</svg>";
  }

  function escapeXml(value) {
    return String(value).replace(/[<>&'\"]/g, character => ({
      "<": "&lt;", ">": "&gt;", "&": "&amp;", "'": "&apos;", '"': "&quot;"
    }[character]));
  }

  function cardSvg(dictName, id, label, outerMm, blackMm, cutLine, showId) {
    const dict = window.ARUCO_DICTS[dictName];
    const n = dict.size;
    const bits = dict.markers[id];
    const total = n + 2;
    const offset = (outerMm - blackMm) / 2;
    const module = blackMm / total;
    const dash = cutLine ? `stroke-dasharray="1.2 1.2"` : "";
    let svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${outerMm}mm" height="${outerMm}mm" viewBox="0 0 ${outerMm} ${outerMm}" shape-rendering="crispEdges">`;
    svg += `<rect x=".1" y=".1" width="${outerMm - 0.2}" height="${outerMm - 0.2}" fill="white" stroke="#777" stroke-width=".2" ${dash}/>`;
    svg += `<rect x="${offset}" y="${offset}" width="${blackMm}" height="${blackMm}" fill="#000"/>`;
    for (let row = 0; row < n; row++) for (let col = 0; col < n; col++) {
      if (bits[row * n + col] === "1") {
        svg += `<rect x="${offset + (col + 1) * module}" y="${offset + (row + 1) * module}" width="${module}" height="${module}" fill="white"/>`;
      }
    }
    const border = (outerMm - blackMm) / 2;
    const labelFont = Math.max(2.2, Math.min(4, border * 0.42));
    const idFont = Math.max(2.4, Math.min(4.2, border * 0.46));
    if (label) {
      svg += `<text x="${Math.max(1, border * 0.18)}" y="${Math.max(labelFont, border * 0.72)}" font-family="Arial,sans-serif" font-size="${labelFont}" font-weight="700">${escapeXml(label)}</text>`;
    }
    if (showId) {
      svg += `<text x="${outerMm - Math.max(1, border * 0.18)}" y="${outerMm - Math.max(1, border * 0.18)}" text-anchor="end" font-family="Arial,sans-serif" font-size="${idFont}" font-weight="700">ID ${id}</text>`;
    }
    return svg + "</svg>";
  }

  function downloadSvg(dictName, id, label, outerMm, blackMm) {
    const svg = cardSvg(dictName, id, label, outerMm, blackMm, UI.cutLine.checked, UI.showId.checked);
    const blob = new Blob([svg], {type: "image/svg+xml;charset=utf-8"});
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${dictName}_id_${id}_outer_${outerMm}mm_black_${blackMm}mm.svg`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    window.arucoGoal?.("generator_svg", {dict: dictName, id});
  }

  function generate() {
    const dictName = UI.dict.value;
    const dict = window.ARUCO_DICTS[dictName];
    resyncSizes();
    let from = clamp(parseInt(UI.idFrom.value || 0, 10), 0, dict.count - 1);
    let to = clamp(parseInt(UI.idTo.value || 0, 10), 0, dict.count - 1);
    if (to < from) [from, to] = [to, from];
    const copies = clamp(parseInt(UI.copies.value || 1, 10), 1, 20);
    const outerMm = clamp(parseFloat(UI.outerMm.value || 60), 20, 140);
    const blackMm = clamp(parseFloat(UI.blackMm.value || 45), 10, 120);
    const labels = UI.labels.value.split(/\r?\n/);
    UI.idFrom.value = from;
    UI.idTo.value = to;
    UI.copies.value = copies;
    UI.sheet.innerHTML = "";
    UI.sheet.style.setProperty("--outer-mm", `${outerMm}mm`);
    UI.sheet.style.setProperty("--black-mm", `${blackMm}mm`);
    const fragment = document.createDocumentFragment();
    let count = 0;
    for (let copy = 0; copy < copies; copy++) for (let id = from; id <= to; id++) {
      const custom = labels[id - from]?.trim() || "";
      const card = document.createElement("div");
      card.className = "marker-card" + (UI.cutLine.checked ? "" : " no-cut");
      card.style.setProperty("--outer-mm", `${outerMm}mm`);
      card.style.setProperty("--black-mm", `${blackMm}mm`);
      card.innerHTML =
        (custom ? `<div class="marker-custom-label">${escapeXml(custom)}</div>` : "") +
        markerSvg(dictName, id) +
        (UI.showId.checked ? `<div class="marker-label">ID ${id}</div>` : "") +
        `<button class="marker-download" type="button">SVG</button>`;
      card.querySelector(".marker-download").addEventListener("click", () => downloadSvg(dictName, id, custom, outerMm, blackMm));
      fragment.appendChild(card);
      count++;
    }
    UI.sheet.appendChild(fragment);
    const white = (outerMm - blackMm) / 2;
    UI.status.textContent = `${dictName} · ID ${from}–${to} · ${copies} ${copies === 1 ? "копия" : "копии/копий"} · внешний ${outerMm} мм · чёрный ${blackMm} мм · белое поле ${white.toFixed(1)} мм · всего ${count}`;
    window.arucoGoal?.("generator_use", {dict: dictName, from, to, copies, outer_mm: outerMm, black_mm: blackMm});
  }

  UI.generateBtn.addEventListener("click", generate);
  UI.printBtn.addEventListener("click", () => {
    window.arucoGoal?.("generator_print", {dict: UI.dict.value});
    window.print();
  });
  UI.outerMm.addEventListener("input", () => {
    sizeEditSource = "outer";
    linkedSizesFromOuter();
    generate();
  });
  UI.blackMm.addEventListener("input", () => {
    sizeEditSource = "black";
    linkedSizesFromBlack();
    generate();
  });
  UI.dict.addEventListener("change", () => {
    resyncSizes();
    generate();
  });
  [UI.idFrom, UI.idTo, UI.copies, UI.showId, UI.cutLine].forEach(element => element.addEventListener("change", generate));
  let labelTimer;
  UI.labels.addEventListener("input", () => {
    clearTimeout(labelTimer);
    labelTimer = setTimeout(generate, 250);
  });

  if (!window.ARUCO_DICTS) {
    UI.status.className = "status error";
    UI.status.textContent = "Не удалось загрузить локальные словари ArUco.";
  } else {
    linkedSizesFromOuter();
    generate();
  }
})();
