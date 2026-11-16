// build_deck.js - CS 259 presentation: EXACTLY 18 slides (no backup or appendix slides).
// All numbers come from presentation/slide_data.json (recomputed from results/raw by export_slide_data.py).
// Charts are native PowerPoint charts (editable); diagrams are native shapes. Error bars are added afterwards by add_error_bars.py
// from the sidecar presentation/errbars.json written here.
const pptxgen = require("pptxgenjs");
const fs = require("fs");
const path = require("path");
// apply_theme.js (theme writer of the pptx tooling) is found through PPTX_SKILL_DIR = the directory that contains scripts/apply_theme.js
const SKILL = process.env.PPTX_SKILL_DIR || "";
const { applyTheme } = require(path.join(SKILL, "scripts/apply_theme.js"));

const D = JSON.parse(fs.readFileSync(path.join(__dirname, "slide_data.json"), "utf8"));
const SER = D.series;
const DATE = process.env.PRESENTATION_DATE || "Presentation date: to be added";
const num = (k) => { if (!(k in D.num)) throw new Error("missing value " + k); return D.num[k]; };
const val = (k) => parseFloat(num(k).replace(/,/g, ""));
const f1 = (k) => val(k).toFixed(1);
const f2 = (k) => val(k).toFixed(2);
const B = SER.batches, iB = (b) => B.indexOf(b);
const r = (x, n = 1) => Number(x).toFixed(n);
const comma = (x) => Math.round(x).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");

// ---------- theme ----------
const THEME = { name: "CS259 Hybrid", headFontFace: "Cambria", bodyFontFace: "Calibri",
  colors: { dk1: "1F2937", lt1: "FFFFFF", dk2: "0F172A", lt2: "F3F4F6", accent1: "2563EB", accent2: "16A34A", accent3: "7C3AED", accent4: "C2570C", accent5: "4B5563", accent6: "F0A36B", hlink: "2563EB", folHlink: "7C3AED" } };
const NAVY = "0F172A", INK = "1F2937", MUTED = "4B5563", LIGHT = "F3F4F6", BLUE = "2563EB", GREEN = "16A34A", PURPLE = "7C3AED", LPURPLE = "A78BFA", ORANGE = "C2570C", LORANGE = "F0A36B", GRAY = "4B5563", LGRAY = "9CA3AF", TEAL = "0F766E";

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9"; // 10 x 5.625 in
pres.author = "Sunnihith Reddy Induru";
pres.title = "Performance Evaluation of Hybrid CPU-GPU Parallelism for Deep Learning Using OpenMP and CUDA";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.defineSlideMaster({ title: "TITLE", background: { color: NAVY }, objects: [
  { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 1.0, w: 8.8, h: 1.9, fontFace: "Cambria", fontSize: 32, bold: true, color: "FFFFFF", valign: "middle", margin: 0 }, text: "" } },
  { placeholder: { options: { name: "body", type: "body", x: 0.6, y: 3.2, w: 8.8, h: 1.6, fontFace: "Calibri", fontSize: 18, color: "CBD5E1", valign: "top", margin: 0 }, text: "" } }] });
pres.defineSlideMaster({ title: "CONTENT", background: { color: "FFFFFF" }, objects: [
  { placeholder: { options: { name: "title", type: "title", x: 0.45, y: 0.2, w: 9.1, h: 0.85, fontFace: "Cambria", fontSize: 26, bold: true, color: NAVY, valign: "middle", margin: 0 }, text: "" } }],
  slideNumber: { x: 9.1, y: 5.3, w: 0.5, h: 0.25, fontFace: "Calibri", fontSize: 10, color: "6B7280", align: "right" } });
pres.defineSlideMaster({ title: "DARK", background: { color: NAVY }, objects: [
  { placeholder: { options: { name: "title", type: "title", x: 0.45, y: 0.2, w: 9.1, h: 0.85, fontFace: "Cambria", fontSize: 26, bold: true, color: "FFFFFF", valign: "middle", margin: 0 }, text: "" } }],
  slideNumber: { x: 9.1, y: 5.3, w: 0.5, h: 0.25, fontFace: "Calibri", fontSize: 10, color: "9CA3AF", align: "right" } });

// ---------- helpers ----------
const LOG = []; const ERR = []; let slideNo = 0;
function addSlide(master, section, title, minutes, purpose, visual, notes, text) {
  minutes = Math.max(0.5, Math.ceil(notes.split(/\s+/).length / 145 * 4) / 4);   // spoken length of the notes at ~145 words per minute
  slideNo++;
  const s = pres.addSlide({ masterName: master, sectionTitle: section });
  s.addText(title, { placeholder: "title" });
  s.addNotes(`[Estimated speaking time: ${minutes} min]\n[Purpose: ${purpose}]\n\n${notes}`);
  LOG.push({ n: slideNo, section, title, minutes, purpose, visual, notes, text: text || "" });
  s._chartCount = 0; s._no = slideNo;
  return s;
}
const T = (s, text, x, y, w, h, o = {}) => s.addText(text, Object.assign({ x, y, w, h, fontFace: "Calibri", fontSize: 14, color: INK, margin: 0, valign: "top", isTextBox: true }, o));
function box(s, x, y, w, h, text, fill, o = {}) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: fill }, line: { color: o.line || fill, width: 1 }, rectRadius: 0.05 });
  if (text) T(s, text, x, y, w, h, { align: "center", valign: "middle", fontSize: o.fs || 12, bold: !!o.bold, color: o.color || "FFFFFF", margin: 0.03 });
}
function arrow(s, x1, y1, x2, y2, color = INK, wd = 1.5) {
  s.addShape(pres.shapes.LINE, { x: Math.min(x1, x2), y: Math.min(y1, y2), w: Math.abs(x2 - x1), h: Math.abs(y2 - y1), flipH: x2 < x1, flipV: y2 < y1, line: { color, width: wd, endArrowType: "triangle" } });
}
function card(s, x, y, w, h, big, label, color, o = {}) {
  const bs = o.bigSize || 36, ls = o.labelSize || 13, bh = o.bigH || h * 0.5;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: LIGHT }, line: { color: LIGHT }, rectRadius: 0.08 });
  T(s, big, x, y + 0.06, w, bh, { align: "center", valign: "middle", fontFace: "Cambria", fontSize: bs, bold: true, color });
  T(s, label, x + 0.1, y + 0.06 + bh, w - 0.2, h - bh - 0.12, { align: "center", fontSize: ls });
}
function bullets(s, items, x, y, w, h, o = {}) {
  const runs = items.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < items.length - 1, paraSpaceAfter: 5 } }));
  T(s, runs, x, y, w, h, Object.assign({ fontSize: 14 }, o));
}
function table(s, rows, x, y, w, colW, fs = 12, o = {}) {
  const data = rows.map((rw, i) => rw.map((c) => ({ text: String(c), options: { bold: i === 0, color: i === 0 ? "FFFFFF" : INK, fill: { color: i === 0 ? NAVY : (i % 2 ? "FFFFFF" : LIGHT) }, fontFace: "Calibri", fontSize: fs, valign: "middle", margin: [0.03, 0.06, 0.03, 0.06] } })));
  s.addTable(data, Object.assign({ x, y, w, colW, border: { type: "solid", pt: 0.5, color: "D1D5DB" }, rowH: o.rowH || 0.3 }, o.tbl || {}));
}
// native chart + sidecar error-bar / dash record (applied to the XML by add_error_bars.py)
function chart(s, type, series, labels, o) {
  const data = series.map((se) => ({ name: se.name, labels, values: se.values }));
  const idx = s._chartCount++;
  const opts = Object.assign({ chartColors: series.map((se) => se.color), showLegend: true, legendPos: "b", legendFontSize: 11, legendColor: INK, legendFontFace: "Calibri",
    catAxisLabelFontSize: 11, valAxisLabelFontSize: 11, catAxisLabelColor: INK, valAxisLabelColor: INK, catAxisLabelFontFace: "Calibri", valAxisLabelFontFace: "Calibri",
    showTitle: true, titleFontSize: 13, titleColor: INK, titleFontFace: "Calibri", showCatAxisTitle: true, showValAxisTitle: true, catAxisTitleFontSize: 11, valAxisTitleFontSize: 11,
    catAxisTitleColor: INK, valAxisTitleColor: INK, valGridLine: { color: "E5E7EB", size: 0.5 }, catGridLine: { style: "none" } }, o);
  if (type === "line") Object.assign(opts, { lineSize: 2.25, lineDataSymbolSize: 7, lineDataSymbol: "circle" });
  s.addChart(type === "line" ? pres.charts.LINE : pres.charts.BAR, data, opts);
  const ci = {}, dash = {}; series.forEach((se) => { if (se.ci) ci[se.name] = se.ci; if (se.dash && se.dash !== "solid") dash[se.name] = se.dash; });
  if (Object.keys(ci).length || Object.keys(dash).length) ERR.push({ slide: s._no, chart: idx, ci, dash });
}
const CUDA = "CUDA pipeline (1-thread preprocessing)";
const lab = B.map(String);
const R4 = (a) => a.map((v) => +v.toFixed(3));
// derived series for the results slides (all from the measured per-pass means and 95 % CIs)
const speedup = (t, tci) => ({ v: SER.serial.map((ts, i) => ts / t[i]), ci: SER.serial.map((ts, i) => (ts / t[i]) * Math.sqrt((SER.serial_ci[i] / ts) ** 2 + (tci[i] / t[i]) ** 2)) });
const thruput = (t, tci) => ({ v: t.map((x) => 10000 / (x / 1000)), ci: t.map((x, i) => (10000 / (x / 1000)) * (tci[i] / x)) });

// ================================================ 18 SLIDES ================================================
pres.addSection({ title: "Introduction" });
// ---- 1 title
{
  slideNo++;
  const s = pres.addSlide({ masterName: "TITLE", sectionTitle: "Introduction" });
  s.addText("Performance Evaluation of Hybrid CPU–GPU Parallelism for Deep Learning Using OpenMP and CUDA", { placeholder: "title" });
  s.addText(`Sunnihith Reddy Induru\nCS 259 — Advanced Parallel Processing\nSan José State University\n${DATE}`, { placeholder: "body" });
  const notes = `Good morning, everyone. My project is called "Performance Evaluation of Hybrid CPU-GPU Parallelism for Deep Learning Using OpenMP and CUDA."\n\nThe project evaluates four execution approaches for exactly the same neural-network inference workload on MNIST digits: a serial CPU baseline, an OpenMP version that uses many CPU threads, a CUDA version that runs the network on the GPU, and a hybrid OpenMP-CUDA pipeline that uses the CPU and the GPU at the same time.\n\nI measured all four on the same machine, and I will tell you when each one is the right choice. One note before we start: every number in these slides was measured by me and can be traced back to the raw measurement files in my repository. I also use one extra configuration, called hybrid-sequential, but only as a diagnostic control - I will explain it when we reach the hybrid design.`;
  s.addNotes(`[Estimated speaking time: 1 min]\n[Purpose: Introduce the project and state that four execution approaches are compared on one workload.]\n\n${notes}`);
  LOG.push({ n: 1, section: "Introduction", title: "Title", minutes: 1, purpose: "Introduce the project and state that four execution approaches are compared on one workload.", visual: "Dark title slide, no diagram.", notes, text: `Performance Evaluation of Hybrid CPU–GPU Parallelism for Deep Learning Using OpenMP and CUDA; Sunnihith Reddy Induru; CS 259 — Advanced Parallel Processing; San José State University; ${DATE}` });
}
// ---- 2 motivation
{
  const s = addSlide("CONTENT", "Introduction", "Why Parallelism Matters for Deep Learning", 0,
    "Show why parallel execution is needed and plant the idea that a fast kernel is not a fast application.", "Four-box flow: workload → repeated operations → computation cost → CPU and GPU parallelism; callout with measured kernel-only vs end-to-end speedup.",
    `Neural-network inference is a large number of repeated mathematical operations - mostly matrix operations. My network does about two hundred thousand multiply-adds per image, and one pass does that for ten thousand images. As the workload grows, the computation cost grows with it, and on one CPU thread it becomes slow.

There are two standard remedies: OpenMP uses several CPU threads that share memory, and CUDA uses many thousands of GPU threads.

But a fast GPU kernel does not always mean a fast complete application. The application also pays for preprocessing, for copying data to and from the GPU, and for kernel-launch overhead. On my measurements the GPU kernels alone are ${f1("Sp:comp:gpuvsserial:4096")} times faster than serial, but the complete CUDA pipeline is only ${f1("Sp:cuda:speedup:4096")} times faster. The rest of the talk explains why, and what a hybrid design can do about it.`,
    "Workload → repeated operations → computation cost → CPU and GPU parallelism; fast kernel ≠ fast application.");
  const steps = ["Neural-network workload", "Repeated mathematical operations", "Large computation cost", "CPU and GPU parallelism"];
  const cols = [BLUE, GRAY, GREEN, PURPLE];
  steps.forEach((t, i) => { const x = 0.45 + i * 2.35; box(s, x, 1.3, 2.0, 1.0, t, cols[i], { fs: 14, bold: true }); if (i < 3) arrow(s, x + 2.0, 1.8, x + 2.35, 1.8, INK, 2); });
  bullets(s, ["Neural networks perform repeated matrix operations", "Serial execution becomes slow as workload size increases", "OpenMP uses multiple CPU threads", "CUDA uses many GPU threads", "A fast GPU kernel does not always mean a fast complete application: preprocessing, data transfer and kernel-launch overhead"], 0.45, 2.6, 5.4, 2.6, { fontSize: 14 });
  card(s, 6.1, 2.6, 3.45, 2.5, `${f1("Sp:comp:gpuvsserial:4096")}× vs ${f1("Sp:cuda:speedup:4096")}×`, `GPU kernels only vs the complete CUDA pipeline (speedup over serial, batch 4096, Spartan node)`, ORANGE, { bigSize: 26, labelSize: 13, bigH: 0.75 });
}
// ---- 3 problem statement
{
  const s = addSlide("CONTENT", "Introduction", "Performance Tradeoffs Across CPU, GPU, and Hybrid Execution", 1,
    "State the main question and the six research questions that organise the results.", "Highlighted question box and six numbered research questions.",
    `This is the question the whole project asks: how do serial CPU, OpenMP CPU, CUDA GPU, and hybrid OpenMP-CUDA implementations compare when they execute the same neural-network inference workload?\n\nTo answer it properly I broke it into six research questions. One: how much speedup does OpenMP provide over serial execution? Two: how does CUDA compare with CPU execution? Three: how does batch size affect performance? Four: how much GPU time is spent on memory transfer? Five: does hybrid execution improve end-to-end performance? And six: how do the results relate to Amdahl's law and parallel overhead?\n\nThe results slides answer these in order: slide 14 gives the end-to-end times, slide 15 speedup and throughput, slide 16 the CUDA overhead and the hybrid, and slide 17 connects everything to Amdahl's law.`,
    "Main question + RQ1–RQ6.");
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.45, y: 1.2, w: 9.1, h: 1.0, fill: { color: NAVY }, line: { color: NAVY }, rectRadius: 0.06 });
  T(s, "“How do serial CPU, OpenMP CPU, CUDA GPU, and hybrid OpenMP–CUDA implementations compare when executing the same neural-network inference workload?”", 0.65, 1.2, 8.7, 1.0, { fontSize: 16, color: "FFFFFF", valign: "middle", italic: true });
  const rq = ["How much speedup does OpenMP provide over serial execution?", "How does CUDA compare with CPU execution?", "How does batch size affect performance?", "How much GPU time is spent on memory transfer?", "Does hybrid execution improve end-to-end performance?", "How do the results relate to Amdahl’s Law and parallel overhead?"];
  const cc = [BLUE, GREEN, GRAY, ORANGE, PURPLE, INK];
  rq.forEach((t, i) => { const col = i % 2, row = Math.floor(i / 2), x = 0.45 + col * 4.65, y = 2.5 + row * 0.92;
    s.addShape(pres.shapes.OVAL, { x, y, w: 0.6, h: 0.6, fill: { color: cc[i] }, line: { color: cc[i] } });
    T(s, `${i + 1}`, x, y, 0.6, 0.6, { align: "center", valign: "middle", bold: true, color: "FFFFFF", fontSize: 18 });
    T(s, t, x + 0.75, y - 0.05, 3.75, 0.75, { fontSize: 14, valign: "middle" }); });
}
// ---- 4 objectives
{
  const s = addSlide("CONTENT", "Introduction", "Project Objectives", 0.75,
    "List what was built and measured, and stress that all implementations compute the same workload.", "Six numbered objectives and a highlighted fairness statement.",
    `Here is what I set out to do. One: implement a serial C++ baseline. Two: implement an OpenMP version for the CPU. Three: implement a CUDA version for the GPU. Four: implement a hybrid OpenMP-CUDA pipeline. Five: compare execution time, speedup, throughput, scalability, correctness and overhead across them. And six: determine which implementation is best for different batch sizes.\n\nThe point I want to stress at the bottom of the slide is fairness. All four implementations use the same input data, the same trained weights, the same network and the same mathematical workload. Only the execution model changes. That is what makes the comparison meaningful: any difference in time comes from how the work is executed, not from doing different work.`,
    "Six objectives; same data, weights, network, workload.");
  const obj = ["Implement a serial C++ CPU baseline", "Implement an OpenMP CPU version", "Implement a CUDA GPU version", "Implement a hybrid OpenMP–CUDA pipeline", "Compare execution time, speedup, throughput, scalability, correctness, and overhead", "Determine which implementation is best for different batch sizes"];
  const cc = [GRAY, BLUE, GREEN, PURPLE, ORANGE, INK];
  obj.forEach((t, i) => { const col = i % 2, row = Math.floor(i / 2), x = 0.45 + col * 4.65, y = 1.3 + row * 1.05;
    s.addShape(pres.shapes.OVAL, { x, y, w: 0.62, h: 0.62, fill: { color: cc[i] }, line: { color: cc[i] } });
    T(s, `${i + 1}`, x, y, 0.62, 0.62, { align: "center", valign: "middle", bold: true, color: "FFFFFF", fontSize: 18 });
    T(s, t, x + 0.78, y - 0.08, 3.7, 0.85, { fontSize: 15, valign: "middle" }); });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.45, y: 4.5, w: 9.1, h: 0.7, fill: { color: NAVY }, line: { color: NAVY }, rectRadius: 0.06 });
  T(s, "All implementations use the same input data, weights, network, and mathematical workload.", 0.65, 4.5, 8.7, 0.7, { fontSize: 16, bold: true, color: "FFFFFF", valign: "middle" });
}
pres.addSection({ title: "Background and Method" });
// ---- 5 background
{
  const s = addSlide("CONTENT", "Background and Method", "CPU, OpenMP, GPU, and CUDA", 1.25,
    "Teach the four execution models (resource, memory model, parallelism) before any results.", "Four-row comparison table with a small 'workers' diagram per model.",
    `Before the results, I want everyone to understand how these four models differ, because the results only make sense with that picture in mind.\n\nSerial CPU: one CPU worker, one thread, doing the work strictly one piece after another, in shared CPU memory. OpenMP CPU: several CPU workers - threads - sharing the same CPU memory; the work is divided among them, with synchronization points between dependent steps. CUDA GPU: many, many GPU workers, but with a separate GPU memory, so data has to be copied there first; the parallelism is massive data parallelism - the same instructions on thousands of independent pieces of data. Hybrid: the CPU and the GPU working together, with coordinated parallelism - the CPU workers prepare the data while the GPU workers compute - and memory split between host and device.\n\nThe small pictures in the last column show the idea: one worker; several workers forked from a master and joined again; a big grid of tiny GPU workers; and a CPU worker feeding a GPU.`,
    "Table: model / main resource / memory model / parallelism + mini diagrams.");
  const rows = [["Model", "Main resource", "Memory model", "Parallelism", "Workers"],
    ["Serial CPU", "One CPU thread", "Shared CPU memory", "Sequential", ""], ["OpenMP CPU", "Multiple CPU threads", "Shared CPU memory", "CPU thread parallelism", ""],
    ["CUDA GPU", "Many GPU threads", "Separate GPU memory", "Massive data parallelism", ""], ["Hybrid", "CPU and GPU", "Host and device memory", "Coordinated parallelism", ""]];
  table(s, rows, 0.3, 1.15, 9.4, [1.4, 1.9, 2.1, 2.0, 2.0], 13, { rowH: [0.4, 0.8, 0.8, 0.8, 0.8] });
  const rowY = (i) => 1.15 + 0.4 + 0.8 * i; const dx = 7.75;
  for (let k = 0; k < 4; k++) box(s, dx + k * 0.42, rowY(0) + 0.27, 0.34, 0.26, `${k + 1}`, GRAY, { fs: 10 });
  box(s, dx, rowY(1) + 0.27, 0.34, 0.26, "M", BLUE, { fs: 10 });
  for (let k = 0; k < 3; k++) box(s, dx + 0.5, rowY(1) + 0.1 + k * 0.2, 0.8, 0.15, "", BLUE);
  box(s, dx + 1.46, rowY(1) + 0.27, 0.34, 0.26, "M", BLUE, { fs: 10 });
  for (let a = 0; a < 6; a++) for (let b = 0; b < 3; b++) box(s, dx + a * 0.3, rowY(2) + 0.12 + b * 0.19, 0.24, 0.14, "", GREEN);
  box(s, dx, rowY(3) + 0.2, 0.55, 0.4, "CPU", BLUE, { fs: 10 }); arrow(s, dx + 0.55, rowY(3) + 0.4, dx + 0.85, rowY(3) + 0.4, INK, 1.5);
  for (let a = 0; a < 4; a++) for (let b = 0; b < 3; b++) box(s, dx + 0.9 + a * 0.24, rowY(3) + 0.12 + b * 0.19, 0.2, 0.14, "", GREEN);
  T(s, "Serial: one worker, one piece at a time.  OpenMP: fork → parallel work → join (M = main thread).  CUDA: a grid of GPU workers.  Hybrid: CPU and GPU working together.", 0.3, 4.9, 9.4, 0.45, { fontSize: 12, color: MUTED });
}
// ---- 6 dataset and network
{
  const s = addSlide("CONTENT", "Background and Method", "MNIST Dataset and Neural-Network Workload", 0,
    "Define the workload: data, network architecture, precision, batch sizes and the fact that inference (not training) is measured.", "Image → pixels → features → network → digit flow, network architecture row, and fact list.",
    `The workload is MNIST digit classification - inference only, no training. The image is the first real test image: 28 by 28 pixels, so 784 input features, and the network predicts seven, which is also its true label.

The architecture is small: 784 inputs, a hidden layer of 256 units, a ReLU, an output layer of 10 units, and an argmax that picks the digit. Everything is float32.

Every pass processes all ten thousand test images, in batches of 1, 8, 32, 64, 128, 256, 1,024 or 4,096. All implementations load the same trained weights, and the model classifies ${num("Sp:accuracy")} percent correctly - confirmed by my training log and the correctness runs.

I chose MNIST because it is realistic but small enough to implement directly in C++ and CUDA, so I control every thread and every copy.`,
    `MNIST image → 28×28 → 784 features → network → digit; 784→256→ReLU→10→argmax; 10,000 images, float32, batches 1–4096, accuracy ${num("Sp:accuracy")} %.`);
  s.addImage({ path: path.join(__dirname, "assets", "mnist_sample.png"), x: 0.45, y: 1.15, w: 1.25, h: 1.25, altText: "MNIST test image 0, a handwritten seven" });
  T(s, "Test image 0 (label 7)", 0.35, 2.42, 1.5, 0.3, { fontSize: 10, color: MUTED, align: "center" });
  const flow = [["28×28 pixels", GRAY], ["784 input features", BLUE], ["Neural network", GREEN], ["Predicted digit: 7", PURPLE]];
  arrow(s, 1.7, 1.78, 2.0, 1.78, INK, 2);
  flow.forEach((f, i) => { const x = 2.0 + i * 1.9; box(s, x, 1.33, 1.6, 0.9, f[0], f[1], { fs: 13, bold: true }); if (i < 3) arrow(s, x + 1.6, 1.78, x + 1.9, 1.78, INK, 2); });
  T(s, "Architecture", 0.45, 2.85, 2, 0.3, { fontSize: 14, bold: true });
  const arch = [["784", GRAY], ["256", BLUE], ["ReLU", LGRAY], ["10", BLUE], ["argmax → digit", PURPLE]];
  arch.forEach((a, i) => { const x = 0.45 + i * 1.7; box(s, x, 3.2, 1.4, 0.5, a[0], a[1], { fs: a[0].length > 8 ? 11 : 13, bold: true, color: a[1] === LGRAY ? INK : "FFFFFF" }); if (i < 4) arrow(s, x + 1.4, 3.45, x + 1.7, 3.45, INK, 2); });
  bullets(s, ["10,000 MNIST test images per pass; 28×28 grayscale; 784 input features", "Float32; same trained weights for all implementations", `Verified model accuracy: ${num("Sp:accuracy")} %`], 0.45, 3.9, 4.6, 1.4, { fontSize: 13 });
  bullets(s, ["Batch sizes: 1, 8, 32, 64, 128, 256, 1024, 4096", "Inference only — training is not measured", "203,264 multiply-adds per image"], 5.2, 3.9, 4.4, 1.4, { fontSize: 13 });
}
// ---- 7 overall system architecture
{
  const s = addSlide("CONTENT", "Background and Method", "Overall System Architecture", 1.25,
    "Show that the mathematical workload is identical while the execution model changes.", "Workload pipeline row with four aligned execution lanes (serial, OpenMP, CUDA, hybrid).",
    `This slide has the whole system on one page. The top row is the workload, and it is the same for everybody: MNIST input, preprocessing, hidden layer, ReLU, output layer, argmax, predicted digit.\n\nUnderneath, each lane shows who executes those stages. Serial, in gray: every stage runs on one CPU thread. OpenMP, in blue: every stage runs on multiple CPU threads. CUDA: the preprocessing still runs on a single CPU thread - which is why I call it the CUDA pipeline with single-threaded preprocessing and not a GPU-only version - and the neural-network layers run on the GPU, with a host-to-device copy before and a device-to-host copy after. Hybrid: OpenMP threads do the preprocessing, CUDA does the computation, and different batches overlap in time.\n\nThe message of the slide is at the bottom: the mathematical workload stays the same, only the execution model changes.`,
    "Workload row; serial / OpenMP / CUDA / hybrid lanes aligned under the stages.");
  const st = ["MNIST input", "Preprocessing", "Hidden layer", "ReLU", "Output layer", "Argmax", "Predicted digit"];
  const X0 = 1.95, W = 1.0, G = 0.1;
  st.forEach((t, i) => { const x = X0 + i * (W + G); box(s, x, 1.15, W, 0.62, t, i === 0 || i === 6 ? LGRAY : NAVY, { fs: 11, bold: true, color: i === 0 || i === 6 ? INK : "FFFFFF" }); if (i < 6) arrow(s, x + W, 1.46, x + W + G, 1.46, INK, 1.2); });
  const xs = (i) => X0 + i * (W + G); const span = (a, b) => xs(b) + W - xs(a);
  const lane = (y, name, color) => T(s, name, 0.45, y, 1.45, 0.62, { fontSize: 13, bold: true, valign: "middle", color });
  lane(2.05, "Serial", GRAY); box(s, xs(1), 2.05, span(1, 5), 0.62, "All stages on ONE CPU thread", GRAY, { fs: 13, bold: true });
  lane(2.8, "OpenMP", BLUE); box(s, xs(1), 2.8, span(1, 5), 0.62, "All stages on MULTIPLE CPU threads", BLUE, { fs: 13, bold: true });
  lane(3.55, "CUDA", GREEN); box(s, xs(1), 3.55, W, 0.62, "CPU preprocessing (1 thread)", GRAY, { fs: 10, bold: true }); box(s, xs(2), 3.55, span(2, 5), 0.62, "GPU: neural-network layers + argmax", GREEN, { fs: 13, bold: true }); T(s, "+ copies\nin / out", xs(6) + 0.1, 3.55, 0.95, 0.62, { fontSize: 11, color: ORANGE, bold: true, valign: "middle" });
  lane(4.3, "Hybrid", PURPLE); box(s, xs(1), 4.3, W, 0.62, "OpenMP preprocessing", BLUE, { fs: 10, bold: true }); box(s, xs(2), 4.3, span(2, 5), 0.62, "CUDA computation, batches overlapped (3 streams)", GREEN, { fs: 12, bold: true });
  T(s, "Same mathematical workload; only the execution model changes.", 0.45, 5.0, 9.1, 0.3, { fontSize: 14, bold: true });
}
// ---- 8 serial
{
  const mn = Math.min(...SER.serial), mx = Math.max(...SER.serial);
  const s = addSlide("CONTENT", "Background and Method", "Serial CPU Implementation", 0,
    "Explain the baseline that all speedups and the correctness checks refer to.", "Short pseudocode box and a one-thread timeline of sequential images.",
    `The serial implementation is the simplest. For each image: preprocess, compute the hidden layer, apply ReLU, compute the output layer, and select the predicted digit. One CPU thread does everything, in order.

It matters for two reasons. It is the baseline - every speedup in this talk is relative to the serial time on the same machine and batch size - and it is the reference for correctness: every other implementation is compared with its outputs.

On the Spartan node a serial pass takes ${r(SER.serial[iB(4096)])} milliseconds at batch 4096, and between ${r(mn)} and ${r(mx)} milliseconds across all batch sizes - essentially independent of batch size - about ${comma(10000 / (SER.serial[iB(4096)] / 1000))} images per second.`,
    "Pseudocode: per image → preprocess, hidden, ReLU, output, select digit; one thread; baseline and correctness reference.");
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.45, y: 1.2, w: 4.2, h: 2.35, fill: { color: "111827" }, line: { color: "111827" }, rectRadius: 0.06 });
  T(s, "For each image:\n    preprocess\n    compute hidden layer\n    apply ReLU\n    compute output layer\n    select predicted digit", 0.65, 1.3, 3.9, 2.1, { fontFace: "Consolas", fontSize: 14, color: "E5E7EB" });
  T(s, "One CPU thread, images processed one after another", 4.95, 1.2, 4.6, 0.3, { fontSize: 13, bold: true });
  ["image 1", "image 2", "image 3", "…"].forEach((t, i) => { const y = 1.6 + i * 0.5; T(s, t, 4.95, y, 0.8, 0.4, { fontSize: 11, valign: "middle", color: MUTED });
    if (t !== "…") ["pre", "hidden", "ReLU", "output", "argmax"].forEach((q, j) => box(s, 5.8 + j * 0.74, y, 0.7, 0.4, q, GRAY, { fs: 10, bold: true })); });
  card(s, 4.95, 3.65, 4.6, 1.5, `${r(mn)}–${r(mx)} ms`, `serial time per pass of 10,000 images, all eight batch sizes (Spartan node)`, GRAY, { bigSize: 26, labelSize: 12, bigH: 0.6 });
  bullets(s, ["One CPU thread performs all work", "Baseline: every speedup is relative to this time", "Also the reference for correctness validation"], 0.45, 3.75, 4.3, 1.5, { fontSize: 13 });
}
// ---- 9 openmp
{
  const sc = SER.scale_spartan;
  const s = addSlide("CONTENT", "Background and Method", "OpenMP CPU Implementation", 0,
    "Explain fork-and-join execution, why synchronization is needed, and which thread counts were used.", "Fork-join diagram (main thread → threads → barrier → next stage) and thread-count chips.",
    `OpenMP uses a fork-and-join model. The main CPU thread forks a team of threads. Each thread processes a separate portion of the work - different images or groups of hidden units - and these calculations are independent. The threads share CPU memory, so nothing is copied. At the end of each parallel loop all threads meet at a barrier before the next stage starts, because the next stage needs the previous results.

Thread counts: on the Spartan node 1, 2, 4, 8, 12, 16 and 24, because my job was allocated 24 CPUs; on the Apple M4 laptop 1, 2, 4, 6, 8 and 10 - a separate platform, never part of the GPU comparison.

Typical limits are thread overhead, synchronization and memory bandwidth. In my data the synchronization cost is visible at tiny batches: one image per batch saturates at ${f1("Sp:omp:best:speedup:1")} times, while large batches reach ${f1("Sp:omp:speedup:4096:24")} times with 24 threads, an efficiency of ${f2("Sp:omp:eff:4096:24")}. I did not isolate memory bandwidth.`,
    "Fork-and-join; threads share memory; synchronization between stages; thread counts: Spartan 1,2,4,8,12,16,24; M4 1,2,4,6,8,10.");
  box(s, 0.45, 2.05, 1.4, 0.75, "Main CPU thread", BLUE, { fs: 12, bold: true });
  arrow(s, 1.85, 2.42, 2.3, 1.6, INK, 1.5); arrow(s, 1.85, 2.42, 2.3, 2.42, INK, 1.5); arrow(s, 1.85, 2.42, 2.3, 3.25, INK, 1.5);
  ["Thread 0", "Thread 1", "Thread 2"].forEach((t, i) => box(s, 2.3, 1.3 + i * 0.83, 2.2, 0.6, `${t}: independent calculations`, BLUE, { fs: 11, bold: true }));
  box(s, 4.75, 1.3, 0.35, 2.43, "", LGRAY);
  T(s, "barrier", 4.55, 3.78, 0.8, 0.3, { fontSize: 11, bold: true, color: MUTED, align: "center" });
  [0, 1, 2].forEach((i) => arrow(s, 4.5, 1.6 + i * 0.83, 4.75, 1.6 + i * 0.83, INK, 1.2));
  arrow(s, 5.1, 2.5, 5.55, 2.5, INK, 1.5);
  box(s, 5.55, 2.05, 1.5, 0.9, "Next neural-network stage", NAVY, { fs: 12, bold: true });
  T(s, "Fork → parallel work → synchronize → next stage", 0.45, 4.15, 6.6, 0.3, { fontSize: 12, color: MUTED });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 7.3, y: 1.2, w: 2.25, h: 3.0, fill: { color: LIGHT }, line: { color: LIGHT }, rectRadius: 0.08 });
  T(s, "Thread counts used", 7.4, 1.28, 2.1, 0.3, { fontSize: 13, bold: true });
  T(s, `Spartan node:\n${sc["1"].map((x) => x.threads).join(", ")}\n(24 CPUs allocated)\n\nApple M4 (separate platform):\n${SER.scale_mac["1"].map((x) => x.threads).join(", ")}`, 7.4, 1.62, 2.1, 2.5, { fontSize: 12 });
  bullets(s, ["Distributes independent work across CPU threads; threads share CPU memory", "Each thread processes a separate portion; synchronization is needed between dependent stages", `Limits: thread overhead, synchronization, memory bandwidth (small batches: speedup only ${f1("Sp:omp:best:speedup:1")}×; large batches: ${f1("Sp:omp:speedup:4096:24")}× with 24 threads)`], 0.45, 4.5, 9.1, 0.85, { fontSize: 12 });
}
// ---- 10 cuda
{
  const s = addSlide("CONTENT", "Background and Method", "CUDA GPU Implementation", 0,
    "Explain the host–device model and the grid → block → thread hierarchy, and that kernel time and end-to-end time are different measurements.", "Host/device data-path flow plus grid, block and thread diagram with block-size options.",
    `On the left is the data path. The CPU is the host, the GPU is the device, and they have separate memories. The batch starts in CPU memory, is copied over PCIe into GPU memory, the host launches a kernel, the kernel computes, and the predictions are copied back.

On the right is how the GPU organizes threads. A launch creates a grid; the grid is made of blocks; each block is made of threads. In my hidden-layer kernel a block is d by d threads, and thread tx, ty of block bx, by computes exactly one output: hidden unit j equals bx times d plus tx, for image b equals by times d plus ty. Threads compute independent outputs. I used 16 by 16 blocks - 256 threads - and also measured 8 by 8 and 32 by 32.

One distinction matters for the whole talk: kernel time and end-to-end time are different measurements. Kernel time is only the GPU computation; end-to-end includes preprocessing, both copies, launches and synchronization. I never treat kernel-only speed as the speed of the application.`,
    "Host memory → H2D → GPU memory → kernel launch → grid/blocks/threads → computation → D2H → predictions; kernel time ≠ end-to-end time.");
  const L = [["CPU host memory\n(input batch)", GRAY], ["GPU memory", GREEN], ["CUDA kernel launch\ngrid → blocks → threads", GREEN], ["GPU memory\n(results)", GREEN], ["CPU predictions", GRAY]];
  L.forEach((b, i) => { const y = 1.15 + i * 0.85; box(s, 0.45, y, 2.2, 0.5, b[0], b[1], { fs: 12, bold: true }); if (i < 4) arrow(s, 1.1, y + 0.5, 1.1, y + 0.85, INK, 1.5); });
  [["host-to-device transfer (PCIe)", 1.15 + 0.5 + 0.02], ["kernel launch", 1.15 + 0.85 + 0.5 + 0.02], ["neural-network computation", 1.15 + 1.7 + 0.5 + 0.02], ["device-to-host transfer (PCIe)", 1.15 + 2.55 + 0.5 + 0.02]].forEach((l, i) => T(s, l[0], 1.2, l[1], 2.0, 0.3, { fontSize: 10, color: i % 3 === 0 ? ORANGE : MUTED, bold: true, valign: "middle" }));
  T(s, "CUDA grid", 3.3, 1.15, 2, 0.3, { fontSize: 13, bold: true });
  for (let a = 0; a < 4; a++) for (let b = 0; b < 3; b++) box(s, 3.3 + a * 0.62, 1.5 + b * 0.5, 0.55, 0.43, a === 1 && b === 1 ? "block" : "", a === 1 && b === 1 ? PURPLE : GREEN, { fs: 10, bold: true });
  T(s, "blocks (bx, by)", 3.3, 3.0, 2.5, 0.28, { fontSize: 11, color: MUTED });
  arrow(s, 4.55, 2.5, 5.85, 2.2, PURPLE, 1.5);
  T(s, "One block = d × d threads", 5.95, 1.15, 3.6, 0.3, { fontSize: 13, bold: true });
  for (let a = 0; a < 6; a++) for (let b = 0; b < 6; b++) box(s, 5.95 + a * 0.3, 1.5 + b * 0.3, 0.26, 0.26, a === 3 && b === 2 ? "T" : "", a === 3 && b === 2 ? ORANGE : LGRAY, { fs: 10, bold: true });
  T(s, "thread (tx, ty)\ncomputes ONE output:\nunit j = bx·d + tx\nimage b = by·d + ty", 7.85, 1.5, 1.75, 1.3, { fontSize: 11 });
  bullets(s, ["CPU = host, GPU = device; separate memories", "Threads are grouped into blocks; blocks form a grid", "Threads compute independent output elements", "Block sizes measured: 8×8 (64), 16×16 (256, default), 32×32 (1,024 threads)", "Kernel time ≠ end-to-end time"], 3.3, 3.35, 6.3, 1.9, { fontSize: 13 });
}
// ---- 11 hybrid
{
  const s = addSlide("CONTENT", "Background and Method", "Hybrid OpenMP–CUDA Pipeline", 0,
    "Explain how OpenMP preprocessing, pinned memory, asynchronous copies and three CUDA streams make different batches overlap, and what hybrid-sequential is.", "Six-box hybrid flow plus a CPU lane and three CUDA stream lanes showing batch overlap (schematic).",
    `This is the central idea. In the plain CUDA pipeline the GPU idles while the CPU preprocesses, and the CPU waits while the GPU works. The hybrid removes that waiting.

The flow at the top: OpenMP threads preprocess into pinned host memory; pinned memory allows asynchronous transfers; the transfers go into CUDA streams; the GPU computes; the predictions come back.

The timeline is a schematic, not measured data. The CPU preprocesses batch 1, then 2, then 3. As soon as batch 1 is ready, its copy, kernels and copy back go into stream 0; while the GPU works on it, the CPU is already preprocessing batch 2, which stream 1 handles, and batch 3 goes to stream 2. So OpenMP preprocesses future batches while CUDA processes earlier ones.

The purple box matters: inside one batch the hidden layer, output layer and argmax depend on each other, so they stay in order; only different batches overlap.

Hybrid-sequential - OpenMP preprocessing with no overlap - is only a diagnostic control. It separates the benefit of parallel preprocessing from the benefit of overlap.`,
    "OpenMP preprocessing → pinned memory → async transfer → CUDA streams → GPU computation → predictions; timeline; layers ordered within a batch; hybrid-sequential = control.");
  const fl = [["OpenMP CPU\npreprocessing", BLUE], ["Pinned host\nmemory", GRAY], ["Asynchronous\ndata transfer", ORANGE], ["CUDA streams\n(3)", GREEN], ["GPU neural-network\ncomputation", GREEN], ["Predictions", NAVY]];
  fl.forEach((f, i) => { const x = 0.45 + i * 1.55; box(s, x, 1.15, 1.35, 0.62, f[0], f[1], { fs: 11, bold: true }); if (i < 5) arrow(s, x + 1.35, 1.46, x + 1.55, 1.46, INK, 1.5); });
  const X0 = 2.2;
  const seg = (x, y, w, c, t) => box(s, x, y, w, 0.3, t, c, { fs: 9, bold: true, line: "FFFFFF" });
  T(s, "CPU (OpenMP)", 0.45, 2.0, 1.7, 0.3, { fontSize: 11, bold: true, color: BLUE, valign: "middle" });
  for (let i = 0; i < 6; i++) seg(X0 + i * 1.1, 2.0, 0.8, BLUE, `pre b${i + 1}`);
  [0, 1, 2].forEach((st) => T(s, `CUDA stream ${st}`, 0.45, 2.4 + st * 0.4, 1.7, 0.3, { fontSize: 11, bold: true, color: GREEN, valign: "middle" }));
  for (let i = 0; i < 6; i++) { const st = i % 3, x = X0 + 0.8 + i * 1.1, y = 2.4 + st * 0.4; seg(x, y, 0.28, ORANGE, "H2D"); seg(x + 0.28, y, 0.62, GREEN, `kern b${i + 1}`); seg(x + 0.9, y, 0.28, ORANGE, "D2H"); }
  T(s, "Schematic (not measured): the CPU preprocesses future batches while the GPU processes earlier ones.", 0.45, 3.65, 9.1, 0.3, { fontSize: 11, italic: true, color: MUTED });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.45, y: 3.98, w: 9.1, h: 0.5, fill: { color: PURPLE }, line: { color: PURPLE }, rectRadius: 0.06 });
  T(s, "Layers within one batch stay dependency-ordered; the overlap is between different batches.", 0.65, 3.98, 8.7, 0.5, { fontSize: 14, bold: true, color: "FFFFFF", valign: "middle" });
  bullets(s, ["OpenMP preprocesses future batches while CUDA processes earlier ones; pinned memory enables asynchronous copies; three streams overlap different batches", "Hybrid-sequential (OpenMP preprocessing, no overlap) is only a diagnostic control: it separates the benefit of parallel preprocessing from the benefit of overlap"], 0.45, 4.58, 9.1, 0.75, { fontSize: 12 });
}
// ---- 12 setup
{
  const s = addSlide("CONTENT", "Background and Method", "Experimental Setup and Measurement Protocol", 0,
    "Document exactly what was measured and why each important decision was made.", "Three-column table: item, configuration, reason.",
    `Here is exactly how I measured, and why. The workload is the ten thousand MNIST test images in float32 through the 784-256-10 network, in batches from 1 to 4,096 - covering both latency-bound and throughput-bound behavior.

The main platform is a Spartan GPU node: two Xeon E5-2680 v4 CPUs - lscpu reports 28 physical cores and 28 logical CPUs, and my jobs were allocated 24, so OpenMP uses at most 24 threads - and a Tesla K40m with CUDA 11.7. Compilers are g++ 11.4.1 with O3 and march native, and nvcc 11.7. The Apple M4, with clang 21, is only a separate CPU study.

Protocol: three unrecorded warm-up passes to remove start-up effects, then twenty recorded passes, all kept and reported with mean, median, standard deviation, minimum, maximum and 95 percent confidence intervals. GPU stages use CUDA events; end-to-end time is wall clock. GPU initialization, allocation and weight upload are one-time costs, excluded from steady state and measured separately: ${f1("Sp:cold:ctor:mean")} milliseconds. The CUDA block is fixed at 16 by 16, and CPU-versus-GPU comparisons use one node only.`,
    "Setup table with reasons.");
  const rows = [["Item", "Configuration", "Why"],
    ["Workload", "10,000 MNIST test images; 784→256→ReLU→10; float32", "Standard, reproducible, small enough to implement directly"],
    ["Batch sizes", "1, 8, 32, 64, 128, 256, 1024, 4096", "Covers latency- to throughput-bound behavior"],
    ["CPU hardware", "2× Xeon E5-2680 v4: 28 cores / 28 logical CPUs (lscpu); 24 allocated", "Host of the GPU node"],
    ["GPU hardware", "Tesla K40m, CUDA 11.7", "GPU available on Spartan"],
    ["Compilers", "g++ 11.4.1 -O3 -march=native; nvcc 11.7.99 -O3 -arch=sm_35 (M4: Apple clang 21.0.0 -O3)", "Strong CPU baseline"],
    ["OpenMP threads; CUDA block", "Spartan 1, 2, 4, 8, 12, 16, 24; M4 1, 2, 4, 6, 8, 10; CUDA block 16×16 (8×8, 32×32 also measured)", "Up to allocated cores; fixed block"],
    ["Warm-up; recorded", "3 unrecorded passes; 20 recorded passes (all kept)", "Remove start-up effects; confidence intervals"],
    ["Timing", "CUDA events for GPU stages; wall clock for end-to-end", "Stage time vs application time"],
    ["Excluded; platforms", `GPU initialization, allocation, weight upload (${f1("Sp:cold:ctor:mean")} ms, measured separately); CPU-vs-GPU on one Spartan node; Mac results separate`, "Steady state; same-machine fairness"]];
  table(s, rows, 0.4, 1.1, 9.2, [1.5, 4.9, 2.8], 10.5, { rowH: 0.4 });
}
pres.addSection({ title: "Results" });
// ---- 13 correctness
{
  const V = SER.validation; const g = (n) => V.find((v) => v.group.indexOf(n) === 0);
  const sup = (e) => String(e).replace(/-/g, "⁻").replace(/\d/g, (d) => "⁰¹²³⁴⁵⁶⁷⁸⁹"[d]);
  const sci = (x) => { if (x === 0) return "0 (bit-identical)"; const [m, e] = x.toExponential(1).split("e"); return `${m}×10${sup(parseInt(e))}`; };
  const row = (label, n) => { const v = g(n); return [label, `${v.passed} / ${v.n}`, sci(v.maxerr), `${v.agree.toFixed(2)} %`, `${v.acc.toFixed(2)} %`]; };
  const s = addSlide("CONTENT", "Results", "Correctness Validation Before Performance Comparison", 0,
    "Show that all implementations produce equivalent outputs before any timing is interpreted.", "Accuracy-vs-correctness definition boxes and a comparison table.",
    `Before interpreting any timing I checked correctness - and I separate two ideas. Accuracy: how well the model classifies MNIST, ${num("Sp:accuracy")} percent. Correctness: whether all implementations produce equivalent outputs.

The table compares each implementation with the serial reference on all ten thousand images, over several batch sizes, thread counts, block sizes and stream counts - eighty comparisons, all passing. OpenMP is bit-identical. CUDA and both hybrid variants differ by at most ${num("Sp:val:cuda:maxerr")} in the logits and predict exactly the same digit for every image.

Small floating-point differences are possible - same operations and source-level order, but compilers may apply optimizations such as fused multiply-add - so I fixed a tolerance beforehand: maximum logit difference 1e-4, agreement at least 99.9 percent. A faster implementation is invalid if its output is incorrect.`,
    "Accuracy vs correctness; table: passed, max logit difference, agreement, accuracy.");
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.45, y: 1.15, w: 4.45, h: 0.8, fill: { color: LIGHT }, line: { color: LIGHT }, rectRadius: 0.06 });
  T(s, "Accuracy: how well does the model classify MNIST?", 0.6, 1.15, 4.2, 0.8, { fontSize: 13, valign: "middle", bold: true });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 5.1, y: 1.15, w: 4.45, h: 0.8, fill: { color: LIGHT }, line: { color: LIGHT }, rectRadius: 0.06 });
  T(s, "Correctness: do all implementations produce equivalent outputs?", 5.25, 1.15, 4.2, 0.8, { fontSize: 13, valign: "middle", bold: true });
  table(s, [["Comparison with serial", "Passed", "Max logit difference", "Prediction agreement", "Accuracy"], row("Serial vs OpenMP", "Serial vs OpenMP"), row("Serial vs CUDA", "Serial vs CUDA"), row("Serial vs hybrid-sequential (control)", "Serial vs Hybrid-sequential"), row("Serial vs hybrid-pipelined", "Serial vs Hybrid-pipelined")],
    0.45, 2.1, 9.1, [3.4, 1.0, 2.0, 1.6, 1.1], 13, { rowH: 0.42 });
  bullets(s, ["Small floating-point differences are possible (compiler optimizations such as fused multiply-add)", "Predefined tolerance: max logit difference ≤ 1×10⁻⁴, agreement ≥ 99.9 %", "Correctness is checked before performance is interpreted; incorrect output makes a fast result invalid"], 0.45, 4.35, 9.1, 1.0, { fontSize: 12 });
}
// ---- 14 end-to-end execution time
{
  const i1 = iB(1), i8 = iB(8), i32 = iB(32), i128 = iB(128), i256 = iB(256), i4096 = iB(4096);
  const s = addSlide("CONTENT", "Results", "End-to-End Execution Time Across All Implementations", 0,
    "Compare all four implementations on one graph and locate the performance crossovers.", "One native line chart (log time axis) with serial, OpenMP, CUDA pipeline and hybrid pipeline versus batch size, with 95% error bars.",
    `This is the main result: all four implementations on one graph - serial, OpenMP with its best thread count, the CUDA pipeline and the hybrid. The y-axis is the time of one pass over ten thousand images in milliseconds, log scale, with tiny 95 percent confidence intervals. Everything is the Spartan node.

Fastest for small batches: OpenMP. At batch 1 it needs ${r(SER.omp[i1])} milliseconds, the hybrid ${r(SER.hyb[i1])}, and the CUDA pipeline ${r(SER.cuda[i1])} - slower than serial at ${r(SER.serial[i1])}. At batch 8 OpenMP still leads, ${r(SER.omp[i8])} against ${r(SER.hyb[i8])}.

Fastest for large batches: the hybrid - ${r(SER.hyb[i4096])} milliseconds at batch 4096, against ${r(SER.cuda[i4096])} for the CUDA pipeline and ${r(SER.omp[i4096])} for OpenMP.

The crossover: the hybrid overtakes OpenMP at batch ${num("Sp:hyb:crossover")}; the plain CUDA pipeline catches OpenMP only around batch 128 to 256.

Why is CUDA slower for small batches? Each batch pays for launches, two copies and a synchronization, and one image leaves most GPU threads idle. Why does the hybrid win for larger batches? The GPU gets enough work, the preprocessing is parallel, and it overlaps with GPU work on another batch.`,
    `Fastest at batch 1/8: OpenMP; from batch ${num("Sp:hyb:crossover")}: hybrid; CUDA pipeline reaches OpenMP around batch 128–256.`);
  chart(s, "line", [{ name: "Serial CPU", values: R4(SER.serial), ci: SER.serial_ci, color: GRAY }, { name: "OpenMP CPU (best thread count)", values: R4(SER.omp), ci: SER.omp_ci, color: BLUE }, { name: CUDA, values: R4(SER.cuda), ci: SER.cuda_ci, color: GREEN }, { name: "Hybrid pipeline (best thread count)", values: R4(SER.hyb), ci: SER.hyb_ci, color: PURPLE }],
    lab, { x: 0.3, y: 1.1, w: 9.4, h: 3.35, title: "End-to-end execution time per pass of 10,000 images (Spartan node, Tesla K40m)", valAxisTitle: "Execution time per pass (ms, log scale)", catAxisTitle: "Batch size (images per batch)", valAxisLogScaleBase: 10, valAxisMinVal: 10, valAxisMaxVal: 10000, legendFontSize: 11 });
  bullets(s, [`Small batches (1, 8): OpenMP fastest — GPU launch, copy and synchronization overhead dominates (CUDA pipeline at batch 1: ${r(SER.cuda[i1])} ms, slower than serial ${r(SER.serial[i1])} ms)`, `Large batches (≥ ${num("Sp:hyb:crossover")}): hybrid fastest — ${r(SER.hyb[i4096])} ms at batch 4096 vs ${r(SER.cuda[i4096])} ms (CUDA pipeline) and ${r(SER.omp[i4096])} ms (OpenMP)`], 0.45, 4.5, 9.1, 0.8, { fontSize: 12 });
}
// ---- 15 speedup and throughput
{
  const so = speedup(SER.omp, SER.omp_ci), sc = speedup(SER.cuda, SER.cuda_ci), sh = speedup(SER.hyb, SER.hyb_ci);
  const to = thruput(SER.omp, SER.omp_ci), tc = thruput(SER.cuda, SER.cuda_ci), th = thruput(SER.hyb, SER.hyb_ci), ts = thruput(SER.serial, SER.serial_ci);
  const i4096 = iB(4096), i1 = iB(1);
  const s = addSlide("CONTENT", "Results", "Speedup and Throughput Across All Implementations", 1.75,
    "Show relative performance (speedup) and absolute performance (throughput) of all four implementations side by side.", "Two native charts: speedup over serial (×) and throughput (images per second, log axis), each with all four implementations.",
    `Same four implementations, two different views. On the left is speedup, defined as the serial time divided by the implementation time, so serial is the line at one. On the right is throughput, ten thousand images divided by the pass time in seconds - how many images per second each implementation processes.\n\nRead the left chart first. At batch 4096 OpenMP is ${r(so.v[i4096])} times faster than serial, the CUDA pipeline ${r(sc.v[i4096])} times, and the hybrid ${r(sh.v[i4096])} times. At batch 1 the picture is different: OpenMP gives ${r(so.v[i1])} times, the hybrid ${r(sh.v[i1])} times, and the CUDA pipeline ${r(sc.v[i1])} - below one, which means slower than serial.\n\nThe right chart says the same thing in images per second. Serial processes about ${comma(ts.v[i4096])} images per second. At batch 4096 OpenMP reaches ${comma(to.v[i4096])}, the CUDA pipeline ${comma(tc.v[i4096])}, and the hybrid ${comma(th.v[i4096])} images per second. Notice that serial and OpenMP throughput barely change with batch size, while the GPU-based implementations improve a lot, because larger batches amortize the fixed launch and copy costs.\n\nSo: the hybrid delivers the highest throughput from batch 32 on, OpenMP is best for the smallest batches, and the CUDA pipeline with single-threaded preprocessing is never the best.`,
    `Speedup = serial time / implementation time; throughput = 10,000 / time (s). Batch 4096: speedup OpenMP ${r(so.v[i4096])}×, CUDA ${r(sc.v[i4096])}×, hybrid ${r(sh.v[i4096])}×.`);
  chart(s, "line", [{ name: "Serial CPU", values: R4(SER.serial.map(() => 1)), color: GRAY }, { name: "OpenMP CPU", values: R4(so.v), ci: so.ci, color: BLUE }, { name: "CUDA pipeline", values: R4(sc.v), ci: sc.ci, color: GREEN }, { name: "Hybrid pipeline", values: R4(sh.v), ci: sh.ci, color: PURPLE }],
    lab, { x: 0.3, y: 1.1, w: 4.65, h: 3.35, title: "Speedup over serial (Spartan)", valAxisTitle: "Speedup over serial (×)", catAxisTitle: "Batch size (images per batch)", valAxisMinVal: 0, valAxisMaxVal: 60, legendFontSize: 10, catAxisLabelFontSize: 10 });
  chart(s, "line", [{ name: "Serial CPU", values: R4(ts.v), ci: ts.ci, color: GRAY }, { name: "OpenMP CPU", values: R4(to.v), ci: to.ci, color: BLUE }, { name: "CUDA pipeline", values: R4(tc.v), ci: tc.ci, color: GREEN }, { name: "Hybrid pipeline", values: R4(th.v), ci: th.ci, color: PURPLE }],
    lab, { x: 5.05, y: 1.1, w: 4.65, h: 3.35, title: "Throughput (Spartan)", valAxisTitle: "Throughput (images per second, log scale)", catAxisTitle: "Batch size (images per batch)", valAxisLogScaleBase: 10, valAxisMinVal: 1000, valAxisMaxVal: 1000000, legendFontSize: 10, catAxisLabelFontSize: 10, valAxisLabelFormatCode: "#,##0" });
  T(s, "Speedup = Serial time / Implementation time        Throughput = 10,000 images / Execution time in seconds", 0.45, 4.5, 9.1, 0.3, { fontSize: 13, bold: true, color: NAVY });
  T(s, `Batch 4096: speedup ${r(so.v[i4096])}× (OpenMP), ${r(sc.v[i4096])}× (CUDA pipeline), ${r(sh.v[i4096])}× (hybrid); throughput up to ${comma(th.v[i4096])} images/s (hybrid) vs ${comma(ts.v[i4096])} images/s (serial).`, 0.45, 4.85, 9.1, 0.45, { fontSize: 12 });
}
// ---- 16 overhead and hybrid performance
{
  const i4096 = iB(4096), i1 = iB(1), i32 = iB(32);
  const pct = (key) => B.map((_, i) => +(SER[key][i] / SER.cuda[i] * 100).toFixed(2));
  const s = addSlide("CONTENT", "Results", "CUDA Overhead and Hybrid Performance", 0,
    "Explain why CUDA kernels are fast but the CUDA pipeline is slower, and quantify what OpenMP preprocessing and CPU–GPU overlap each contribute.", "Left: line chart of kernel-only, CUDA end-to-end, hybrid-sequential and hybrid-pipelined; right: stacked percentage chart of CUDA pipeline stages.",
    `This slide explains the gap between a fast kernel and a slower pipeline, and what the hybrid recovers. On the left are four things: CUDA kernels only, which exclude preprocessing and copies; CUDA end-to-end, the full pipeline; hybrid-sequential, the control with OpenMP preprocessing but no overlap; and the pipelined hybrid.

At batch 4096 the kernels take ${r(SER.kernel[i4096])} milliseconds, but the complete CUDA pipeline takes ${r(SER.cuda[i4096])}. The stacked bar shows why: kernels are ${f1("Sp:cuda:kshare:4096")} percent, single-threaded CPU preprocessing ${f1("Sp:cuda:preshare:4096")} percent - ${f1("Sp:cuda:pre:4096")} milliseconds at every batch size - and copies only ${f1("Sp:cuda:tshare:4096")} percent. At batch 1 copies are ${f1("Sp:cuda:tshare:1")} percent and launch and synchronization ${f1("Sp:cuda:othershare:1")} percent; that gray part is a residual, not directly timed.

OpenMP preprocessing alone takes the pass from ${r(SER.cuda[i4096])} to ${r(SER.hseq[i4096])} milliseconds, ${f2("Sp:hseq:vscuda:4096")} times faster. The asynchronous overlap brings it to ${r(SER.hyb[i4096])} - another ${f2("Sp:hyb:vshseq:4096")} times, and only ${f2("Sp:hyb:vskernel:4096")} times the kernel-only time.

It depends on batch size: at batch 1 the hybrid needs ${r(SER.hyb[i1])} milliseconds against ${r(SER.omp[i1])} for OpenMP, so it is not best there; it overtakes OpenMP from batch ${num("Sp:hyb:crossover")}.`,
    `Batch 4096: kernels ${r(SER.kernel[i4096])} ms, CUDA end-to-end ${r(SER.cuda[i4096])} ms, hybrid-sequential ${r(SER.hseq[i4096])} ms, hybrid-pipelined ${r(SER.hyb[i4096])} ms; shares: kernels ${f1("Sp:cuda:kshare:4096")} %, preprocessing ${f1("Sp:cuda:preshare:4096")} %, copies ${f1("Sp:cuda:tshare:4096")} %.`);
  chart(s, "line", [{ name: "CUDA kernels only (compute-only)", values: R4(SER.kernel), ci: SER.kernel_ci, color: TEAL }, { name: "CUDA end-to-end", values: R4(SER.cuda), ci: SER.cuda_ci, color: GREEN }, { name: "Hybrid-sequential (control)", values: R4(SER.hseq), ci: SER.hseq_ci, color: LPURPLE, dash: "dash" }, { name: "Hybrid-pipelined", values: R4(SER.hyb), ci: SER.hyb_ci, color: PURPLE }],
    lab, { x: 0.3, y: 1.1, w: 4.75, h: 3.45, title: "Time per pass (Spartan)", valAxisTitle: "Time per pass (ms, log scale)", catAxisTitle: "Batch size (images per batch)", valAxisLogScaleBase: 10, valAxisMinVal: 10, valAxisMaxVal: 10000, legendFontSize: 10, catAxisLabelFontSize: 10, valAxisLabelFontSize: 10 });
  const sers = [{ name: "CPU preprocessing (1 thread)", key: "pre", color: BLUE }, { name: "Host-to-device transfer", key: "h2d", color: ORANGE }, { name: "CUDA kernels", key: "kernel", color: GREEN }, { name: "Device-to-host transfer", key: "d2h", color: LORANGE }, { name: "Launch / sync overhead (residual)", key: "other", color: LGRAY }];
  chart(s, "bar", sers.map((q) => ({ name: q.name, values: pct(q.key), color: q.color })), lab, { x: 5.1, y: 1.1, w: 4.6, h: 3.45, barDir: "col", barGrouping: "stacked", barGapWidthPct: 40, title: "CUDA pipeline time breakdown", valAxisTitle: "Share of end-to-end time (%)", catAxisTitle: "Batch size (images per batch)", valAxisMaxVal: 100, valAxisMinVal: 0, legendFontSize: 9, catAxisLabelFontSize: 10, valAxisLabelFontSize: 10 });
  bullets(s, [`Batch 4096: kernels ${r(SER.kernel[i4096])} ms vs complete CUDA pipeline ${r(SER.cuda[i4096])} ms — preprocessing is ${f1("Sp:cuda:preshare:4096")} % of the pipeline, copies ${f1("Sp:cuda:tshare:4096")} %`, `OpenMP preprocessing alone (control): ${f2("Sp:hseq:vscuda:4096")}× faster than the CUDA pipeline; asynchronous overlap adds ${f2("Sp:hyb:vshseq:4096")}× more; hybrid beats OpenMP only from batch ${num("Sp:hyb:crossover")}`], 0.45, 4.62, 9.1, 0.75, { fontSize: 12 });
}
// ---- 17 Amdahl
{
  const thr = SER.scale_spartan["1"].map((x) => x.threads); const labT = thr.map(String);
  const fit = (f) => thr.map((p) => +(1 / (f + (1 - f) / p)).toFixed(3));
  const meas = (b) => SER.scale_spartan[b].map((x) => +x.speedup.toFixed(3));
  const f1v = SER.amdahl["1"].f, f4v = SER.amdahl["4096"].f;
  const s = addSlide("CONTENT", "Results", "Amdahl’s Law and Performance Bottlenecks", 0,
    "Connect Amdahl's law to the measured results and explain which serial costs limit the speedup.", "Formula, native chart of measured speedup vs fitted Amdahl curves (batch 1 and 4096), and four connecting statements.",
    `Amdahl's law: S of N equals one over one minus P plus P over N. P is the parallel portion and one minus P the serial portion; however many threads you add, speedup cannot exceed one over the serial fraction. Serial preprocessing, transfers, synchronization and kernel launches sit in that serial part.

I fitted it to my OpenMP data. For batch 4096 on the Xeon the serial fraction is only ${num("Sp:amdahl:f:4096")}, a ceiling of ${f1("Sp:amdahl:ceil:4096")} times, so the ${f1("Sp:omp:speedup:4096:24")} times measured at 24 threads is not limited by it. For one image per batch it is ${num("Sp:amdahl:f:1")}, a ceiling of ${f1("Sp:amdahl:ceil:1")} times, and the measured curve flattens at ${f1("Sp:omp:best:speedup:1")} times: small batches carry more overhead relative to useful work. On the Apple M4, a separate platform, speedup flattens beyond its four performance cores, at ${f1("Mac:omp:speedup:4096:10")} times with ten threads.

The same logic explains the GPU: kernels are ${f1("Sp:comp:gpuvsserial:4096")} times faster than serial, but transfers and single-threaded preprocessing act like a serial part, so the pipeline reaches ${f1("Sp:cuda:speedup:4096")} times. The hybrid overlaps independent stages of different batches and reaches ${f1("Sp:hyb:best:speedup:4096")} times.`,
    `S(N) = 1/((1−P)+P/N); Xeon f = ${num("Sp:amdahl:f:4096")} (batch 4096), ${num("Sp:amdahl:f:1")} (batch 1).`);
  T(s, "S(N) = 1 / ( (1 − P) + P / N )", 0.45, 1.12, 5.4, 0.45, { fontSize: 20, bold: true, fontFace: "Consolas", color: NAVY });
  chart(s, "line", [{ name: "Measured, batch 4096", values: meas("4096"), ci: SER.scale_spartan["4096"].map((x) => x.speedup_ci), color: "1E3A8A" }, { name: `Amdahl fit, f = ${f4v.toFixed(3)}`, values: fit(f4v), color: "1E3A8A", dash: "dash" }, { name: "Measured, batch 1", values: meas("1"), ci: SER.scale_spartan["1"].map((x) => x.speedup_ci), color: ORANGE }, { name: `Amdahl fit, f = ${f1v.toFixed(3)}`, values: fit(f1v), color: ORANGE, dash: "dash" }, { name: "Ideal (f = 0)", values: thr, color: LGRAY, dash: "sysDash" }],
    labT, { x: 0.3, y: 1.55, w: 5.2, h: 3.75, title: "OpenMP speedup vs threads, Xeon (Spartan)", valAxisTitle: "Speedup over serial (×)", catAxisTitle: "OpenMP threads", legendFontSize: 10, valAxisMinVal: 0 });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 5.65, y: 1.12, w: 3.9, h: 4.15, fill: { color: LIGHT }, line: { color: LIGHT }, rectRadius: 0.08 });
  T(s, "P = parallel portion; 1 − P = serial portion", 5.8, 1.18, 3.6, 0.3, { fontSize: 12, bold: true });
  bullets(s, ["Serial preprocessing, transfers, synchronization and kernel launches limit total speedup", `OpenMP: near-linear for batches ≥ 32 on the Xeon (f = ${num("Sp:amdahl:f:4096")}); flattens at batch 1 (${f1("Sp:omp:best:speedup:1")}×, f = ${num("Sp:amdahl:f:1")}) and on the M4 beyond 4 cores`, "Small batches: more overhead relative to useful work", `CUDA kernels ${f1("Sp:comp:gpuvsserial:4096")}× → pipeline ${f1("Sp:cuda:speedup:4096")}× (transfers + preprocessing)`, `Hybrid overlaps independent stages → ${f1("Sp:hyb:best:speedup:4096")}×`], 5.8, 1.55, 3.65, 3.7, { fontSize: 13 });
}
pres.addSection({ title: "Conclusions" });
pres.addSection({ title: "Conclusions" });
// ---- 18 conclusions
{
  const s = addSlide("DARK", "Conclusions", "Conclusions, Limitations, and Future Work", 0,
    "Summarise the verified conclusions, state the limitations honestly, list future work and end with the main message.", "Three-column text (conclusions, limitations, future work) and a closing statement.",
    `The conclusions, all backed by measurements. One: OpenMP improves CPU execution - ${f1("Sp:omp:speedup:4096:24")} times with 24 threads on the Xeon at large batches - but reaches scaling limits at tiny batches and on the M4's efficiency cores. Two: CUDA kernels give strong computational speedup, ${f1("Sp:comp:gpuvsserial:4096")} times over serial compute-only at batch 4096. Three: CUDA end-to-end performance is limited by preprocessing and transfers - the complete pipeline reaches ${f1("Sp:cuda:speedup:4096")} times. Four: hybrid execution can cut end-to-end time - ${f1("Sp:hyb:best:e2e:4096")} milliseconds against ${f1("Sp:cuda:e2e:4096")} for the CUDA pipeline at batch 4096. Five: the best implementation depends on batch size - OpenMP for batches of 1 and 8, the hybrid from batch ${num("Sp:hyb:crossover")}.

Limitations: an older Tesla K40m, a small fully connected network, straightforward rather than fully tuned kernels, a shared environment, results that may differ on modern GPUs, and different CPU architectures on the Mac and Spartan. CUDA also used a fixed block size while OpenMP and the hybrid used their best thread count.

Future work: shared-memory tiling, GPU-side preprocessing, cuBLAS, a newer GPU, larger and convolutional networks, and energy measurements.

The main message: there is no universally fastest implementation. The best choice depends on workload size, parallel work, preprocessing cost, memory-transfer overhead, and the ability to overlap CPU and GPU stages. Thank you - I am happy to take questions.`,
    "Five conclusions; six limitations; seven future-work items; closing statement.");
  T(s, "Conclusions", 0.45, 1.1, 3.1, 0.3, { fontSize: 16, bold: true, color: "86EFAC", fontFace: "Cambria" });
  bullets(s, [`OpenMP improves CPU execution (${f1("Sp:omp:speedup:4096:24")}× at 24 threads) but reaches scaling limits`, `CUDA kernels give strong computational speedup (${f1("Sp:comp:gpuvsserial:4096")}× vs serial)`, `CUDA end-to-end is limited by preprocessing and transfers (${f1("Sp:cuda:speedup:4096")}×)`, `Hybrid can cut end-to-end time (${f1("Sp:hyb:best:e2e:4096")} ms vs ${f1("Sp:cuda:e2e:4096")} ms)`, "The best implementation depends on batch size and workload"], 0.45, 1.42, 3.1, 2.95, { fontSize: 13, color: "E5E7EB" });
  T(s, "Limitations", 3.7, 1.1, 2.9, 0.3, { fontSize: 16, bold: true, color: "FCA5A5", fontFace: "Cambria" });
  bullets(s, ["Older Tesla K40m GPU", "Small fully connected network", "Straightforward, not fully tuned kernels", "Shared computing environment", "Results may differ on modern GPUs", "Mac and Spartan use different CPU architectures"], 3.7, 1.42, 2.9, 2.95, { fontSize: 13, color: "E5E7EB" });
  T(s, "Future work", 6.75, 1.1, 2.8, 0.3, { fontSize: 16, bold: true, color: "93C5FD", fontFace: "Cambria" });
  bullets(s, ["CUDA shared-memory tiling", "GPU-side preprocessing", "cuBLAS comparison", "Newer GPU comparison", "Larger networks", "Convolutional neural networks", "Energy measurements"], 6.75, 1.42, 2.8, 2.95, { fontSize: 13, color: "E5E7EB" });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.45, y: 4.4, w: 9.1, h: 0.9, fill: { color: PURPLE }, line: { color: PURPLE }, rectRadius: 0.06 });
  T(s, "“There is no universally fastest implementation. The best choice depends on workload size, parallel work, preprocessing cost, memory-transfer overhead, and the ability to overlap CPU and GPU stages.”", 0.65, 4.4, 8.7, 0.9, { fontSize: 14, bold: true, color: "FFFFFF", valign: "middle", italic: true });
}

// ---------- write files ----------
(async () => {
  if (LOG.length !== 18) throw new Error(`expected exactly 18 slides, built ${LOG.length}`);
  const out = path.join(__dirname, "CS259_Hybrid_CPU_GPU_Induru.pptx");
  await pres.writeFile({ fileName: out });
  await applyTheme(out, THEME);
  fs.writeFileSync(path.join(__dirname, "errbars.json"), JSON.stringify(ERR));
  const mins = LOG.reduce((a, l) => a + l.minutes, 0);
  const words = LOG.reduce((a, l) => a + l.notes.split(/\s+/).length, 0);
  const md = LOG.map((l) => `## Slide ${l.n}: ${l.title}\n\n**Estimated speaking time:** ${l.minutes} min\n\n**Main purpose:** ${l.purpose}\n\n**Recommended visual:** ${l.visual}\n\n**Text on the slide:** ${l.text}\n\n**What to say:**\n\n${l.notes}\n`).join("\n");
  fs.writeFileSync(path.join(__dirname, "speaker_notes.md"), `# Speaker notes — exactly 18 slides, about ${mins} minutes\n\n${md}`);
  fs.writeFileSync(path.join(__dirname, "slide_content.md"), "# Slide content (18 slides)\n\n" + LOG.map((l) => `${l.n}. **${l.title}** (${l.minutes} min) — ${l.purpose}\n   - Visual: ${l.visual}\n   - Text: ${l.text}`).join("\n") + "\n");
  console.log(`wrote ${out}: ${LOG.length} slides; speaking time ${mins} min; notes ${words} words (~${(words / 140).toFixed(1)} min at 140 wpm)`);
})();
