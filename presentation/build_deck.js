// build_deck.js - CS 259 presentation: exactly 18 main slides + separate backup slides.
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

// ---------- theme ----------
const THEME = { name: "CS259 Hybrid", headFontFace: "Cambria", bodyFontFace: "Calibri",
  colors: { dk1: "1F2937", lt1: "FFFFFF", dk2: "0F172A", lt2: "F3F4F6", accent1: "2563EB", accent2: "16A34A", accent3: "7C3AED", accent4: "C2570C", accent5: "4B5563", accent6: "F0A36B", hlink: "2563EB", folHlink: "7C3AED" } };
const NAVY = "0F172A", INK = "1F2937", MUTED = "4B5563", LIGHT = "F3F4F6", BLUE = "2563EB", GREEN = "16A34A", PURPLE = "7C3AED", LPURPLE = "A78BFA", ORANGE = "C2570C", LORANGE = "F0A36B", GRAY = "4B5563", LGRAY = "9CA3AF";

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
function addSlide(master, section, title, minutes, notes, text) {
  slideNo++;
  const s = pres.addSlide({ masterName: master, sectionTitle: section });
  s.addText(title, { placeholder: "title" });
  s.addNotes(`[Estimated speaking time: ${minutes} min]\n\n${notes}`);
  LOG.push({ n: slideNo, section, title, minutes, notes, text: text || "" });
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
// native chart + sidecar error-bar record (added to the XML by add_error_bars.py)
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
const CUDA = "CUDA (1-thread preprocessing)";

// =============================================== MAIN SLIDES (18) ===============================================
pres.addSection({ title: "Introduction" });
// ---- 1
{
  slideNo++;
  const s = pres.addSlide({ masterName: "TITLE", sectionTitle: "Introduction" });
  s.addText("Performance Evaluation of Hybrid CPU–GPU Parallelism for Deep Learning Using OpenMP and CUDA", { placeholder: "title" });
  s.addText(`Sunnihith Reddy Induru\nCS 259 — Advanced Parallel Processing\nSan José State University\n${DATE}`, { placeholder: "body" });
  const notes = `Good morning, everyone. My project is called "Performance Evaluation of Hybrid CPU-GPU Parallelism for Deep Learning Using OpenMP and CUDA."\n\nIn one sentence: I took one small neural-network inference workload and ran it four ways - serial on one CPU thread, in parallel on many CPU threads with OpenMP, on the GPU with CUDA, and as a hybrid that uses OpenMP and CUDA together - and I measured when each one is the right choice.\n\nEverything I will show was measured by me on the same machine, and every number in the slides can be traced back to the raw measurement files in my repository.`;
  s.addNotes(`[Estimated speaking time: 0.5 min]\n\n${notes}`);
  LOG.push({ n: 1, section: "Introduction", title: "Title", minutes: 0.5, notes, text: `Title; Sunnihith Reddy Induru; CS 259 — Advanced Parallel Processing; San José State University; ${DATE}` });
}
// ---- 2 motivation
{
  const s = addSlide("CONTENT", "Introduction", "Why Parallelism Matters for Deep Learning", 1.0,
    `Neural-network inference looks complicated, but underneath it is a large number of repeated arithmetic operations - mostly matrix operations that multiply inputs by weights. My network performs about two hundred thousand multiply-adds for every single image, and a pass over the MNIST test set does that ten thousand times.\n\nRun one after another on a single CPU thread, that work becomes slow. There are two standard ways to speed it up. OpenMP splits the work across several CPU threads that share memory. CUDA launches thousands of lightweight threads on a GPU.\n\nBut there is a trap, and it is the theme of this talk: a GPU can compute very quickly while the complete application is much slower, because the application also has to preprocess the data, copy it across to the GPU, launch the kernels and synchronize. On my measurements the GPU kernels alone are ${f1("Sp:comp:gpuvsserial:4096")} times faster than serial code, but the complete CUDA pipeline is only ${f1("Sp:cuda:speedup:4096")} times faster. The rest of the talk explains why, and what a hybrid design can do about it.`,
    "Workload → repeated matrix operations → many arithmetic operations → need for CPU and GPU parallelism; GPU kernels fast, application slower (preprocessing, transfers, launch overhead).");
  const steps = ["Neural-network workload", "Repeated matrix operations", "Large number of arithmetic calculations", "Need for CPU and GPU parallelism"];
  const cols = [BLUE, GRAY, GREEN, PURPLE];
  steps.forEach((t, i) => { const x = 0.45 + i * 2.35; box(s, x, 1.3, 2.0, 1.0, t, cols[i], { fs: 14, bold: true }); if (i < 3) arrow(s, x + 2.0, 1.8, x + 2.35, 1.8, INK, 2); });
  bullets(s, ["Neural networks repeat the same computation many times", "Serial execution becomes slow for large workloads", "OpenMP: multiple CPU threads sharing memory", "CUDA: many GPU threads on separate device memory"], 0.45, 2.65, 5.3, 2.4, { fontSize: 15 });
  card(s, 6.0, 2.65, 3.55, 2.3, `${f1("Sp:comp:gpuvsserial:4096")}× vs ${f1("Sp:cuda:speedup:4096")}×`, `GPU kernels only vs the complete CUDA pipeline (speedup over serial, batch 4096, Spartan node)`, ORANGE, { bigSize: 26, labelSize: 13, bigH: 0.75 });
}
// ---- 3 problem statement
{
  const s = addSlide("CONTENT", "Introduction", "Performance Tradeoffs Across CPU, GPU, and Hybrid Execution", 1.0,
    `This is the question the whole project asks: how do serial CPU, OpenMP CPU, CUDA GPU and hybrid OpenMP-CUDA implementations compare when they execute the same neural-network inference workload?\n\nTo answer it properly I broke it into six research questions. One: how much speedup does OpenMP give over serial execution? Two: how does CUDA compare with serial and OpenMP? Three: how does batch size change CPU and GPU performance? Four: how much of the GPU's time is data transfer? Five: does hybrid CPU-GPU execution improve end-to-end performance? And six: how do the results relate to Amdahl's law and parallel overhead?\n\nI will come back to each of these - the results slides are organised around them.`,
    "Main question + RQ1–RQ6.");
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.45, y: 1.2, w: 9.1, h: 1.0, fill: { color: NAVY }, line: { color: NAVY }, rectRadius: 0.06 });
  T(s, "How do serial CPU, OpenMP CPU, CUDA GPU, and hybrid OpenMP–CUDA implementations compare when executing the same neural-network inference workload?", 0.65, 1.2, 8.7, 1.0, { fontSize: 16, color: "FFFFFF", valign: "middle", italic: true });
  const rq = ["How much speedup does OpenMP provide over serial execution?", "How does CUDA compare with serial and OpenMP execution?", "How does batch size affect CPU and GPU performance?", "How much GPU time is spent on data transfer?", "Does hybrid CPU–GPU execution improve end-to-end performance?", "How do the results relate to Amdahl’s Law and parallel overhead?"];
  const cc = [BLUE, GREEN, GRAY, ORANGE, PURPLE, INK];
  rq.forEach((t, i) => { const col = i % 2, row = Math.floor(i / 2), x = 0.45 + col * 4.65, y = 2.5 + row * 0.92;
    s.addShape(pres.shapes.OVAL, { x, y, w: 0.6, h: 0.6, fill: { color: cc[i] }, line: { color: cc[i] } });
    T(s, `${i + 1}`, x, y, 0.6, 0.6, { align: "center", valign: "middle", bold: true, color: "FFFFFF", fontSize: 18 });
    T(s, t, x + 0.75, y - 0.05, 3.75, 0.75, { fontSize: 14, valign: "middle" }); });
}
// ---- 4 execution models
{
  const s = addSlide("CONTENT", "Introduction", "Serial, OpenMP, CUDA, and Hybrid Execution Models", 1.5,
    `Before the results, I want everyone to understand how these four models differ, because the results only make sense with that picture in mind.\n\nSerial execution uses one CPU thread and processes the work strictly one piece after another. OpenMP uses several CPU threads, but they all share the same CPU memory; the work is divided among the threads, and there is a synchronization point at the end of each parallel loop. CUDA runs on the GPU, which has its own separate device memory, so data must be copied there first; the GPU then runs thousands of threads on independent pieces of data. The hybrid model gives different stages to different processors - the CPU threads prepare data while the GPU computes - and the memory is split between host and device.\n\nThe small diagrams in the last column show the idea: one thread, a fork into several threads and a join, a grid of GPU threads, and CPU plus GPU working together.`,
    "Table: model / main resource / memory model / main parallelism + mini diagrams.");
  const rows = [["Model", "Main resource", "Memory model", "Main parallelism", "Diagram"],
    ["Serial CPU", "One CPU thread", "Shared CPU memory", "None", ""], ["OpenMP", "Multiple CPU threads", "Shared CPU memory", "Thread-level parallelism", ""],
    ["CUDA", "GPU threads", "Separate device memory", "Massive data parallelism", ""], ["Hybrid", "CPU and GPU", "Host and device memory", "Coordinated parallelism", ""]];
  table(s, rows, 0.3, 1.15, 9.4, [1.4, 1.9, 2.1, 2.0, 2.0], 13, { rowH: [0.4, 0.8, 0.8, 0.8, 0.8] });
  const rowY = (i) => 1.15 + 0.4 + 0.8 * i; const dx = 7.75;
  for (let k = 0; k < 4; k++) box(s, dx + k * 0.42, rowY(0) + 0.27, 0.34, 0.26, `${k + 1}`, GRAY, { fs: 10 });
  box(s, dx, rowY(1) + 0.27, 0.34, 0.26, "M", BLUE, { fs: 10 });
  for (let k = 0; k < 3; k++) box(s, dx + 0.5, rowY(1) + 0.1 + k * 0.2, 0.8, 0.15, "", BLUE);
  box(s, dx + 1.46, rowY(1) + 0.27, 0.34, 0.26, "M", BLUE, { fs: 10 });
  for (let a = 0; a < 6; a++) for (let b = 0; b < 3; b++) box(s, dx + a * 0.3, rowY(2) + 0.12 + b * 0.19, 0.24, 0.14, "", GREEN);
  box(s, dx, rowY(3) + 0.2, 0.55, 0.4, "CPU", BLUE, { fs: 10 }); arrow(s, dx + 0.55, rowY(3) + 0.4, dx + 0.85, rowY(3) + 0.4, INK, 1.5);
  for (let a = 0; a < 4; a++) for (let b = 0; b < 3; b++) box(s, dx + 0.9 + a * 0.24, rowY(3) + 0.12 + b * 0.19, 0.2, 0.14, "", GREEN);
  T(s, "Serial: one thread, one piece at a time.  OpenMP: fork → parallel loop → barrier/join (M = master thread).  CUDA: a grid of GPU threads.  Hybrid: CPU and GPU working together.", 0.3, 4.9, 9.4, 0.45, { fontSize: 12, color: MUTED });
}
pres.addSection({ title: "Method" });
// ---- 5 workload
{
  const s = addSlide("CONTENT", "Method", "MNIST Inference Workload", 1.0,
    `The workload is MNIST handwritten-digit classification, and I measure inference, not training. Each image is 28 by 28 pixels - 784 numbers - and the network turns those 784 features into a predicted digit from zero to nine. The image on the slide is the first real image of the MNIST test set; the weights I use predict a seven for it, which is also its true label.\n\nEvery pass processes all ten thousand MNIST test images, in batches of 1, 8, 32, 64, 128, 256, 1,024 or 4,096 images. The computation is float32, and every implementation loads exactly the same trained weight file. The network classifies ${num("Sp:accuracy")} percent of the test images correctly - that number comes from my training log and from the correctness runs.\n\nI chose MNIST because it is a realistic but manageable deep-learning workload: small enough that I could implement it directly in C++ and CUDA, so I control every thread and every copy, without a deep-learning framework hiding them.`,
    `10,000 test images; batches 1–4096; float32; same weights; accuracy ${num("Sp:accuracy")} %.`);
  s.addImage({ path: path.join(__dirname, "assets", "mnist_sample.png"), x: 0.45, y: 1.3, w: 1.7, h: 1.7, altText: "MNIST test image 0, a handwritten seven" });
  T(s, "MNIST test image 0\n(true label 7)", 0.45, 3.02, 1.7, 0.45, { fontSize: 11, color: MUTED, align: "center" });
  const flow = [["28×28 pixels", GRAY], ["784 input features", BLUE], ["Neural network\n784→256→10", GREEN], ["Predicted digit: 7", PURPLE]];
  arrow(s, 2.15, 2.15, 2.5, 2.15, INK, 2);
  flow.forEach((f, i) => { const x = 2.5 + i * 1.8; box(s, x, 1.6, 1.5, 1.1, f[0], f[1], { fs: 13, bold: true }); if (i < 3) arrow(s, x + 1.5, 2.15, x + 1.8, 2.15, INK, 2); });
  card(s, 0.45, 3.65, 2.1, 1.45, "10,000", "MNIST test images per pass", BLUE, { bigSize: 26, labelSize: 12, bigH: 0.55 });
  card(s, 2.7, 3.65, 2.1, 1.45, "1 – 4096", "images per batch (8 sizes)", PURPLE, { bigSize: 26, labelSize: 12, bigH: 0.55 });
  card(s, 4.95, 3.65, 2.1, 1.45, "Float32", "same trained weights everywhere", GRAY, { bigSize: 26, labelSize: 12, bigH: 0.55 });
  card(s, 7.2, 3.65, 2.35, 1.45, `${num("Sp:accuracy")} %`, "MNIST test accuracy (verified)", GREEN, { bigSize: 26, labelSize: 12, bigH: 0.55 });
}
// ---- 6 network computation
{
  const s = addSlide("CONTENT", "Method", "Neural-Network Computation", 1.0,
    `This is the entire network. 784 input features go through a fully connected layer from 784 to 256 units, a ReLU activation, a second fully connected layer from 256 to 10 outputs, and an argmax that picks the predicted digit. That is two hundred and three thousand multiply-adds per image.\n\nIn the program the work is split into four measured stages: preprocessing, which standardizes each image; the hidden layer; the output layer; and the argmax.\n\nThe key point for parallelism is at the bottom: each output element - for example hidden unit j of image b - is a dot product that does not depend on any other output element in the same layer. So all of them can be computed at the same time. That independence is exactly what OpenMP threads and CUDA threads exploit. What is not independent is the order of the layers: the output layer needs the hidden layer first.`,
    "784 → FC 784→256 → ReLU → FC 256→10 → argmax; four stages; independent output elements.");
  const nodes = [["784 input\nfeatures", GRAY], ["Fully connected\n784 → 256", BLUE], ["ReLU", GRAY], ["Fully connected\n256 → 10", BLUE], ["argmax", PURPLE], ["Predicted\ndigit", GREEN]];
  nodes.forEach((n, i) => { const x = 0.45 + i * 1.55; box(s, x, 1.3, 1.3, 0.95, n[0], n[1], { fs: 13, bold: true }); if (i < 5) arrow(s, x + 1.3, 1.78, x + 1.55, 1.78, INK, 2); });
  T(s, "Four measured stages", 0.45, 2.55, 4, 0.35, { fontSize: 15, bold: true });
  ["1  Preprocessing (per-image standardization)", "2  Hidden layer", "3  Output layer", "4  Argmax"].forEach((t, i) => { box(s, 0.45, 2.95 + i * 0.5, 3.9, 0.42, t, [LGRAY, BLUE, GREEN, PURPLE][i], { fs: 13, bold: true, color: i === 0 ? INK : "FFFFFF" }); });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 4.7, y: 2.55, w: 4.85, h: 2.4, fill: { color: LIGHT }, line: { color: LIGHT }, rectRadius: 0.08 });
  T(s, "Independent outputs", 4.9, 2.65, 4.4, 0.35, { fontSize: 15, bold: true });
  T(s, "h[b][j] = ReLU(b1[j] + Σ x[b][k]·W1[k][j])", 4.9, 3.02, 4.5, 0.35, { fontSize: 12, fontFace: "Consolas", color: BLUE });
  bullets(s, ["Every (image b, unit j) pair is computed independently", "→ one OpenMP work item or one CUDA thread each", "Layers of one batch stay in order: hidden → output → argmax", "203,264 multiply-adds per image; 203,530 parameters"], 4.9, 3.45, 4.5, 1.45, { fontSize: 13 });
}
// ---- 7 four implementations
{
  const s = addSlide("CONTENT", "Method", "Four Implementations of the Same Computation", 1.5,
    `Here are the four implementations side by side, colour-coded by the resource that executes each stage.\n\nSerial, in gray: one CPU thread does the preprocessing, the hidden layer and the output layer with argmax. OpenMP, in blue: the same stages, but each one is split across T CPU threads. CUDA: the preprocessing still runs on a single CPU thread - which is why I call it "CUDA with single-threaded preprocessing", not "GPU-only" - then the batch is copied to the GPU, three kernels run, and the results are copied back. Hybrid: OpenMP threads do the preprocessing into pinned memory, the copies are asynchronous, the kernels run on three CUDA streams, so different batches overlap.\n\nOne more thing, at the bottom of the slide: hybrid-sequential is a diagnostic control, not a fifth implementation. It uses OpenMP preprocessing and CUDA computation, but without overlapping batches. I use it later to separate two effects: the benefit of parallel preprocessing and the benefit of overlap.`,
    "Serial | OpenMP | CUDA (1-thread preprocessing) | Hybrid; hybrid-sequential = diagnostic control.");
  const lanes = [["Serial CPU", [["Preprocess\n(1 thread)", GRAY], ["Hidden layer", GRAY], ["Output layer\n+ argmax", GRAY]]],
    ["OpenMP CPU", [["Preprocess\n(T threads)", BLUE], ["Hidden layer\n(T threads)", BLUE], ["Output layer\n+ argmax (T)", BLUE]]],
    ["CUDA pipeline", [["Preprocess\n(1 CPU thread)", GRAY], ["Host→device\ncopy", ORANGE], ["CUDA kernels", GREEN], ["Device→host\ncopy", ORANGE]]],
    ["Hybrid pipeline", [["OpenMP preprocess\n(pinned memory)", BLUE], ["Async\ncopy in", ORANGE], ["CUDA kernels\n(3 streams)", GREEN], ["Async\ncopy out", ORANGE]]]];
  lanes.forEach((ln, i) => { const y = 1.2 + i * 0.88; T(s, ln[0], 0.45, y, 1.55, 0.7, { fontSize: 13, bold: true, valign: "middle" });
    ln[1].forEach((b, j) => { const x = 2.05 + j * 1.85; box(s, x, y, 1.65, 0.7, b[0], b[1], { fs: 11, bold: true }); if (j < ln[1].length - 1) arrow(s, x + 1.65, y + 0.35, x + 1.85, y + 0.35, INK, 1.5); }); });
  [["1 CPU thread", GRAY], ["OpenMP threads", BLUE], ["GPU threads", GREEN], ["PCIe copy", ORANGE]].forEach((l, i) => { box(s, 2.05 + i * 1.85, 4.82, 0.22, 0.22, "", l[1]); T(s, l[0], 2.35 + i * 1.85, 4.8, 1.5, 0.28, { fontSize: 11, valign: "middle" }); });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.45, y: 4.78, w: 1.5, h: 0.34, fill: { color: LPURPLE }, line: { color: LPURPLE }, rectRadius: 0.05 });
  T(s, "Control only", 0.45, 4.78, 1.5, 0.34, { fontSize: 11, bold: true, color: "FFFFFF", align: "center", valign: "middle" });
  T(s, "Hybrid-sequential = diagnostic control (not a fifth implementation): OpenMP preprocessing + CUDA, without overlapping batches.", 0.45, 5.17, 8.6, 0.3, { fontSize: 11, color: MUTED });
}
// ---- 8 CUDA execution model
{
  const s = addSlide("CONTENT", "Method", "CUDA Host–Device Execution", 1.5,
    `This slide shows how a CUDA program works. On the left is the data path. The CPU is the host and the GPU is the device, and they have separate memories. The input batch starts in CPU memory, is copied across the PCIe connection into GPU global memory, and then the host launches a kernel. When the kernel finishes, the predictions are copied back.\n\nOn the right is how the GPU organizes its threads. A kernel launch creates a grid. The grid is made of thread blocks, and each block is made of threads. In my hidden-layer kernel a block is a square of d by d threads, and thread tx, ty of block bx, by computes exactly one output element: hidden unit j equals bx times d plus tx, for image b equals by times d plus ty. I tested three block sizes: 8 by 8, which is 64 threads, 16 by 16, which is 256 threads and my default, and 32 by 32, which is 1,024 threads.\n\nTwo consequences matter for the results. First, every copy and every launch costs time that has nothing to do with computation. Second, for a batch of just one image the grid has very few useful threads, so the GPU is badly under-used.`,
    "Host memory → H2D copy → device memory → kernel launch → grid → blocks → threads → D2H copy → predictions; 8×8, 16×16, 32×32.");
  const L = [["CPU host memory\n(input batch)", GRAY], ["GPU global memory", GREEN], ["CUDA kernel launch\n<<<grid, block>>>", GREEN], ["GPU global memory\n(results)", GREEN], ["CPU predictions", GRAY]];
  L.forEach((b, i) => { const y = 1.15 + i * 0.85; box(s, 0.45, y, 2.2, 0.5, b[0], b[1], { fs: 12, bold: true }); if (i < 4) arrow(s, 1.1, y + 0.5, 1.1, y + 0.85, INK, 1.5); });
  [["host→device copy (PCIe)", 1.15 + 0.5 + 0.02], ["kernel launch", 1.15 + 0.85 + 0.5 + 0.02], ["kernel runs on the GPU", 1.15 + 1.7 + 0.5 + 0.02], ["device→host copy (PCIe)", 1.15 + 2.55 + 0.5 + 0.02]].forEach((l, i) => T(s, l[0], 1.2, l[1], 1.9, 0.3, { fontSize: 10, color: i % 3 === 0 ? ORANGE : MUTED, bold: true, valign: "middle" }));
  T(s, "CUDA grid", 3.3, 1.15, 2, 0.3, { fontSize: 13, bold: true });
  for (let a = 0; a < 4; a++) for (let b = 0; b < 3; b++) box(s, 3.3 + a * 0.62, 1.5 + b * 0.5, 0.55, 0.43, a === 1 && b === 1 ? "block" : "", a === 1 && b === 1 ? PURPLE : GREEN, { fs: 10, bold: true });
  T(s, "blocks (bx, by)", 3.3, 3.0, 2.5, 0.28, { fontSize: 11, color: MUTED });
  arrow(s, 4.55, 2.5, 5.85, 2.2, PURPLE, 1.5);
  T(s, "One block = d × d threads", 5.95, 1.15, 3.6, 0.3, { fontSize: 13, bold: true });
  for (let a = 0; a < 6; a++) for (let b = 0; b < 6; b++) box(s, 5.95 + a * 0.3, 1.5 + b * 0.3, 0.26, 0.26, a === 3 && b === 2 ? "T" : "", a === 3 && b === 2 ? ORANGE : LGRAY, { fs: 10, bold: true });
  T(s, "thread (tx, ty)\ncomputes ONE output:\nunit j = bx·d + tx\nimage b = by·d + ty", 7.85, 1.5, 1.75, 1.3, { fontSize: 11 });
  [["8×8", "64 threads"], ["16×16", "256 threads (default)"], ["32×32", "1,024 threads"]].forEach((b, i) => card(s, 3.3 + i * 2.1, 3.45, 2.0, 1.1, b[0], b[1], [GRAY, GREEN, GRAY][i], { bigSize: 22, labelSize: 11, bigH: 0.5 }));
  T(s, "Grid size = ⌈256 / d⌉ × ⌈B / d⌉ blocks for batch size B. A batch of one image leaves most launched threads without work.", 3.3, 4.7, 6.3, 0.55, { fontSize: 12, color: MUTED });
}
// ---- 9 hybrid pipeline
{
  const s = addSlide("CONTENT", "Method", "Hybrid CPU–GPU Pipeline", 2.0,
    `This is the central idea of the hybrid implementation. In the CUDA pipeline, the GPU sits idle while the CPU preprocesses, and the CPU waits while the GPU works. The hybrid removes that waiting.\n\nThe diagram is a schematic, not measured data. The top lane is the CPU: OpenMP threads preprocess batch 1, then batch 2, then batch 3. Below are three CUDA streams. As soon as batch 1 is preprocessed, its host-to-device copy, its kernels and its device-to-host copy go into stream 0. While the GPU works on batch 1, the CPU is already preprocessing batch 2, which is then handled by stream 1, and batch 3 goes to stream 2. Batches are assigned round-robin, and each stream has its own device buffers and its own pinned host buffers. Pinned memory is what allows copies to be asynchronous.\n\nThe important statement is on the slide: within one batch, the hidden layer, the output layer and the argmax depend on each other, so they stay in order. The overlap happens only between different batches.\n\nFinally, the hybrid-sequential control: it uses OpenMP preprocessing but waits for each batch to finish before starting the next. Comparing the CUDA pipeline, the control and the full hybrid lets me say how much of the gain comes from parallel preprocessing, and how much comes from overlap.`,
    "OpenMP preprocesses batch i+1 while CUDA copies/computes batch i; three streams; layers within a batch stay ordered; overlap between batches.");
  const X0 = 2.2;
  const seg = (x, y, w, c, t) => { box(s, x, y, w, 0.34, t, c, { fs: 10, bold: true, line: "FFFFFF" }); };
  T(s, "CPU\n(OpenMP)", 0.45, 1.3, 1.6, 0.5, { fontSize: 12, bold: true, color: BLUE, valign: "middle" });
  for (let i = 0; i < 6; i++) seg(X0 + i * 1.1, 1.3, 0.8, BLUE, `pre b${i + 1}`);
  [0, 1, 2].forEach((st) => { T(s, `CUDA stream ${st}`, 0.45, 2.0 + st * 0.5, 1.7, 0.34, { fontSize: 12, bold: true, color: GREEN, valign: "middle" }); });
  for (let i = 0; i < 6; i++) { const st = i % 3, x = X0 + 0.8 + i * 1.1, y = 2.0 + st * 0.5;
    seg(x, y, 0.28, ORANGE, "H2D"); seg(x + 0.28, y, 0.62, GREEN, `kern b${i + 1}`); seg(x + 0.9, y, 0.28, ORANGE, "D2H"); }
  arrow(s, X0 + 0.4, 1.64, X0 + 0.95, 2.0, INK, 1);
  T(s, "Schematic (not measured). Pinned host memory allows asynchronous copies; a stream slot is reused only after its batch has finished.", 0.45, 3.55, 9.1, 0.4, { fontSize: 12, italic: true, color: MUTED });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.45, y: 4.05, w: 9.1, h: 0.62, fill: { color: PURPLE }, line: { color: PURPLE }, rectRadius: 0.06 });
  T(s, "Within one batch the hidden layer, output layer and argmax remain dependency-ordered. The overlap occurs between different batches.", 0.65, 4.05, 8.7, 0.62, { fontSize: 15, bold: true, color: "FFFFFF", valign: "middle" });
  T(s, "Hybrid-sequential (control): OpenMP preprocessing, but no overlap — separates the benefit of parallel preprocessing from the benefit of overlap.", 0.45, 4.8, 9.1, 0.45, { fontSize: 13 });
}
// ---- 10 setup
{
  const s = addSlide("CONTENT", "Method", "Experimental Setup and Measurement Protocol", 1.25,
    `Here is exactly how I measured. The dataset is the ten thousand MNIST test images in float32. Each configuration gets three warm-up passes that are not recorded, followed by twenty recorded passes - and every recorded pass is kept as a row in a raw CSV file; nothing is removed.\n\nGPU stages are timed with CUDA events; the end-to-end time is the wall-clock time of the whole pass. One-time costs - creating the CUDA context, allocating buffers, uploading the weights - are excluded from the steady-state timing, and I measured them separately: about ${f1("Sp:cold:ctor:mean")} milliseconds in total.\n\nThe main platform is a Spartan GPU node with a Tesla K40m and two Xeon E5-2680 v4 CPUs. The node has 28 physical cores and 28 logical CPUs according to lscpu, and my jobs were allocated 24, so OpenMP uses at most 24 threads.\n\nTwo rules matter. All CPU-versus-GPU comparisons use the Spartan node only. The Apple M4 laptop is used only as a separate CPU scalability platform, and its numbers are never mixed with the Spartan GPU comparisons.`,
    "Setup table; Spartan node for CPU-vs-GPU; M4 separate.");
  const rows = [["Item", "Configuration"], ["Dataset", "10,000 MNIST test images per pass"], ["Precision", "Float32"], ["Warm-up", "3 unrecorded passes"], ["Measurement", "20 recorded passes (all rows kept)"], ["GPU timing", "CUDA events (per stage)"], ["End-to-end timing", "Wall-clock time of the whole pass"],
    ["One-time setup", `Excluded from steady state (measured separately: ${f1("Sp:cold:ctor:mean")} ms)`], ["Main GPU", "Tesla K40m (CUDA 11.7)"], ["CPU", "2× Xeon E5-2680 v4: 28 cores / 28 logical CPUs (lscpu)"], ["OpenMP limit", "24 allocated threads"]];
  table(s, rows, 0.45, 1.15, 6.3, [1.7, 4.6], 12, { rowH: 0.33 });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 7.0, y: 1.15, w: 2.55, h: 3.6, fill: { color: LIGHT }, line: { color: LIGHT }, rectRadius: 0.08 });
  T(s, "Rules", 7.15, 1.25, 2.3, 0.3, { fontSize: 15, bold: true });
  bullets(s, ["CPU vs GPU: Spartan node only", "Apple M4 (10 cores): separate CPU scalability platform; never mixed with GPU results", "All raw measurements retained", "Mean, median, std. dev., min, max reported where needed"], 7.15, 1.6, 2.3, 3.1, { fontSize: 12 });
}
pres.addSection({ title: "Results" });
// ---- 11 correctness
{
  const V = SER.validation; const g = (n) => V.find((v) => v.group.indexOf(n) === 0);
  const sup = (e) => String(e).replace(/-/g, "⁻").replace(/\d/g, (d) => "⁰¹²³⁴⁵⁶⁷⁸⁹"[d]);
  const sci = (x) => { if (x === 0) return "0 (bit-identical)"; const [m, e] = x.toExponential(1).split("e"); return `${m}×10${sup(parseInt(e))}`; };
  const row = (label, n) => { const v = g(n); return [label, `${v.passed} / ${v.n}`, sci(v.maxerr), `${v.agree.toFixed(2)} %`, n.indexOf("Serial float32") === 0 ? "—" : `${v.acc.toFixed(2)} %`]; };
  const s = addSlide("CONTENT", "Results", "Correctness Across Implementations", 0.75,
    `Before I trust any timing, I checked that every implementation computes the same thing. Every implementation is compared with the serial reference on all ten thousand images, over several batch sizes, thread counts, block sizes and stream counts - eighty comparisons in the reference build, and all of them pass.\n\nOpenMP is bit-identical to serial. CUDA and both hybrid variants differ by at most ${num("Sp:val:cuda:maxerr")} in the logits - which is tiny - and they predict exactly the same digit as serial for every image. Accuracy is ${num("Sp:accuracy")} percent everywhere.\n\nThe small differences are expected: the operations and the source-level order of the sums are the same, but compilers can apply floating-point optimizations such as fused multiply-add. The correctness checks run outside the timed region, and I would not accept a performance result from an implementation that failed them.`,
    "Correctness table: comparisons passed, max logit difference, prediction agreement, accuracy.");
  table(s, [["Comparison", "Passed", "Max logit difference", "Prediction agreement", "Accuracy"], row("Serial vs OpenMP", "Serial vs OpenMP"), row("Serial vs CUDA", "Serial vs CUDA"), row("Serial vs hybrid-sequential (control)", "Serial vs Hybrid-sequential"), row("Serial vs hybrid-pipelined", "Serial vs Hybrid-pipelined"), row("Serial float32 vs NumPy float64 (first 100 images)", "Serial float32")],
    0.45, 1.25, 9.1, [3.6, 1.0, 1.9, 1.5, 1.1], 13, { rowH: 0.42 });
  bullets(s, ["Same mathematical operations, data, weights, dimensions, precision and source-level reduction order", "Small differences can come from compiler floating-point optimizations such as fused multiply-add", "Checks run outside the timed region; tolerance (1×10⁻⁴) fixed before measuring"], 0.45, 4.0, 9.1, 1.3, { fontSize: 13 });
}
// ---- 12 OpenMP scalability
{
  const sc = SER.scale_spartan; const thr = sc["1"].map((x) => String(x.threads));
  const cols = { "1": "93C5FD", "256": BLUE, "4096": "1E3A8A" };
  const mk = (key, ci) => ["1", "256", "4096"].map((b) => ({ name: `Batch ${b}`, values: sc[b].map((x) => +x[key].toFixed(4)), ci: ci ? sc[b].map((x) => +x[ci].toFixed(4)) : null, color: cols[b] }));
  const s = addSlide("CONTENT", "Results", "OpenMP Scalability", 1.5,
    `RQ1: how much speedup does OpenMP give? These three charts are all from the Spartan node, for three batch sizes - 1, 256 and 4096 images - against the number of OpenMP threads.\n\nLeft: execution time per pass on a log scale. For batches of 256 and 4096 it falls from about twelve hundred milliseconds with one thread to about ${f1("Sp:omp:best:e2e:4096")} milliseconds with 24 threads. Middle: the speedup over serial. For large batches it follows the ideal line closely - ${f1("Sp:omp:speedup:4096:24")} times with 24 threads at batch 4096. Right: parallel efficiency, ${f2("Sp:omp:eff:4096:24")} at 24 threads for batch 4096.\n\nBatch size 1 behaves differently: the speedup saturates at about ${f1("Sp:omp:best:speedup:1")} times and efficiency drops to ${f2("Sp:omp:eff:1:24")}, because one image offers only 16 work items per stage and every stage ends in a barrier - there is too little work per synchronization.\n\nThe Apple M4 is a different story and is shown separately in the backup: its speedup follows the ideal up to its 4 performance cores - ${f2("Mac:omp:speedup:4096:4")} times with 4 threads - then flattens at ${f1("Mac:omp:speedup:4096:10")} times with 10 threads. The two machines are different architectures, so they must be read separately. I did not isolate memory bandwidth as a cause of any flattening; what I can say is what the data shows.`,
    `Spartan: time, speedup, efficiency vs threads; ${f1("Sp:omp:speedup:4096:24")}× at 24 threads (batch 4096); batch 1 saturates; M4 in backup.`);
  const y = 1.15, w = 3.05, h = 3.1;
  chart(s, "line", mk("time", "time_ci"), thr, { x: 0.3, y, w, h, title: "Time per pass", valAxisTitle: "Time (ms, log scale)", catAxisTitle: "OpenMP threads", valAxisLogScaleBase: 10, valAxisMinVal: 10, valAxisMaxVal: 10000, legendFontSize: 10, catAxisLabelFontSize: 10, valAxisLabelFontSize: 10 });
  chart(s, "line", mk("speedup", "speedup_ci").concat([{ name: "Ideal", values: sc["1"].map((x) => x.threads), color: LGRAY, dash: "dash" }]), thr, { x: 3.4, y, w, h, title: "Speedup over serial", valAxisTitle: "Speedup (×)", catAxisTitle: "OpenMP threads", legendFontSize: 10, catAxisLabelFontSize: 10, valAxisLabelFontSize: 10, valAxisMinVal: 0 });
  chart(s, "line", mk("eff", "eff_ci"), thr, { x: 6.5, y, w, h, title: "Parallel efficiency", valAxisTitle: "Efficiency (speedup / threads)", catAxisTitle: "OpenMP threads", legendFontSize: 10, catAxisLabelFontSize: 10, valAxisLabelFontSize: 10, valAxisMinVal: 0, valAxisMaxVal: 1.1 });
  bullets(s, [`Spartan, batch 4096: ${f1("Sp:omp:speedup:4096:24")}× with 24 threads (efficiency ${f2("Sp:omp:eff:4096:24")}); batch 1: only ${f1("Sp:omp:best:speedup:1")}× — too little work per barrier`, `Apple M4 (separate platform, see backup): flattens beyond its 4 performance cores — ${f1("Mac:omp:speedup:4096:10")}× with 10 threads`], 0.45, 4.35, 9.1, 0.9, { fontSize: 13 });
}
// ---- 13 CUDA kernel vs end-to-end
{
  const lab = B.map(String);
  const s = addSlide("CONTENT", "Results", "CUDA Computation and End-to-End Performance", 1.75,
    `RQ2 and RQ3: how does CUDA compare, and how does batch size matter? I split this slide into two charts on purpose, because they answer different questions.\n\nThe left chart is end-to-end: the time of the whole pass, including preprocessing, copies, launches and synchronization. It shows serial, the best OpenMP configuration, and the CUDA pipeline with single-threaded preprocessing. The right chart is compute-only: only the hidden layer, the output layer and the argmax - for the CPU it is the sum of those timed stages, for the GPU it is the kernel time measured with CUDA events.\n\nCompute-only, the GPU kernels are ${f1("Sp:comp:gpuvsserial:4096")} times faster than serial and ${f2("Sp:comp:gpuvsomp:4096")} times faster than the best OpenMP configuration at batch 4096. End-to-end, the CUDA pipeline is ${f1("Sp:cuda:speedup:4096")} times faster than serial and only ${f2("Sp:cuda:vscpu:4096")} times faster than OpenMP - because preprocessing and copies are included. Notice the batch-1 end: CUDA end-to-end is ${f2("Sp:cuda:speedup:1")} times serial, which means it is slower; even compute-only the kernels are just ${f2("Sp:comp:gpuvsserial:1")} times faster. The GPU needs enough work to amortize its overheads.\n\nA caution on one number: comparing the kernel time with OpenMP's end-to-end time would give about 2.49; the like-for-like compute-only comparison is ${f2("Sp:comp:gpuvsomp:4096")}.`,
    `End-to-end: serial, OpenMP, CUDA pipeline. Compute-only: serial, OpenMP, CUDA kernels. Kernels ${f1("Sp:comp:gpuvsserial:4096")}× vs pipeline ${f1("Sp:cuda:speedup:4096")}× (batch 4096); batch 1 CUDA ${f2("Sp:cuda:speedup:1")}×.`);
  const common = { catAxisTitle: "Batch size (images per batch)", valAxisLogScaleBase: 10, valAxisMinVal: 10, valAxisMaxVal: 10000, legendFontSize: 11 };
  chart(s, "line", [{ name: "Serial CPU", values: SER.serial.map((v) => +v.toFixed(3)), ci: SER.serial_ci, color: GRAY }, { name: "OpenMP (best threads)", values: SER.omp.map((v) => +v.toFixed(3)), ci: SER.omp_ci, color: BLUE }, { name: CUDA, values: SER.cuda.map((v) => +v.toFixed(3)), ci: SER.cuda_ci, color: GREEN }],
    lab, Object.assign({ x: 0.3, y: 1.15, w: 4.6, h: 3.2, title: "End-to-end (stages 0–3), Spartan", valAxisTitle: "Time per pass (ms, log scale)" }, common));
  chart(s, "line", [{ name: "Serial CPU (stages 1–3)", values: SER.serial_c.map((v) => +v.toFixed(3)), ci: SER.serial_c_ci, color: GRAY }, { name: "OpenMP (stages 1–3)", values: SER.omp_c.map((v) => +v.toFixed(3)), ci: SER.omp_c_ci, color: BLUE }, { name: "CUDA kernels only", values: SER.kernel.map((v) => +v.toFixed(3)), ci: SER.kernel_ci, color: "0F766E" }],
    lab, Object.assign({ x: 5.05, y: 1.15, w: 4.65, h: 3.2, title: "Compute-only (stages 1–3), Spartan", valAxisTitle: "Time per pass (ms, log scale)" }, common));
  bullets(s, [`Batch 4096: kernels ${f1("Sp:comp:gpuvsserial:4096")}× serial (compute-only) vs pipeline ${f1("Sp:cuda:speedup:4096")}× (end-to-end)`, `Batch 1: CUDA end-to-end ${f2("Sp:cuda:speedup:1")}× — slower than serial; overheads dominate`], 0.45, 4.45, 9.1, 0.85, { fontSize: 13 });
}
// ---- 14 breakdown
{
  const lab = B.map(String);
  const pct = (key) => B.map((_, i) => +(SER[key][i] / SER.cuda[i] * 100).toFixed(2));
  const s = addSlide("CONTENT", "Results", "Where the CUDA Pipeline Time Goes", 1.25,
    `RQ4: how much GPU time is spent on data transfer? This stacked chart splits the end-to-end time of the CUDA pipeline into stages, as a percentage, for each batch size.\n\nLook at the two ends. At batch 1 the kernels are ${f1("Sp:cuda:kshare:1")} percent of the time, the copies are ${f1("Sp:cuda:tshare:1")} percent, and launch, API and synchronization overhead is ${f1("Sp:cuda:othershare:1")} percent. At batch 4096 the picture flips: kernels are ${f1("Sp:cuda:kshare:4096")} percent, the single-threaded CPU preprocessing is ${f1("Sp:cuda:preshare:4096")} percent - ${f1("Sp:cuda:pre:4096")} milliseconds that stay constant for every batch size - and the copies are only ${f1("Sp:cuda:tshare:4096")} percent.\n\nSo transfers matter most for small batches, but for large batches the dominant non-GPU cost is not the PCIe copy, it is the single-threaded preprocessing on the CPU. That is the lesson: a fast kernel does not automatically make a fast application. The gray "other" segment is the part of the wall-clock time not covered by the four timed stages - launch, API calls and synchronization - so it is a residual, not a directly timed quantity.`,
    `Batch 1: kernels ${f1("Sp:cuda:kshare:1")} %, copies ${f1("Sp:cuda:tshare:1")} %; batch 4096: kernels ${f1("Sp:cuda:kshare:4096")} %, preprocessing ${f1("Sp:cuda:preshare:4096")} %, copies ${f1("Sp:cuda:tshare:4096")} %.`);
  const sers = [{ name: "CPU preprocessing (1 thread)", key: "pre", color: BLUE }, { name: "Host-to-device copy", key: "h2d", color: ORANGE }, { name: "CUDA kernels", key: "kernel", color: GREEN }, { name: "Device-to-host copy", key: "d2h", color: LORANGE }, { name: "Other: launch / API / sync (residual)", key: "other", color: LGRAY }];
  chart(s, "bar", sers.map((q) => ({ name: q.name, values: pct(q.key), color: q.color })), lab, { x: 0.3, y: 1.15, w: 6.1, h: 4.1, barDir: "col", barGrouping: "stacked", barGapWidthPct: 40, title: "Share of end-to-end time, CUDA pipeline (Spartan)", valAxisTitle: "Share of end-to-end time (%)", catAxisTitle: "Batch size (images per batch)", valAxisMaxVal: 100, valAxisMinVal: 0, legendFontSize: 10 });
  const pc = (k, b) => (SER[k][iB(b)] / SER.cuda[iB(b)] * 100).toFixed(1) + " %";
  table(s, [["Stage (% of time)", "Batch 1", "Batch 4096"], ["Preprocessing", pc("pre", 1), pc("pre", 4096)], ["Host→device", pc("h2d", 1), pc("h2d", 4096)], ["CUDA kernels", pc("kernel", 1), pc("kernel", 4096)], ["Device→host", pc("d2h", 1), pc("d2h", 4096)], ["Other (residual)", pc("other", 1), pc("other", 4096)]], 6.55, 1.3, 3.1, [1.45, 0.8, 0.85], 12, { rowH: 0.36 });
  T(s, `Preprocessing is ${r(SER.pre[iB(4096)])} ms per pass at every batch size; the 4096-image host→device copy takes ${r(SER.h2d[iB(4096)], 2)} ms.`, 6.55, 3.65, 3.1, 1.3, { fontSize: 13 });
}
// ---- 15 hybrid results
{
  const lab = B.map(String);
  const vs = B.map((_, i) => SER.cuda[i] / SER.hyb[i]);
  const s = addSlide("CONTENT", "Results", "Hybrid Execution Reduces End-to-End Time", 1.75,
    `RQ5: does hybrid execution improve end-to-end performance? This chart compares three configurations at every batch size: the CUDA pipeline, the hybrid-sequential control, and the pipelined hybrid. Each hybrid point uses the best OpenMP thread count for that batch size.\n\nThe pipelined hybrid is faster than the CUDA pipeline at all eight batch sizes - by ${Math.min(...vs).toFixed(2)} to ${Math.max(...vs).toFixed(2)} times; the 95 percent confidence intervals are tiny and a Welch test gives p below ten to the minus thirty-two for every batch size. At batch 4096 it needs ${f1("Sp:hyb:best:e2e:4096")} milliseconds against ${f1("Sp:cuda:e2e:4096")}.\n\nTwo effects, separated by the control. First, parallel preprocessing alone - the hybrid-sequential control - gives ${f2("Sp:hseq:vscuda:4096")} times over the CUDA pipeline at batch 4096. Second, overlapping the batches adds another ${f2("Sp:hyb:vshseq:4096")} times. The hybrid time is only ${f2("Sp:hyb:vskernel:4096")} times the kernel-only time, so preprocessing and copies are nearly hidden behind the kernels.\n\nBut I do not claim hybrid is always best. Against the best OpenMP configuration, the hybrid is faster only from batch ${num("Sp:hyb:crossover")} upward; at batch sizes 1 and 8, plain OpenMP is faster, because there the GPU path is dominated by overhead.`,
    `Hybrid ${f1("Sp:hyb:best:e2e:4096")} ms vs CUDA pipeline ${f1("Sp:cuda:e2e:4096")} ms (batch 4096); effects: ${f2("Sp:hseq:vscuda:4096")}× preprocessing, ${f2("Sp:hyb:vshseq:4096")}× overlap; hybrid faster than OpenMP from batch ${num("Sp:hyb:crossover")}.`);
  chart(s, "line", [{ name: CUDA, values: SER.cuda.map((v) => +v.toFixed(3)), ci: SER.cuda_ci, color: GREEN }, { name: "Hybrid-sequential (control)", values: SER.hseq.map((v) => +v.toFixed(3)), ci: SER.hseq_ci, color: LPURPLE, dash: "dash" }, { name: "Hybrid-pipelined", values: SER.hyb.map((v) => +v.toFixed(3)), ci: SER.hyb_ci, color: PURPLE }],
    lab, { x: 0.3, y: 1.15, w: 6.2, h: 3.5, title: "End-to-end time, best thread count (Spartan)", valAxisTitle: "Time per pass (ms, log scale)", catAxisTitle: "Batch size (images per batch)", valAxisLogScaleBase: 10, valAxisMinVal: 10, valAxisMaxVal: 10000 });
  card(s, 6.7, 1.2, 2.9, 1.15, `${f2("Sp:hseq:vscuda:4096")}×`, "parallel preprocessing alone (control vs CUDA pipeline, batch 4096)", BLUE, { bigSize: 28, labelSize: 11, bigH: 0.5 });
  card(s, 6.7, 2.45, 2.9, 1.15, `${f2("Sp:hyb:vshseq:4096")}×`, "extra from overlapping batches (pipelined vs control, batch 4096)", PURPLE, { bigSize: 28, labelSize: 11, bigH: 0.5 });
  card(s, 6.7, 3.7, 2.9, 1.0, `${Math.min(...vs).toFixed(2)}–${Math.max(...vs).toFixed(2)}×`, "pipelined vs CUDA pipeline, all 8 batch sizes", GREEN, { bigSize: 22, labelSize: 11, bigH: 0.45 });
  T(s, `Hybrid is faster than the best OpenMP only from batch ${num("Sp:hyb:crossover")} upward; at batch 1 and 8 OpenMP is faster.`, 0.45, 4.8, 9.1, 0.45, { fontSize: 13, bold: true });
}
// ---- 16 best by batch
{
  const cand = (i) => [["Serial", SER.serial[i]], ["OpenMP", SER.omp[i]], ["CUDA pipeline", SER.cuda[i]], ["Hybrid pipeline", SER.hyb[i]]].sort((a, b) => a[1] - b[1]);
  const s = addSlide("CONTENT", "Results", "The Best Implementation Depends on Batch Size", 1.25,
    `This table brings the results together. For every batch size it lists the fastest end-to-end implementation, its time, the runner-up and its time - all measured on the Spartan node.\n\nFor a batch of one image and a batch of eight, plain OpenMP on the multicore CPU is the fastest: the GPU path is dominated by launch, copy and synchronization overhead. From batch 32 upward the pipelined hybrid is fastest, by about a factor of two over the runner-up, because the GPU now gets enough work and the CPU preprocessing overlaps with GPU execution.\n\nNotice what never wins: the CUDA pipeline with single-threaded preprocessing is never the fastest end-to-end, even though its kernels are the fastest compute-only from batch 32 on. That is the whole message of the project: the choice depends on workload size and overhead, not on assuming that one platform is always fastest.\n\nOne honest caveat that is also in the paper: CUDA uses a fixed 16 by 16 block, while OpenMP and the hybrid use their best thread count - so this is not a best-versus-best comparison. The best CUDA block would change the CUDA time by at most ${num("Sp:cuda:blockgain:max")} percent.`,
    "Fastest / runner-up per batch size (end-to-end, Spartan).");
  const rows = [["Batch size", "Fastest implementation", "Time (ms)", "Runner-up", "Time (ms)"]].concat(B.map((b, i) => { const c = cand(i); return [b, c[0][0], c[0][1].toFixed(1), c[1][0], c[1][1].toFixed(1)]; }));
  table(s, rows, 0.45, 1.2, 6.3, [0.95, 1.9, 0.95, 1.6, 0.9], 13, { rowH: 0.36 });
  bullets(s, ["Batch 1–8: OpenMP — GPU overhead dominates", `Batch ≥ ${num("Sp:hyb:crossover")}: hybrid pipeline — enough GPU work, CPU/GPU overlap`, "CUDA pipeline with single-threaded preprocessing is never fastest end-to-end", "Fixed 16×16 CUDA block vs tuned OpenMP threads: not best-vs-best"], 6.95, 1.25, 2.65, 3.4, { fontSize: 13 });
  T(s, "End-to-end time per pass of 10,000 images, Spartan node (Tesla K40m, 24 threads).", 0.45, 4.95, 9.1, 0.3, { fontSize: 12, color: MUTED });
}
// ---- 17 Amdahl and limitations
{
  const thr = SER.scale_spartan["1"].map((x) => x.threads); const lab = thr.map(String);
  const fit = (f) => thr.map((p) => +(1 / (f + (1 - f) / p)).toFixed(3));
  const meas = (b) => SER.scale_spartan[b].map((x) => +x.speedup.toFixed(3));
  const f1v = SER.amdahl["1"].f, f4v = SER.amdahl["4096"].f;
  const s = addSlide("CONTENT", "Results", "Why Speedup Eventually Stops Increasing", 1.25,
    `RQ6: how do the results relate to Amdahl's law? The law says that if P is the parallel portion of the work, the speedup on N processors is one divided by one minus P plus P over N. The serial portion, one minus P, limits the speedup no matter how many threads you add.\n\nI fitted this to my OpenMP measurements. For batch 4096 on the Xeon the fitted serial fraction is only ${num("Sp:amdahl:f:4096")}, which would allow a ceiling of ${f1("Sp:amdahl:ceil:4096")} times - so the ${f1("Sp:omp:speedup:4096:24")} times I measured with 24 threads is not limited by the serial fraction. For a batch of one image the fitted serial fraction is ${num("Sp:amdahl:f:1")}, a ceiling of only ${f1("Sp:amdahl:ceil:1")} times. So the batch size changes the effective serial fraction.\n\nThe same logic explains the CUDA pipeline: its single-threaded preprocessing, copies and launches behave like a serial part, which is why the end-to-end speedup is smaller than the kernel speedup, and why the hybrid, which parallelizes and overlaps that part, helps.\n\nAnd the limitations, which I want to state clearly: the GPU is an old Tesla K40m; the network is small and fully connected; my kernels are not tuned; the cluster is shared; the comparison uses a fixed CUDA block against tuned OpenMP thread counts; and results may differ on modern GPUs.`,
    `S(N) = 1/((1−P)+P/N); Xeon f = ${num("Sp:amdahl:f:4096")} (batch 4096), ${num("Sp:amdahl:f:1")} (batch 1); limitations list.`);
  T(s, "S(N) = 1 / ( (1 − P) + P / N )", 0.45, 1.15, 5.4, 0.45, { fontSize: 20, bold: true, fontFace: "Consolas", color: NAVY });
  chart(s, "line", [{ name: `Measured, batch 4096`, values: meas("4096"), ci: SER.scale_spartan["4096"].map((x) => x.speedup_ci), color: "1E3A8A" }, { name: `Amdahl fit, f = ${f4v.toFixed(3)}`, values: fit(f4v), color: "1E3A8A", dash: "dash" }, { name: `Measured, batch 1`, values: meas("1"), ci: SER.scale_spartan["1"].map((x) => x.speedup_ci), color: ORANGE }, { name: `Amdahl fit, f = ${f1v.toFixed(3)}`, values: fit(f1v), color: ORANGE, dash: "dash" }, { name: "Ideal (f = 0)", values: thr, color: LGRAY, dash: "sysDash" }],
    lab, { x: 0.3, y: 1.65, w: 5.6, h: 3.6, title: "Speedup vs OpenMP threads, Xeon (Spartan)", valAxisTitle: "Speedup over serial (×)", catAxisTitle: "OpenMP threads", legendFontSize: 10, valAxisMinVal: 0 });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 6.1, y: 1.15, w: 3.5, h: 4.1, fill: { color: LIGHT }, line: { color: LIGHT }, rectRadius: 0.08 });
  T(s, "Limitations", 6.25, 1.22, 3.2, 0.3, { fontSize: 15, bold: true });
  bullets(s, ["Old GPU: Tesla K40m", "Small fully connected network", "Untuned kernels", "Shared cluster environment", "Fixed CUDA block vs tuned OpenMP threads", "Results may differ on modern GPUs", "The serial part is the 1−P in the formula; it limits any speedup"], 6.25, 1.6, 3.25, 3.6, { fontSize: 13 });
}
pres.addSection({ title: "Conclusions" });
// ---- 18 conclusions
{
  const s = addSlide("DARK", "Conclusions", "Conclusions and Future Work", 1.5,
    `Let me finish with four conclusions, all of them backed by measurements. One: OpenMP gives strong CPU speedup - ${f1("Sp:omp:speedup:4096:24")} times with 24 threads on the Xeon for large batches - until scaling limits appear: batch size 1, and on the Apple M4 the efficiency cores. Two: CUDA kernels can be very fast - ${f1("Sp:comp:gpuvsserial:4096")} times faster than serial compute-only - but the end-to-end pipeline is only ${f1("Sp:cuda:speedup:4096")} times, because it includes preprocessing and transfers. Three: hybrid execution reduces end-to-end time when CPU preprocessing overlaps with GPU computation - ${f1("Sp:hyb:best:e2e:4096")} milliseconds against ${f1("Sp:cuda:e2e:4096")} for the CUDA pipeline at batch 4096. Four: the best execution model depends on batch size: OpenMP for batches of 1 and 8, the hybrid from batch ${num("Sp:hyb:crossover")} up.\n\nFuture work: shared-memory-tiled CUDA kernels, a comparison with cuBLAS, GPU-side preprocessing, a newer GPU, larger networks, convolutional networks, and energy measurements.\n\nThe main result is that CPU, GPU and hybrid parallelism should be selected according to workload size and overhead - not by assuming that one platform is always fastest. Thank you. I am happy to take questions; I have backup slides for the full timing table, block sizes, compiler flags, cold start, variation, hardware limits, correctness details and kernel code.`,
    "Four conclusions; future work; final statement.");
  T(s, "Conclusions", 0.45, 1.2, 4.6, 0.35, { fontSize: 18, bold: true, color: "86EFAC", fontFace: "Cambria" });
  bullets(s, [`OpenMP: ${f1("Sp:omp:speedup:4096:24")}× on 24 Xeon threads for large batches, until scaling limits appear`, `CUDA kernels ${f1("Sp:comp:gpuvsserial:4096")}× vs serial (compute-only), but the end-to-end pipeline only ${f1("Sp:cuda:speedup:4096")}×`, `Hybrid: ${f1("Sp:hyb:best:e2e:4096")} ms vs ${f1("Sp:cuda:e2e:4096")} ms for the CUDA pipeline when CPU preprocessing overlaps GPU work`, "The best model depends on batch size and workload"], 0.45, 1.6, 4.6, 2.7, { fontSize: 14, color: "E5E7EB" });
  T(s, "Future work", 5.35, 1.2, 4.2, 0.35, { fontSize: 18, bold: true, color: "93C5FD", fontFace: "Cambria" });
  bullets(s, ["Shared-memory-tiled CUDA kernels", "cuBLAS comparison", "GPU-side preprocessing", "Newer GPU comparison", "Larger networks and convolutional networks", "Energy measurements"], 5.35, 1.6, 4.2, 2.7, { fontSize: 14, color: "E5E7EB" });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.45, y: 4.4, w: 9.1, h: 0.85, fill: { color: PURPLE }, line: { color: PURPLE }, rectRadius: 0.06 });
  T(s, "CPU, GPU, and hybrid parallelism should be selected according to workload size and overhead, not by assuming that one platform is always fastest.", 0.65, 4.4, 8.7, 0.85, { fontSize: 15, bold: true, color: "FFFFFF", valign: "middle" });
}

// =============================================== BACKUP SLIDES ===============================================
pres.addSection({ title: "Backup" });
const BK = (title, notes, text) => addSlide("CONTENT", "Backup", "Backup: " + title, 0, notes, text);
{
  const s = BK("Full end-to-end timing table (Spartan)", "Full table of end-to-end times per pass for every batch size. OpenMP and Hybrid show the best thread count in brackets. The GPU-kernels column is the compute-only kernel time. Speedups are over serial.", "Full timing table.");
  const rows = [["Batch", "Serial", "OpenMP (thr.)", "GPU kernels", "CUDA e2e", "Hybrid (thr.)", "Kernel ×", "CUDA ×", "Hybrid ×"]].concat(D.cpugpu.map((q) => [q.batch, q.serial.toFixed(1), `${q.omp.toFixed(1)} (${q.ompthr})`, q.kernel.toFixed(1), q.cuda.toFixed(1), `${q.hyb.toFixed(1)} (${q.hybthr})`, q.ks.toFixed(2), q.cs.toFixed(2), q.hs.toFixed(2)]));
  table(s, rows, 0.4, 1.2, 9.2, [0.65, 0.95, 1.4, 1.05, 1.0, 1.4, 0.9, 0.9, 0.95], 12);
  T(s, "ms per pass of 10,000 images; speedups (×) over serial. “CUDA” = single-threaded preprocessing, fixed 16×16 block. Kernel = compute-only.", 0.4, 4.5, 9.2, 0.5, { fontSize: 11, color: MUTED });
}
{
  const s = BK("Compute-only comparison (stages 1–3)", `Compute-only means just the hidden layer, output layer and argmax. At batch 4096 the GPU kernels take ${f1("Sp:comp:kernel:4096")} milliseconds against ${f1("Sp:comp:omp:4096")} for the best OpenMP configuration: ${f2("Sp:comp:gpuvsomp:4096")} times. If one divides OpenMP's end-to-end time, which includes preprocessing, by the kernel time, one gets about 2.49 - but that mixes a compute-only number with an end-to-end number, so I do not use it.`, "Compute-only table.");
  const rows = [["Batch", "Serial (ms)", "OpenMP (ms)", "GPU kernels (ms)", "Kernels vs serial (×)", "Kernels vs OpenMP (×)"]].concat(B.map((b) => [b, num(`Sp:comp:serial:${b}`), `${num(`Sp:comp:omp:${b}`)} (${num(`Sp:comp:ompthr:${b}`)})`, num(`Sp:comp:kernel:${b}`), num(`Sp:comp:gpuvsserial:${b}`), num(`Sp:comp:gpuvsomp:${b}`)]));
  table(s, rows, 0.4, 1.2, 9.2, [0.8, 1.5, 1.6, 1.7, 1.8, 1.8], 12);
  T(s, "Stages 1–3 only (no preprocessing, no copies). Like-for-like ratio at batch 4096: 2.44× (kernels vs OpenMP compute-only). The 2.49× figure would come from dividing OpenMP's end-to-end time by the kernel time, which mixes definitions.", 0.4, 4.45, 9.2, 0.8, { fontSize: 12, color: MUTED });
}
{
  const sc = SER.scale_mac; const thr = sc["1"].map((x) => String(x.threads)); const cols = { "1": "93C5FD", "256": BLUE, "4096": "1E3A8A" };
  const mk = (key, ci) => ["1", "256", "4096"].map((b) => ({ name: `Batch ${b}`, values: sc[b].map((x) => +x[key].toFixed(4)), ci: ci ? sc[b].map((x) => +x[ci].toFixed(4)) : null, color: cols[b] }));
  const s = BK("OpenMP on the Apple M4 (separate platform)", `The Apple M4 has 10 cores: 4 performance and 6 efficiency. The speedup follows the ideal line up to 4 threads - ${f2("Mac:omp:speedup:4096:4")} times at batch 4096 - then flattens at ${f2("Mac:omp:speedup:4096:10")} times with 10 threads. With one image per batch OpenMP is slower than serial: ${f2("Mac:omp:speedup:1:10")} times with 10 threads. These results are never compared with the Spartan GPU results.`, "M4 OpenMP charts.");
  const y = 1.15, w = 3.05, h = 3.3;
  chart(s, "line", mk("time", "time_ci"), thr, { x: 0.3, y, w, h, title: "Time per pass (Apple M4)", valAxisTitle: "Time (ms, log scale)", catAxisTitle: "OpenMP threads", valAxisLogScaleBase: 10, valAxisMinVal: 10, valAxisMaxVal: 10000, legendFontSize: 10, catAxisLabelFontSize: 10, valAxisLabelFontSize: 10 });
  chart(s, "line", mk("speedup", "speedup_ci").concat([{ name: "Ideal", values: sc["1"].map((x) => x.threads), color: LGRAY, dash: "dash" }]), thr, { x: 3.4, y, w, h, title: "Speedup over serial (Apple M4)", valAxisTitle: "Speedup (×)", catAxisTitle: "OpenMP threads", legendFontSize: 10, catAxisLabelFontSize: 10, valAxisLabelFontSize: 10, valAxisMinVal: 0 });
  chart(s, "line", mk("eff", "eff_ci"), thr, { x: 6.5, y, w, h, title: "Efficiency (Apple M4)", valAxisTitle: "Efficiency (speedup / threads)", catAxisTitle: "OpenMP threads", legendFontSize: 10, catAxisLabelFontSize: 10, valAxisLabelFontSize: 10, valAxisMinVal: 0, valAxisMaxVal: 1.1 });
  T(s, "Apple M4: 10 cores (4 performance + 6 efficiency). Separate CPU platform — never mixed with the Spartan CPU-vs-GPU comparison.", 0.4, 4.6, 9.2, 0.5, { fontSize: 12, color: MUTED });
}
{
  const lab = B.map(String); const bl = SER.blocks;
  const s = BK("CUDA block-size comparison", `Block size only matters at small batches. At batch 64 the kernels take ${f1("Sp:cuda:blk8:kernel:64")} ms with 8 by 8 blocks, ${f1("Sp:cuda:blk16:kernel:64")} with 16 by 16 and ${f1("Sp:cuda:blk32:kernel:64")} with 32 by 32. At batch 4096 all three are within one percent. If the best of the three block sizes were used, the CUDA end-to-end time would improve by at most ${num("Sp:cuda:blockgain:max")} percent, so the main comparison, which uses a fixed 16 by 16 block, is not best-versus-best, and is labelled that way.`, "Block-size chart.");
  chart(s, "line", [{ name: "8×8 (64 threads)", values: bl["8"].kernel.map((v) => +v.toFixed(3)), ci: bl["8"].kernel_ci, color: "86EFAC" }, { name: "16×16 (256 threads)", values: bl["16"].kernel.map((v) => +v.toFixed(3)), ci: bl["16"].kernel_ci, color: GREEN }, { name: "32×32 (1,024 threads)", values: bl["32"].kernel.map((v) => +v.toFixed(3)), ci: bl["32"].kernel_ci, color: "14532D" }],
    lab, { x: 0.3, y: 1.15, w: 6.0, h: 3.9, title: "CUDA kernel time by block size (Spartan)", valAxisTitle: "Kernel time per pass (ms, log scale)", catAxisTitle: "Batch size (images per batch)", valAxisLogScaleBase: 10, valAxisMinVal: 10, valAxisMaxVal: 10000 });
  bullets(s, [`Batch 64: ${f1("Sp:cuda:blk8:kernel:64")} / ${f1("Sp:cuda:blk16:kernel:64")} / ${f1("Sp:cuda:blk32:kernel:64")} ms (8×8 / 16×16 / 32×32)`, "Batch 4096: all within 1 %", `Best block improves CUDA end-to-end by ≤ ${num("Sp:cuda:blockgain:max")} %`, "Main comparison: fixed 16×16 block vs tuned OpenMP threads"], 6.5, 1.3, 3.1, 3.4, { fontSize: 13 });
}
{
  const s = BK("Compiler settings and flag sensitivity", "Compiler settings of the three builds. On Spartan one binary is built with g++ 11.4.1 through nvcc 11.7; the reference build adds -march=native, the sensitivity build does not. The Mac uses Apple clang with no architecture flag. There is no fast-math, and the floating-point contraction options were not set, so each compiler's default applies. Plain -O3 changes the serial time by about five percent.", "Compiler table.");
  table(s, [["Build", "Compiler", "Flags"], ["Apple M4", "Apple clang 21.0.0, libomp 23.1.2", "-O3 -std=c++14 -fopenmp; no -march"], ["Spartan reference", "g++ 11.4.1 via nvcc 11.7.99", "host -O3 -fopenmp -march=native; device -O3 -arch=sm_35"], ["Spartan sensitivity", "same", "same without -march=native"]], 0.4, 1.2, 9.2, [1.8, 3.1, 4.3], 12);
  const rows = [["Implementation (ms per pass)", "native, batch 256", "-O3, batch 256", "native, batch 4096", "-O3, batch 4096"]].concat(D.flags.map((q) => [q.impl, q.native256.toFixed(1), q.o3256.toFixed(1), q.native4096.toFixed(1), q.o34096.toFixed(1)]));
  table(s, rows, 0.4, 2.85, 9.2, [3.2, 1.5, 1.5, 1.5, 1.5], 12);
  T(s, "No -ffast-math; -ffp-contract and --fmad were not set (compiler defaults).", 0.4, 4.75, 9, 0.3, { fontSize: 11, color: MUTED });
}
{
  const s = BK("Cold-start timing", `One-time costs excluded from the steady-state times, measured in ten fresh processes: CUDA context creation ${f1("Sp:cold:init:mean")} ms on average, weight upload ${f2("Sp:cold:upload:mean")} ms, buffer allocation ${f2("Sp:cold:alloc:mean")} ms - ${f1("Sp:cold:ctor:mean")} ms in total, about ${f2("Sp:cold:ctorvspass")} times a steady-state CUDA pass. After the set-up the first CUDA pass shows no penalty; the first 24-thread OpenMP pass is ${f1("Sp:cold:omp:firstpenalty")} percent slower than the second.`, "Cold-start table.");
  const q = (l, k) => [l, num(`Sp:cold:${k}:mean`), num(`Sp:cold:${k}:median`), num(`Sp:cold:${k}:std`), num(`Sp:cold:${k}:min`), num(`Sp:cold:${k}:max`)];
  table(s, [["Quantity (ms)", "Mean", "Median", "Std. dev.", "Min", "Max"], q("CUDA context creation", "init"), q("Weight upload", "upload"), q("Buffer/stream/event allocation", "alloc"), q("Total one-time GPU set-up", "ctor"), q("CUDA pass, 1st", "cuda1"), q("CUDA pass, 3rd", "cuda3"), q("Hybrid pass, 1st", "hyb1"), q("Hybrid pass, 2nd", "hyb2"), q("OpenMP 24 threads, 1st", "omp1"), q("OpenMP 24 threads, 2nd", "omp2")], 0.4, 1.2, 9.2, [3.2, 1.2, 1.2, 1.2, 1.2, 1.2], 12);
  T(s, "10 fresh processes, batch 256, 24 OpenMP threads, Spartan node.", 0.4, 4.85, 9, 0.3, { fontSize: 11, color: MUTED });
}
{
  const s = BK("Run-to-run variation", `Variation is small: the median coefficient of variation is ${f1("Sp:cv:median")} percent on Spartan. The largest is the ${num("Sp:slow:impl")} configuration at batch ${num("Sp:slow:batch")} with ${num("Sp:slow:threads")} threads: mean ${f2("Sp:slow:mean")} ms, median ${f2("Sp:slow:median")}, standard deviation ${f2("Sp:slow:std")}, minimum ${f2("Sp:slow:min")}, maximum ${f2("Sp:slow:max")}. One pass is above 1.5 times the median. I did not remove it; it is in all statistics and in the raw data.`, "Variation table.");
  table(s, [["Configuration (ms)", "n", "Mean", "Median", "Std. dev.", "Min", "Max"], [`Spartan: ${num("Sp:slow:impl")}, batch ${num("Sp:slow:batch")}, ${num("Sp:slow:threads")} threads`, num("Sp:slow:n"), num("Sp:slow:mean"), num("Sp:slow:median"), num("Sp:slow:std"), num("Sp:slow:min"), num("Sp:slow:max")], [`Apple M4: ${num("Mac:slow:impl")}, batch ${num("Mac:slow:batch")}`, num("Mac:slow:n"), num("Mac:slow:mean"), num("Mac:slow:median"), num("Mac:slow:std"), num("Mac:slow:min"), num("Mac:slow:max")]], 0.4, 1.4, 9.2, [3.9, 0.5, 0.9, 0.9, 1.1, 0.9, 1.0], 12);
  bullets(s, [`Median coefficient of variation: ${f1("Sp:cv:median")} % (Spartan), ${f1("Mac:cv:median")} % (M4)`, "One pass above 1.5× median in the Spartan case; the run is kept", "20 passes run back to back: not independent samples of machine state"], 0.5, 3.0, 9.0, 1.8, { fontSize: 14 });
}
{
  const s = BK("Measured hardware limits (Spartan)", "Micro-benchmark results used in the analysis: PCIe bandwidth, device memory copy rate, kernel launch cost, CPU memory bandwidth and OpenMP fork-join cost. No hardware peak numbers are assumed; everything here was measured.", "Micro-benchmarks.");
  table(s, [["Quantity (Spartan node)", "Measured value"]].concat(D.micro), 0.5, 1.3, 9.0, [5.6, 3.4], 14);
}
{
  const V = SER.validation;
  const s = BK("Detailed correctness results (Spartan, reference build)", `Detailed correctness table for the reference build: number of passing comparisons, maximum and mean logit difference, minimum prediction agreement and accuracy for each comparison group. In the plain -O3 sensitivity build the largest CUDA difference is ${num("SpO3:val:cuda:maxerr")}.`, "Detailed correctness.");
  const sci = (x) => { if (x === 0) return "0"; const [m, e] = x.toExponential(2).split("e"); return `${m}e${parseInt(e)}`; };
  table(s, [["Comparison", "Passed", "Max |Δlogit|", "Mean |Δlogit|", "Min agreement", "Accuracy"]].concat(V.map((v) => [v.group.replace("Serial float32 vs NumPy float64", "Serial vs NumPy float64 (100 images)"), `${v.passed} / ${v.n}`, sci(v.maxerr), sci(v.meanerr), v.agree.toFixed(2) + " %", v.group.indexOf("NumPy") >= 0 ? "—" : v.acc.toFixed(2) + " %"])), 0.4, 1.2, 9.2, [3.6, 1.0, 1.3, 1.3, 1.1, 0.9], 12);
  T(s, `Tolerance: max |Δlogit| ≤ 1×10⁻⁴ and agreement ≥ 99.9 %, fixed before measuring. Plain -O3 sensitivity build: largest CUDA difference ${num("SpO3:val:cuda:maxerr")}.`, 0.4, 4.4, 9.2, 0.6, { fontSize: 12, color: MUTED });
}
{
  const s = BK("Kernel and OpenMP code details", "Two short excerpts from the source code. The hidden-layer kernel: each thread computes one output element, with the hidden unit index varying fastest so that consecutive threads read consecutive weight addresses. The OpenMP region: one parallel region covers the whole pass, each stage is a work-shared loop, and the implicit barrier after each loop is required because the next stage reads data written by other threads.", "Code excerpts.");
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.4, y: 1.2, w: 4.55, h: 3.6, fill: { color: "111827" }, line: { color: "111827" }, rectRadius: 0.06 });
  T(s, "__global__ void layer1_kernel(\n    const float* x, const float* w1,\n    const float* b1, float* h, int B) {\n  int j = blockIdx.x*blockDim.x + threadIdx.x;\n  int b = blockIdx.y*blockDim.y + threadIdx.y;\n  if (b >= B || j >= 256) return;\n  float acc = b1[j];\n  for (int k = 0; k < 784; ++k)\n    acc += x[b*784+k] * w1[k*256+j];\n  h[b*256+j] = acc > 0.f ? acc : 0.f;\n}", 0.55, 1.3, 4.3, 3.4, { fontFace: "Consolas", fontSize: 10.5, color: "E5E7EB" });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 5.1, y: 1.2, w: 4.5, h: 3.6, fill: { color: "111827" }, line: { color: "111827" }, rectRadius: 0.06 });
  T(s, "#pragma omp parallel num_threads(T)\nfor (int s = 0; s < n; s += batch) {\n  #pragma omp for schedule(static)\n  for (b...) preprocess(b);\n  #pragma omp for collapse(2)\n  for (b...) for (jb...) hidden(b, jb);\n  #pragma omp for collapse(2)\n  for (b...) for (c...) output(b, c);\n  #pragma omp for\n  for (b...) argmax(b);\n}", 5.25, 1.3, 4.3, 3.4, { fontFace: "Consolas", fontSize: 10.5, color: "E5E7EB" });
}

// ---------- write files ----------
(async () => {
  const out = path.join(__dirname, "CS259_Hybrid_CPU_GPU_Induru.pptx");
  await pres.writeFile({ fileName: out });
  await applyTheme(out, THEME);
  fs.writeFileSync(path.join(__dirname, "errbars.json"), JSON.stringify(ERR));
  const main = LOG.filter((l) => l.section !== "Backup");
  const words = main.reduce((a, l) => a + l.notes.split(/\s+/).length, 0);
  const md = LOG.map((l) => `## ${l.section === "Backup" ? "Backup" : "Slide"} ${l.n}: ${l.title}\n\n**Estimated speaking time:** ${l.minutes} min\n\n**On the slide:** ${l.text}\n\n**What to say:**\n\n${l.notes}\n`).join("\n");
  fs.writeFileSync(path.join(__dirname, "speaker_notes.md"), `# Speaker notes — 18 main slides (about ${main.reduce((a, l) => a + l.minutes, 0)} minutes) + backup slides\n\n${md}`);
  fs.writeFileSync(path.join(__dirname, "slide_content.md"), "# Slide content\n\n" + LOG.map((l) => `${l.n}. [${l.section}] **${l.title}** — ${l.text}`).join("\n") + "\n");
  console.log(`wrote ${out}: ${main.length} main slides, ${LOG.length - main.length} backup slides; main-slide minutes ${main.reduce((a, l) => a + l.minutes, 0)}; notes words ${words} (~${(words / 140).toFixed(1)} min at 140 wpm)`);
})();
