// build_deck.js - builds the 20-minute CS 259 presentation from the measured results.
// Every number on the slides comes from presentation/slide_data.json (exported from results/raw by export_slide_data.py).
const pptxgen = require("pptxgenjs");
const fs = require("fs");
const path = require("path");
// apply_theme.js (theme writer of the pptx tooling) is found through PPTX_SKILL_DIR = the directory that contains scripts/apply_theme.js
const SKILL = process.env.PPTX_SKILL_DIR || "";
const { applyTheme } = require(path.join(SKILL, "scripts/apply_theme.js"));

const D = JSON.parse(fs.readFileSync(path.join(__dirname, "slide_data.json"), "utf8"));
const num = (k) => { if (!(k in D.num)) throw new Error("missing value " + k); return D.num[k]; };
const val = (k) => parseFloat(num(k).replace(/,/g, ""));
const f1 = (k) => val(k).toFixed(1);
const f2 = (k) => val(k).toFixed(2);
const FIG = (n) => path.join(__dirname, "..", "results", "figures", "slides", n + ".png");
const pngSize = (f) => { const b = fs.readFileSync(f); return [b.readUInt32BE(16), b.readUInt32BE(20)]; };

// ---------- theme (same colours as the figures) ----------
const THEME = {
  name: "CS259 Hybrid", headFontFace: "Cambria", bodyFontFace: "Calibri",
  colors: { dk1: "1F2937", lt1: "FFFFFF", dk2: "0F172A", lt2: "F3F4F6", accent1: "2563EB", accent2: "16A34A", accent3: "7C3AED",
            accent4: "C2570C", accent5: "4B5563", accent6: "F0A36B", hlink: "2563EB", folHlink: "7C3AED" },
};
const NAVY = "0F172A", INK = "1F2937", MUTED = "4B5563", LIGHT = "F3F4F6", BLUE = "2563EB", GREEN = "16A34A", PURPLE = "7C3AED", ORANGE = "C2570C", GRAY = "4B5563";

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9"; // 10 x 5.625 in
pres.author = "Sunnihith Reddy Induru";
pres.title = "Performance Evaluation of Hybrid CPU-GPU Parallelism for Deep Learning Using OpenMP and CUDA";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };

pres.defineSlideMaster({
  title: "TITLE", background: { color: NAVY },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 1.2, w: 8.8, h: 1.9, fontFace: "Cambria", fontSize: 32, bold: true, color: "FFFFFF", valign: "middle", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.6, y: 3.3, w: 8.8, h: 1.3, fontFace: "Calibri", fontSize: 18, color: "CBD5E1", valign: "top", margin: 0 }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "CONTENT", background: { color: "FFFFFF" },
  objects: [{ placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.25, w: 9.0, h: 0.85, fontFace: "Cambria", fontSize: 26, bold: true, color: NAVY, valign: "middle", margin: 0 }, text: "" } }],
  slideNumber: { x: 9.1, y: 5.25, w: 0.5, h: 0.25, fontFace: "Calibri", fontSize: 10, color: "6B7280", align: "right" },
});
pres.defineSlideMaster({
  title: "DARK", background: { color: NAVY },
  objects: [{ placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.25, w: 9.0, h: 0.85, fontFace: "Cambria", fontSize: 26, bold: true, color: "FFFFFF", valign: "middle", margin: 0 }, text: "" } }],
  slideNumber: { x: 9.1, y: 5.25, w: 0.5, h: 0.25, fontFace: "Calibri", fontSize: 10, color: "9CA3AF", align: "right" },
});

// ---------- helpers ----------
const LOG = []; // for slide_content.md / speaker_notes.md
function addSlide(master, section, title, minutes, notes, textForMd) {
  const s = pres.addSlide({ masterName: master, sectionTitle: section });
  s.addText(title, { placeholder: "title" });
  s.addNotes(`[${minutes} min]\n${notes}`);
  LOG.push({ n: LOG.length + 1, title, minutes, notes, text: textForMd || "" });
  return s;
}
function card(s, x, y, w, h, big, label, color, o = {}) {
  const bs = o.bigSize || 40, ls = o.labelSize || 14, bh = o.bigH || h * 0.5;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: LIGHT }, line: { color: LIGHT }, rectRadius: 0.08 });
  s.addText(big, { x, y: y + 0.08, w, h: bh, align: "center", valign: "middle", fontFace: "Cambria", fontSize: bs, bold: true, color, margin: 0, isTextBox: true });
  s.addText(label, { x: x + 0.1, y: y + 0.08 + bh, w: w - 0.2, h: h - bh - 0.14, align: "center", valign: "top", fontFace: "Calibri", fontSize: ls, color: INK, margin: 0, isTextBox: true });
}
function bullets(s, items, x, y, w, h, opts = {}) {
  const runs = items.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < items.length - 1, paraSpaceAfter: 6 } }));
  s.addText(runs, Object.assign({ x, y, w, h, fontFace: "Calibri", fontSize: 15, color: INK, valign: "top", margin: 0, isTextBox: true }, opts));
}
function image(s, name, x, y, maxW, maxH, alt) {
  const [pw, ph] = pngSize(FIG(name));
  const r = Math.min(maxW / pw, maxH / ph);
  const w = pw * r, h = ph * r;
  s.addImage({ path: FIG(name), x: x + (maxW - w) / 2, y, w, h, altText: alt });
  return h;
}
function table(s, rows, x, y, w, colW, fontSize = 12, headFill = NAVY) {
  const data = rows.map((r, i) => r.map((c) => ({ text: String(c), options: { bold: i === 0, color: i === 0 ? "FFFFFF" : INK, fill: { color: i === 0 ? headFill : (i % 2 ? "FFFFFF" : LIGHT) }, fontFace: "Calibri", fontSize, valign: "middle", margin: [0.03, 0.06, 0.03, 0.06] } })));
  s.addTable(data, { x, y, w, colW, border: { type: "solid", pt: 0.5, color: "D1D5DB" }, rowH: 0.3 });
}
const CUDA = "CUDA (1-thread preprocessing)";

// ============================ SLIDES ============================
pres.addSection({ title: "Introduction" });
// 1 title
{
  const s = pres.addSlide({ masterName: "TITLE", sectionTitle: "Introduction" });
  s.addText("Performance Evaluation of Hybrid CPU-GPU Parallelism for Deep Learning Using OpenMP and CUDA", { placeholder: "title" });
  s.addText("Sunnihith Reddy Induru\nCS 259 – Advanced Parallel Processing · San Jose State University", { placeholder: "body" });
  const notes = "Greet the audience. One sentence: I compared four ways of running the same neural-network inference – serial, OpenMP on the CPU, CUDA on the GPU, and a hybrid that uses both – and measured when each one wins. Everything I show was measured by me and is in the paper.";
  s.addNotes("[0.5 min]\n" + notes);
  LOG.push({ n: 1, title: "Title", minutes: 0.5, notes, text: "Performance Evaluation of Hybrid CPU-GPU Parallelism for Deep Learning Using OpenMP and CUDA — Sunnihith Reddy Induru, CS 259, SJSU" });
}
// 2 motivation
{
  const s = addSlide("CONTENT", "Introduction", "A fast GPU kernel is not a fast application", 1.25,
    `Start with the punchline. At batch size 4096 the GPU kernels alone are ${f1("Sp:comp:gpuvsserial:4096")} times faster than serial code. But the pipeline an application actually runs - preprocessing, copies, kernels - is only ${f1("Sp:cuda:speedup:4096")} times faster. And with one image per batch the same GPU pipeline is ${f2("Sp:cuda:speedup:1")} times: slower than serial. Same GPU, same data. The rest of the talk explains why, and what to do about it. All numbers: Tesla K40m node, mean of 20 runs.`,
    `Kernels only ${f1("Sp:comp:gpuvsserial:4096")}× | end-to-end ${f1("Sp:cuda:speedup:4096")}× | batch 1 ${f2("Sp:cuda:speedup:1")}×`);
  card(s, 0.5, 1.35, 2.85, 2.35, `${f1("Sp:comp:gpuvsserial:4096")}×`, "GPU kernels only (compute-only) vs serial, batch 4096", GREEN);
  card(s, 3.575, 1.35, 2.85, 2.35, `${f1("Sp:cuda:speedup:4096")}×`, `End-to-end ${CUDA} vs serial, same run`, ORANGE);
  card(s, 6.65, 1.35, 2.85, 2.35, `${f2("Sp:cuda:speedup:1")}×`, "End-to-end at batch 1: slower than serial", GRAY);
  s.addText("Same GPU, same program, same data. The gap is single-threaded preprocessing, copies and launch overhead.", { x: 0.5, y: 3.95, w: 9, h: 0.5, fontFace: "Calibri", fontSize: 18, color: INK, margin: 0, isTextBox: true });
  s.addText("Measured on a Spartan node: Tesla K40m, 2× Xeon E5-2680 v4; 10,000 MNIST images; mean of 20 passes.", { x: 0.5, y: 4.85, w: 8.5, h: 0.3, fontFace: "Calibri", fontSize: 11, color: MUTED, margin: 0, isTextBox: true });
}
// 3 research questions
{
  const rq = [["RQ1", "How much speedup does OpenMP give over serial?", BLUE], ["RQ2", "How does CUDA compare with serial and OpenMP – compute-only and end-to-end?", GREEN],
    ["RQ3", "How does the batch size change CPU and GPU performance?", GRAY], ["RQ4", "How much GPU time is data transfer, not computation?", ORANGE],
    ["RQ5", "Does a hybrid OpenMP–CUDA pipeline improve end-to-end time?", PURPLE], ["RQ6", "How do results relate to Amdahl's law, overhead and bandwidth?", INK]];
  const s = addSlide("CONTENT", "Introduction", "Six questions about CPU, GPU and hybrid execution", 1.0,
    "Read the six questions briefly. RQ1-RQ3 are about scaling and batch size, RQ4 about transfers, RQ5 is the hybrid, RQ6 connects to theory. I will show the answer to each with measured numbers.",
    rq.map((r) => r[0] + ": " + r[1]).join("\n"));
  rq.forEach((r, i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = 0.5 + col * 4.6, y = 1.35 + row * 1.25;
    s.addShape(pres.shapes.OVAL, { x, y, w: 0.7, h: 0.7, fill: { color: r[2] }, line: { color: r[2] } });
    s.addText(r[0], { x, y, w: 0.7, h: 0.7, align: "center", valign: "middle", fontFace: "Calibri", fontSize: 14, bold: true, color: "FFFFFF", margin: 0, isTextBox: true });
    s.addText(r[1], { x: x + 0.85, y: y - 0.05, w: 3.55, h: 0.8, fontFace: "Calibri", fontSize: 15, color: INK, valign: "middle", margin: 0, isTextBox: true });
  });
}
// 4 background
{
  const s = addSlide("CONTENT", "Introduction", "Two kinds of parallelism, two kinds of overhead", 1.0,
    "OpenMP: a team of CPU threads sharing memory; every parallel loop ends in a barrier, so the work per loop must be larger than the synchronisation cost. CUDA: thousands of GPU threads, but separate memory - data must cross PCIe, and each kernel launch has a fixed cost. The hybrid idea: let the CPU prepare the next batch while the GPU computes the current one.",
    "OpenMP: shared memory, fork-join, barrier per loop. CUDA: thousands of threads, separate memory, PCIe copies, launch cost. Hybrid: overlap CPU and GPU work.");
  [["OpenMP on the CPU", BLUE, ["Threads share memory", "Each parallel loop ends in a barrier", "Overhead: synchronisation, vs work per batch"]],
   ["CUDA on the GPU", GREEN, ["Thousands of threads, separate memory", "Inputs and results cross PCIe", "Overhead: copies and kernel launches"]]].forEach((c, i) => {
    const x = 0.5 + i * 4.6;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.35, w: 4.4, h: 2.55, fill: { color: LIGHT }, line: { color: LIGHT }, rectRadius: 0.08 });
    s.addText(c[0], { x: x + 0.25, y: 1.5, w: 3.9, h: 0.45, fontFace: "Cambria", fontSize: 20, bold: true, color: c[1], margin: 0, isTextBox: true });
    bullets(s, c[2], x + 0.25, 2.1, 3.9, 1.7, { fontSize: 15 });
  });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.5, y: 4.15, w: 9.0, h: 0.8, fill: { color: PURPLE }, line: { color: PURPLE }, rectRadius: 0.08 });
  s.addText("Hybrid: OpenMP threads prepare batch i+1 while the GPU copies and computes batch i", { x: 0.7, y: 4.15, w: 8.6, h: 0.8, fontFace: "Calibri", fontSize: 17, bold: true, color: "FFFFFF", valign: "middle", margin: 0, isTextBox: true });
}
pres.addSection({ title: "Method" });
// 5 workload
{
  const s = addSlide("CONTENT", "Method", "Workload: MNIST digits through a 784→256→10 network", 1.0,
    "The workload is deliberately small and fully specified. Ten thousand MNIST test images, a fully connected network 784 to 256 with ReLU to 10, float32. 203,530 parameters; I trained the weights once with NumPy and every implementation loads the same file. Each pass has four stages: preprocessing - per-image standardisation, the hidden layer, the output layer, and argmax. I process the images in batches of 1 to 4096.",
    "10,000 MNIST test images | 784→256→ReLU→10, float32 | 203,530 parameters | batches 1–4096 | stages: preprocess, hidden, output, argmax");
  const h = image(s, "network_architecture", 0.5, 1.2, 9.0, 2.0, "Network architecture figure");
  card(s, 0.5, 3.55, 2.85, 1.5, "10,000", "MNIST test images per pass", BLUE);
  card(s, 3.575, 3.55, 2.85, 1.5, "203,530", "float32 parameters (97.97 % accuracy)", GREEN);
  card(s, 6.65, 3.55, 2.85, 1.5, "1 – 4096", "images per batch", PURPLE);
}
// 6 architecture
{
  const s = addSlide("CONTENT", "Method", "Four implementations of the same computation", 1.5,
    "Four primary implementations. Serial: one CPU thread. OpenMP: the CPU stages run on T threads. CUDA: preprocessing on ONE CPU thread, then copies, three GPU kernels, copy back - note this is not GPU-only because the preprocessing is on the CPU, so I call it CUDA with single-threaded preprocessing. Hybrid: OpenMP threads preprocess into pinned memory, copies are asynchronous, kernels run on streams. I also measured one diagnostic control, hybrid-sequential, to separate parallel preprocessing from overlapping. All use the same operations, data, weights, precision and source-level reduction order.",
    "Serial | OpenMP | CUDA (1-thread preprocessing) | Hybrid pipeline. Hybrid-sequential = diagnostic control only.");
  image(s, "architecture", 0.8, 1.2, 8.4, 3.5, "Execution architecture of the four implementations");
  s.addText("Diagnostic control (not a fifth implementation): hybrid-sequential = OpenMP preprocessing without overlap.", { x: 0.5, y: 4.8, w: 9, h: 0.3, fontFace: "Calibri", fontSize: 12, color: MUTED, margin: 0, isTextBox: true });
}
// 7 hybrid timeline schematic
{
  const s = addSlide("CONTENT", "Method", "Streams overlap different batches, never the layers of one batch", 1.5,
    "This is a schematic, not measured data. Top: the CUDA pipeline does preprocessing, copy, kernels, copy back for batch 1, and only then starts batch 2 - the GPU waits during preprocessing. Bottom: the hybrid preprocesses batch 2 on the CPU while the GPU is still working on batch 1. Important: the hidden layer, output layer and argmax of ONE batch depend on each other, so they run in order on one stream. The overlap is only between different batches, using three streams and pinned buffers.",
    "Schematic: sequential vs pipelined. Overlap between batches only; layers of one batch stay in order on one stream.");
  const X0 = 1.9, U = 1.15; // unit width
  const seg = (x, y, w, c, t) => { s.addShape(pres.shapes.RECTANGLE, { x, y, w, h: 0.4, fill: { color: c }, line: { color: "FFFFFF", width: 1 } }); s.addText(t, { x, y, w, h: 0.4, align: "center", valign: "middle", fontFace: "Calibri", fontSize: 10, bold: true, color: "FFFFFF", margin: 0, isTextBox: true }); };
  s.addText(`${CUDA}\n(sequential)`, { x: 0.5, y: 1.35, w: 1.4, h: 0.6, fontFace: "Calibri", fontSize: 12, bold: true, color: INK, margin: 0, isTextBox: true });
  for (let i = 0; i < 3; i++) { const b = X0 + i * 2.4 * 0.95 * 1.0; const k = 0.95; const x = X0 + i * 2.4 * k;
    seg(x, 1.4, 0.7 * k, GRAY, "pre"); seg(x + 0.7 * k, 1.4, 0.35 * k, ORANGE, "H2D"); seg(x + 1.05 * k, 1.4, 1.0 * k, GREEN, `kernels b${i + 1}`); seg(x + 2.05 * k, 1.4, 0.35 * k, ORANGE, "D2H"); }
  s.addText("Hybrid\n(pipelined)", { x: 0.5, y: 2.55, w: 1.4, h: 0.6, fontFace: "Calibri", fontSize: 12, bold: true, color: PURPLE, margin: 0, isTextBox: true });
  s.addText("CPU", { x: 1.4, y: 2.62, w: 0.5, h: 0.3, fontFace: "Calibri", fontSize: 11, color: MUTED, margin: 0, isTextBox: true });
  s.addText("GPU", { x: 1.4, y: 3.12, w: 0.5, h: 0.3, fontFace: "Calibri", fontSize: 11, color: MUTED, margin: 0, isTextBox: true });
  const P = 1.7 * 0.95; // pipeline period
  for (let i = 0; i < 3; i++) { const x = X0 + i * P; seg(x, 2.6, 0.7 * 0.95, BLUE, `pre b${i + 1}`);
    const g = X0 + 0.7 * 0.95 + i * P; seg(g, 3.1, 0.35 * 0.95, ORANGE, "H2D"); seg(g + 0.35 * 0.95, 3.1, 1.0 * 0.95, GREEN, `kernels b${i + 1}`); seg(g + 1.35 * 0.95, 3.1, 0.35 * 0.95, ORANGE, "D2H"); }
  s.addText("Schematic, not to scale. Overlap exists only between different batches.", { x: 0.5, y: 3.75, w: 9, h: 0.3, fontFace: "Calibri", fontSize: 12, italic: true, color: MUTED, margin: 0, isTextBox: true });
  bullets(s, ["3 CUDA streams, pinned host buffers, asynchronous copies", "A slot is reused only after its previous batch finished (CUDA event)", "Layers of one batch run in order on one stream"], 0.5, 4.1, 9.0, 1.1, { fontSize: 15 });
}
// 8 setup
{
  const s = addSlide("CONTENT", "Method", "Setup: one GPU node, steady-state timing, 20 passes", 1.0,
    "The reference platform is a Spartan GPU node: two Xeon E5-2680 v4 CPUs - lscpu reports 2 sockets times 14 cores times 1 thread, so 28 physical cores and 28 logical CPUs; my job was allocated 24 - and a Tesla K40m with CUDA 11.7. The CPU-versus-GPU comparison uses only this node. The Mac M4 is used for the OpenMP study only and never mixed with GPU numbers. Each configuration: 3 warm-up passes and 20 recorded passes. All times are steady-state: GPU initialisation, allocation and weight upload are excluded - I measured them separately, 110.7 ms in total. Compile flags are in the paper.",
    "Spartan node: 2× Xeon E5-2680 v4 (28 cores / 28 logical, 24 allocated), Tesla K40m, CUDA 11.7. Mac M4 (10/10) CPU only. 3 warm-up + 20 passes. Steady state.");
  table(s, [["", "Spartan GPU node", "Apple M4 (CPU only)"], ["CPU", "2× Xeon E5-2680 v4", "Apple M4"], ["Cores / logical CPUs", "28 / 28 (lscpu); 24 allocated", "10 / 10 (4 perf. + 6 eff.)"], ["GPU / CUDA", "Tesla K40m / CUDA 11.7", "none"], ["Compiler", "g++ 11.4.1 -O3 -march=native; nvcc 11.7", "Apple clang 21.0.0 -O3"]], 0.5, 1.3, 5.6, [1.35, 2.35, 1.9], 12);
  bullets(s, ["3 warm-up + 20 recorded passes", "Steady state: GPU initialisation excluded (measured separately: " + f1("Sp:cold:ctor:mean") + " ms)", "CUDA events + wall clock; same node for CPU vs GPU", "Mac results never mixed with GPU numbers"], 6.35, 1.3, 3.2, 3.2, { fontSize: 14 });
  s.addText("Spartan: 2 sockets × 14 cores × 1 thread per core (lscpu); jobs were allocated 24 CPUs.", { x: 0.5, y: 4.2, w: 5.6, h: 0.5, fontFace: "Calibri", fontSize: 12, color: MUTED, margin: 0, isTextBox: true });
}
pres.addSection({ title: "Results" });
// 9 correctness
{
  const s = addSlide("CONTENT", "Results", "All implementations produce the same predictions", 1.0,
    `Before timing anything I verified correctness. Every implementation is compared with the serial reference on all 10,000 images: eighty comparisons per build over batch sizes, thread counts, block sizes and stream counts, all within the tolerance I fixed in advance. OpenMP is bit-identical to serial. CUDA and hybrid differ by at most ${num("Sp:val:cuda:maxerr")} in the logits, and predict exactly the same digit for every image. Accuracy is ${num("Sp:accuracy")} percent everywhere. Small differences can come from compiler floating-point optimisations such as fused multiply-add.`,
    `${num("Sp:val:passed")}/${num("Sp:val:total")} comparisons pass | max logit difference ${num("Sp:val:cuda:maxerr")} | 100 % identical predictions | ${num("Sp:accuracy")} % accuracy`);
  card(s, 0.5, 1.3, 2.1, 1.9, `${num("Sp:val:passed")}/${num("Sp:val:total")}`, "comparisons pass", GREEN);
  card(s, 2.75, 1.3, 2.1, 1.9, num("Sp:val:cuda:maxerr"), "max logit difference, GPU vs serial", BLUE, { bigSize: 26 });
  card(s, 5.0, 1.3, 2.1, 1.9, "100 %", "identical predicted digits", PURPLE);
  card(s, 7.25, 1.3, 2.25, 1.9, `${num("Sp:accuracy")} %`, "MNIST test accuracy", INK);
  bullets(s, ["OpenMP is bit-identical to serial", "Float32 vs an independent float64 NumPy computation: " + num("Sp:val:numpy:maxerr") + " (tolerance 1×10⁻⁴)", "Differences can come from compiler floating-point optimisations (e.g. fused multiply-add)"], 0.5, 3.5, 9.0, 1.6, { fontSize: 15 });
}
// 10 OpenMP
{
  const s = addSlide("CONTENT", "Results", "OpenMP scales with the fast cores – and loses at batch 1 on the M4", 1.5,
    `RQ1. On the Xeon the speedup is almost linear: ${f1("Sp:omp:speedup:4096:24")} times with 24 threads at batch 4096, efficiency ${f2("Sp:omp:eff:4096:24")}. On the Apple M4 it follows the ideal line up to its four performance cores - ${f2("Mac:omp:speedup:4096:4")} times with four threads - then flattens at ${f1("Mac:omp:speedup:4096:10")} times with ten. With one image per batch, OpenMP on the M4 is slower than serial: ${f2("Mac:omp:speedup:1:10")} times with ten threads, because the synchronisation cost per batch is larger than the work. On the Xeon one image takes ${f1("Sp:serial:usimg:1")} microseconds, on the M4 only ${f1("Mac:serial:usimg:1")}. The Mac is not compared with the GPU.`,
    `Xeon ${f1("Sp:omp:speedup:4096:24")}× (24 threads) | M4 ${f1("Mac:omp:speedup:4096:10")}× (10 threads) | M4 batch 1: ${f2("Mac:omp:speedup:1:10")}×`);
  image(s, "omp_combined", 0.3, 1.15, 7.2, 3.6, "OpenMP speedup and efficiency on M4 and Xeon");
  card(s, 7.65, 1.2, 1.9, 1.2, `${f1("Sp:omp:speedup:4096:24")}×`, "Xeon, 24 threads, batch 4096", BLUE, { bigSize: 30, labelSize: 12, bigH: 0.55 });
  card(s, 7.65, 2.5, 1.9, 1.2, `${f1("Mac:omp:speedup:4096:10")}×`, "M4, 10 threads, batch 4096", BLUE, { bigSize: 30, labelSize: 12, bigH: 0.55 });
  card(s, 7.65, 3.8, 1.9, 1.2, `${f2("Mac:omp:speedup:1:10")}×`, "M4, 10 threads, batch 1", GRAY, { bigSize: 30, labelSize: 12, bigH: 0.55 });
}
// 11 compute-only vs end-to-end (native chart)
{
  const s = addSlide("CONTENT", "Results", "Compute-only versus end-to-end: the GPU's lead shrinks", 1.5,
    `RQ2. Two different questions. Compute-only - just the hidden layer, output layer and argmax - the GPU kernels are ${f1("Sp:comp:gpuvsserial:4096")} times faster than serial and ${f2("Sp:comp:gpuvsomp:4096")} times faster than the best OpenMP at batch 4096. End-to-end, with single-threaded preprocessing and copies, the CUDA pipeline is ${f1("Sp:cuda:speedup:4096")} times faster than serial and only ${f2("Sp:cuda:vscpu:4096")} times faster than OpenMP. The hybrid pipeline reaches ${f1("Sp:hyb:best:speedup:4096")} times. For the hybrid there is no compute-only number because its stages overlap. This CUDA result uses a fixed 16 by 16 block; OpenMP and the hybrid use their best thread count.`,
    `Compute-only: OpenMP ${f1("Sp:comp:ompspeedup:4096")}×, GPU kernels ${f1("Sp:comp:gpuvsserial:4096")}×. End-to-end: OpenMP ${f1("Sp:omp:best:speedup:4096")}×, CUDA ${f1("Sp:cuda:speedup:4096")}×, hybrid ${f1("Sp:hyb:best:speedup:4096")}×`);
  s.addChart(pres.charts.BAR, [
    { name: "Compute-only (stages 1–3)", labels: ["OpenMP, 24 threads", CUDA, "Hybrid pipeline"], values: [val("Sp:comp:ompspeedup:4096"), val("Sp:comp:gpuvsserial:4096"), 0] },
    { name: "End-to-end (stages 0–3)", labels: ["OpenMP, 24 threads", CUDA, "Hybrid pipeline"], values: [val("Sp:omp:best:speedup:4096"), val("Sp:cuda:speedup:4096"), val("Sp:hyb:best:speedup:4096")] },
  ], { x: 0.4, y: 1.2, w: 6.2, h: 3.9, barDir: "col", barGrouping: "clustered", chartColors: ["94A3B8", NAVY], showLegend: true, legendPos: "b", legendFontSize: 12, legendColor: INK,
       showValue: true, dataLabelFormatCode: '0.0"×";;', dataLabelFontSize: 12, dataLabelColor: INK, dataLabelPosition: "outEnd",
       catAxisLabelFontSize: 11, catAxisLabelColor: INK, valAxisLabelFontSize: 11, valAxisLabelColor: INK, valAxisTitle: "Speedup over serial (×), batch 4096", showValAxisTitle: true, valAxisTitleFontSize: 11, valAxisTitleColor: INK,
       valGridLine: { color: "E5E7EB", size: 0.5 }, catGridLine: { style: "none" }, valAxisMaxVal: 60, valAxisMinVal: 0 });
  bullets(s, [`Compute-only: kernels ${f1("Sp:comp:gpuvsserial:4096")}× serial, ${f2("Sp:comp:gpuvsomp:4096")}× best OpenMP`, `End-to-end: only ${f2("Sp:cuda:vscpu:4096")}× best OpenMP`, `Batch 1: pipeline ${f2("Sp:cuda:speedup:1")}× (slower than serial)`, "Hybrid: no compute-only number (stages overlap)"], 6.8, 1.3, 2.8, 3.7, { fontSize: 14 });
}
// 12 breakdown
{
  const s = addSlide("CONTENT", "Results", "Where the CUDA pipeline's time goes", 1.5,
    `RQ4. At batch 4096 the pipeline spends ${f1("Sp:cuda:kshare:4096")} percent in GPU kernels, ${f1("Sp:cuda:preshare:4096")} percent in the single-threaded CPU preprocessing - ${f1("Sp:cuda:pre:4096")} milliseconds, constant for every batch size - and only ${f1("Sp:cuda:tshare:4096")} percent in copies. The host-to-device copy of 31.4 megabytes takes ${f2("Sp:cuda:h2d:4096")} ms, ${f1("Sp:cuda:h2dgbs:4096")} gigabytes per second, matching my separate PCIe measurement. At batch 1 the picture flips: kernels ${f1("Sp:cuda:kshare:1")} percent, copies ${f1("Sp:cuda:tshare:1")} percent, launch overhead ${f1("Sp:cuda:othershare:1")} percent.`,
    `Batch 4096: kernels ${f1("Sp:cuda:kshare:4096")} %, preprocessing ${f1("Sp:cuda:preshare:4096")} %, copies ${f1("Sp:cuda:tshare:4096")} % | batch 1: kernels ${f1("Sp:cuda:kshare:1")} %, copies ${f1("Sp:cuda:tshare:1")} %`);
  const h = image(s, "transfer_breakdown_spartan_k40_native", 0.4, 1.15, 4.6, 3.95, "Stage breakdown of the CUDA pipeline");
  card(s, 5.3, 1.25, 2.1, 1.7, `${f1("Sp:cuda:preshare:4096")} %`, "CPU preprocessing (1 thread), batch 4096", BLUE);
  card(s, 7.5, 1.25, 2.0, 1.7, `${f1("Sp:cuda:tshare:4096")} %`, "copies (H2D + D2H), batch 4096", ORANGE);
  bullets(s, [`Preprocessing: ${f1("Sp:cuda:pre:4096")} ms per pass, constant`, `H2D copy: ${f2("Sp:cuda:h2d:4096")} ms = ${f1("Sp:cuda:h2dgbs:4096")} GB/s`, `Batch 1: copies ${f1("Sp:cuda:tshare:1")} %, launch/sync ${f1("Sp:cuda:othershare:1")} %`], 5.3, 3.15, 4.2, 2.0, { fontSize: 14 });
}
// 13 hybrid
{
  const s = addSlide("CONTENT", "Results", "The hybrid hides CPU work behind the GPU", 1.5,
    `RQ5. The pipelined hybrid needs ${f1("Sp:hyb:best:e2e:4096")} ms at batch 4096: ${f2("Sp:hyb:vscuda:4096")} times faster than the CUDA pipeline and ${f2("Sp:hyb:vscpu:4096")} times faster than the best OpenMP. Two ingredients: parallel preprocessing alone - the hybrid-sequential control - gives ${f2("Sp:hseq:vscuda:4096")} times, and overlapping batches adds another ${f2("Sp:hyb:vshseq:4096")} times. The hybrid time is only ${f2("Sp:hyb:vskernel:4096")} times the kernel-only time, so copies and preprocessing are almost completely hidden. The hybrid is fastest from batch ${num("Sp:hyb:crossover")}; at batch 1 and 8 OpenMP alone wins. All differences are significant, p below 10 to the minus 32.`,
    `Hybrid ${f1("Sp:hyb:best:e2e:4096")} ms: ${f2("Sp:hyb:vscuda:4096")}× vs CUDA pipeline, ${f2("Sp:hyb:vscpu:4096")}× vs best OpenMP | parallel preprocessing ${f2("Sp:hseq:vscuda:4096")}× + overlap ${f2("Sp:hyb:vshseq:4096")}×`);
  const h = image(s, "hybrid_compare_spartan_k40_native", 0.5, 1.12, 9.0, 2.85, "Hybrid versus non-hybrid execution time and speedup");
  card(s, 0.5, 4.05, 2.85, 1.2, `${f1("Sp:hyb:best:e2e:4096")} ms`, "hybrid pass at batch 4096", GREEN, { bigSize: 28, labelSize: 12, bigH: 0.55 });
  card(s, 3.575, 4.05, 2.85, 1.2, `${f2("Sp:hseq:vscuda:4096")}×`, "from parallel preprocessing alone (control vs CUDA pipeline)", BLUE, { bigSize: 28, labelSize: 12, bigH: 0.55 });
  card(s, 6.65, 4.05, 2.85, 1.2, `${f2("Sp:hyb:vshseq:4096")}×`, "extra from overlapping batches", PURPLE, { bigSize: 28, labelSize: 12, bigH: 0.55 });
}
// 14 Amdahl
{
  const s = addSlide("CONTENT", "Results", "Amdahl's law: the batch size changes the serial fraction", 1.25,
    `RQ6. I fitted Amdahl's law to the measured speedups. On the Xeon, for batches of 64 or more, the serial fraction is only ${[num("Sp:amdahl:f:64"), num("Sp:amdahl:f:4096")].sort().join(" to ")}, a ceiling above 130 times - so the ${f1("Sp:omp:speedup:4096:24")} times at 24 threads is not limited by the serial fraction. With one image per batch it is ${num("Sp:amdahl:f:1")}, a ceiling of only ${f1("Sp:amdahl:ceil:1")} times. On the M4 the Karp-Flatt metric jumps from ${num("Mac:kf:4096:4")} to ${num("Mac:kf:4096:6")} when the efficiency cores join in - a heterogeneous chip breaks the equal-processor assumption. Synchronisation cost against work per batch explains the rest: ${f1("Sp:micro:openmp_fork_join:24")} microseconds fork-join on the Xeon, ${f1("Mac:micro:openmp_fork_join:10")} on the M4.`,
    `Xeon f = ${[num("Sp:amdahl:f:64"), num("Sp:amdahl:f:4096")].sort().join("–")} (batch ≥64), f = ${num("Sp:amdahl:f:1")} (batch 1) | M4 Karp–Flatt ${num("Mac:kf:4096:4")} → ${num("Mac:kf:4096:6")}`);
  const h = image(s, "amdahl_combined", 0.9, 1.15, 8.2, 2.95, "Measured speedups and fitted Amdahl curves");
  bullets(s, [`Xeon, batch ≥ 64: f = ${[num("Sp:amdahl:f:64"), num("Sp:amdahl:f:4096")].sort().join("–")}; measured ${f1("Sp:omp:speedup:4096:24")}× is far below the ceiling`, `Batch 1: f = ${num("Sp:amdahl:f:1")}, ceiling only ${f1("Sp:amdahl:ceil:1")}×`, `M4: Karp–Flatt jumps ${num("Mac:kf:4096:4")} → ${num("Mac:kf:4096:6")} when efficiency cores join`], 0.5, 4.2, 9.0, 1.0, { fontSize: 14 });
}
// 15 which to use
{
  const nm = (x) => ({ "Hybrid": "Hybrid pipeline", "CUDA (1-thread pre.)": "CUDA (1-thread pre.)" }[x] || x);
  const s = addSlide("CONTENT", "Results", "Which implementation should you use?", 1.0,
    "The answer depends on the batch size. For single images or batches of 8, plain OpenMP on the multicore CPU is fastest. From batch 32 on, the pipelined hybrid is fastest, by about a factor of two over the runner-up. The CUDA pipeline with single-threaded preprocessing is never the fastest end-to-end. In a compute-only comparison the GPU kernels are the fastest from batch 32 on - so the GPU pays off only when preprocessing and copies are overlapped. Caveat: CUDA uses a fixed block size while OpenMP and hybrid use their best thread count.",
    "Batch 1–8: OpenMP | batch ≥32: hybrid pipeline | CUDA (1-thread preprocessing) never fastest end-to-end");
  const rows = [["Batch", "Fastest", "Time (ms)", "Runner-up", "Time (ms)"]].concat(D.best.map((r) => [r.batch, nm(r.fastest), r.t1.toFixed(1), nm(r.second), r.t2.toFixed(1)]));
  table(s, rows, 0.5, 1.25, 6.2, [0.8, 1.6, 1.0, 1.9, 0.9], 13);
  bullets(s, ["Batch 1–8: OpenMP on the CPU", "Batch ≥ 32: hybrid pipeline", "CUDA with 1-thread preprocessing is never fastest end-to-end"], 6.95, 1.3, 2.6, 3.0, { fontSize: 14 });
  s.addText("End-to-end times for 10,000 images, Spartan node. CUDA uses a fixed 16×16 block; OpenMP and hybrid use their best thread count.", { x: 0.5, y: 4.55, w: 9, h: 0.5, fontFace: "Calibri", fontSize: 11, color: MUTED, margin: 0, isTextBox: true });
}
pres.addSection({ title: "Conclusions" });
// 16 conclusions (dark)
{
  const s = addSlide("DARK", "Conclusions", "Conclusions, limitations and future work", 1.25,
    `Conclusions: OpenMP ${f1("Sp:omp:speedup:4096:24")} times on 24 Xeon threads; the GPU's kernels are ${f1("Sp:comp:gpuvsserial:4096")} times faster than serial but the end-to-end pipeline only ${f1("Sp:cuda:speedup:4096")} times; the hybrid reaches ${f1("Sp:hyb:best:e2e:4096")} ms per pass, ${f2("Sp:hyb:vscuda:4096")} times better than the CUDA pipeline. Best choice depends on batch size. Limitations, honestly: one old GPU, the K40m; one CPU node plus a laptop; untuned kernels and a small network; shared machines, median variation ${f1("Sp:cv:median")} percent, one slow pass kept in the data. Future work: tiled kernels and cuBLAS, newer GPUs, larger and convolutional networks, GPU-side preprocessing. Thank you - questions?`,
    "Conclusions | Limitations | Future work");
  const col = (x, head, items, c) => { s.addText(head, { x, y: 1.3, w: 2.9, h: 0.4, fontFace: "Cambria", fontSize: 18, bold: true, color: c, margin: 0, isTextBox: true });
    const runs = items.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < items.length - 1, paraSpaceAfter: 6 } }));
    s.addText(runs, { x, y: 1.8, w: 2.9, h: 3.3, fontFace: "Calibri", fontSize: 14, color: "E5E7EB", valign: "top", margin: 0, isTextBox: true }); };
  col(0.5, "Conclusions", [`OpenMP: ${f1("Sp:omp:speedup:4096:24")}× on 24 Xeon threads`, `GPU kernels ${f1("Sp:comp:gpuvsserial:4096")}×, end-to-end pipeline ${f1("Sp:cuda:speedup:4096")}×`, `Hybrid: ${f1("Sp:hyb:best:e2e:4096")} ms, ${f2("Sp:hyb:vscuda:4096")}× over the CUDA pipeline`, "Best choice depends on batch size"], "86EFAC");
  col(3.55, "Limitations", ["One old GPU (Tesla K40m), one node + one laptop", "Untuned kernels, small network", `Shared machines: median variation ${f1("Sp:cv:median")} %; one slow pass kept`, "Fixed CUDA block vs tuned OpenMP"], "FCA5A5");
  col(6.6, "Future work", ["Tiled kernels, cuBLAS", "Newer GPUs; larger and convolutional networks", "GPU-side preprocessing", "Energy measurements"], "93C5FD");
}
// ============================ BACKUP ============================
pres.addSection({ title: "Backup" });
{
  const s = addSlide("CONTENT", "Backup", "Backup: all end-to-end times (Spartan node)", 0,
    "Backup slide for questions: end-to-end time per pass for every batch size. OpenMP and Hybrid show the best thread count in brackets. The kernel column is the compute-only GPU kernel time.", "Table of all times");
  const rows = [["Batch", "Serial", "OpenMP (thr.)", "GPU kernels", "CUDA e2e", "Hybrid (thr.)", "Kernel ×", "CUDA ×", "Hybrid ×"]].concat(D.cpugpu.map((r) => [r.batch, r.serial.toFixed(1), `${r.omp.toFixed(1)} (${r.ompthr})`, r.kernel.toFixed(1), r.cuda.toFixed(1), `${r.hyb.toFixed(1)} (${r.hybthr})`, r.ks.toFixed(2), r.cs.toFixed(2), r.hs.toFixed(2)]));
  table(s, rows, 0.4, 1.2, 9.2, [0.65, 0.95, 1.4, 1.05, 1.0, 1.4, 0.9, 0.9, 0.95], 12);
  s.addText("Times in ms per pass of 10,000 images; speedups (×) over serial. “CUDA” = single-threaded preprocessing, fixed 16×16 block. Kernel = compute-only.", { x: 0.4, y: 4.45, w: 9.2, h: 0.5, fontFace: "Calibri", fontSize: 11, color: MUTED, margin: 0, isTextBox: true });
}
{
  const s = addSlide("CONTENT", "Backup", "Backup: CUDA block size and what tuning would change", 0,
    `Block size matters only at small batches: at batch 64 the kernel takes ${f1("Sp:cuda:blk8:kernel:64")} ms with 8 by 8 blocks, ${f1("Sp:cuda:blk16:kernel:64")} with 16 by 16 and ${f1("Sp:cuda:blk32:kernel:64")} with 32 by 32. If the best block were used, the CUDA end-to-end time would improve by at most ${num("Sp:cuda:blockgain:max")} percent, and the crossover with OpenMP would move from batch 256 to ${num("Sp:cuda:bestblock:crossover")}. The main comparison keeps the fixed block, so it is not best-versus-best.`, "Block-size figure and sensitivity");
  image(s, "cuda_block_size_spartan_k40_native", 0.4, 1.15, 5.0, 3.95, "Kernel time for three block sizes");
  bullets(s, [`Batch 64: ${f1("Sp:cuda:blk8:kernel:64")} / ${f1("Sp:cuda:blk16:kernel:64")} / ${f1("Sp:cuda:blk32:kernel:64")} ms (8×8 / 16×16 / 32×32)`, "Batch 4096: all within 1 %", `Best block improves end-to-end by ≤ ${num("Sp:cuda:blockgain:max")} %`, "Main comparison: fixed block vs tuned OpenMP, not best-vs-best"], 5.7, 1.3, 3.9, 3.5, { fontSize: 14 });
}
{
  const s = addSlide("CONTENT", "Backup", "Backup: compiler settings and flag sensitivity", 0,
    "Compiler settings. On Spartan one binary is built with g++ 11.4.1 through nvcc 11.7 for the K40's compute capability 3.5; the reference build adds -march=native, the sensitivity build does not. The Mac uses Apple clang with no architecture flag. No fast-math, and the floating-point contraction options were not set, so compiler defaults apply. Plain -O3 changes the serial time by only about five percent.", "Compiler table and flag sensitivity");
  table(s, [["Build", "Compiler", "Flags"], ["Apple M4", "Apple clang 21.0.0, libomp 23.1.2", "-O3 -std=c++14 -fopenmp; no -march"], ["Spartan reference", "g++ 11.4.1 via nvcc 11.7.99", "host -O3 -fopenmp -march=native; device -O3 -arch=sm_35"], ["Spartan sensitivity", "same", "same without -march=native"]], 0.4, 1.2, 9.2, [1.8, 3.1, 4.3], 12);
  const rows = [["Implementation (ms per pass)", "native 256", "-O3 256", "native 4096", "-O3 4096"]].concat(D.flags.map((r) => [r.impl, r.native256.toFixed(1), r.o3256.toFixed(1), r.native4096.toFixed(1), r.o34096.toFixed(1)]));
  table(s, rows, 0.4, 2.85, 9.2, [3.2, 1.5, 1.5, 1.5, 1.5], 12);
  s.addText("No -ffast-math; -ffp-contract and --fmad not set (compiler defaults).", { x: 0.4, y: 4.75, w: 9, h: 0.3, fontFace: "Calibri", fontSize: 11, color: MUTED, margin: 0, isTextBox: true });
}
{
  const s = addSlide("CONTENT", "Backup", "Backup: cold start and one-time GPU costs", 0,
    `One-time costs excluded from steady-state times, measured in ten fresh processes: CUDA context creation ${f1("Sp:cold:init:mean")} ms on average, weight upload ${f2("Sp:cold:upload:mean")} ms, buffer allocation ${f2("Sp:cold:alloc:mean")} ms - ${f1("Sp:cold:ctor:mean")} ms in total, about ${f2("Sp:cold:ctorvspass")} times a steady-state CUDA pass. After set-up the first CUDA pass shows no penalty; the first 24-thread OpenMP pass is ${f1("Sp:cold:omp:firstpenalty")} percent slower.`, "Cold-start table");
  const r = (l, k) => [l, num(`Sp:cold:${k}:mean`), num(`Sp:cold:${k}:median`), num(`Sp:cold:${k}:std`), num(`Sp:cold:${k}:min`), num(`Sp:cold:${k}:max`)];
  table(s, [["Quantity (ms)", "Mean", "Median", "Std. dev.", "Min", "Max"], r("CUDA context creation", "init"), r("Weight upload", "upload"), r("Buffer/stream/event allocation", "alloc"), r("Total one-time GPU set-up", "ctor"), r("CUDA pass, 1st", "cuda1"), r("CUDA pass, 3rd", "cuda3"), r("Hybrid pass, 1st", "hyb1"), r("Hybrid pass, 2nd", "hyb2"), r("OpenMP 24 thr. pass, 1st", "omp1"), r("OpenMP 24 thr. pass, 2nd", "omp2")], 0.4, 1.2, 9.2, [3.2, 1.2, 1.2, 1.2, 1.2, 1.2], 12);
  s.addText(`10 fresh processes, batch 256, 24 OpenMP threads, Spartan node.`, { x: 0.4, y: 4.75, w: 9, h: 0.3, fontFace: "Calibri", fontSize: 11, color: MUTED, margin: 0, isTextBox: true });
}
{
  const s = addSlide("CONTENT", "Backup", "Backup: run-to-run variation and the slow pass", 0,
    `Variation is small: median coefficient of variation ${f1("Sp:cv:median")} percent on Spartan. The largest is the ${num("Sp:slow:impl")} configuration at batch ${num("Sp:slow:batch")} with ${num("Sp:slow:threads")} threads: mean ${f2("Sp:slow:mean")} ms, median ${f2("Sp:slow:median")}, standard deviation ${f2("Sp:slow:std")}, minimum ${f2("Sp:slow:min")}, maximum ${f2("Sp:slow:max")}. One pass is over 1.5 times the median. I did not remove it; it is in all statistics and in the raw data.`, "Slow-pass statistics");
  table(s, [["Configuration", "n", "Mean", "Median", "Std. dev.", "Min", "Max"], [`Spartan: ${num("Sp:slow:impl")}, batch ${num("Sp:slow:batch")}, ${num("Sp:slow:threads")} threads (ms)`, num("Sp:slow:n"), num("Sp:slow:mean"), num("Sp:slow:median"), num("Sp:slow:std"), num("Sp:slow:min"), num("Sp:slow:max")], [`M4: ${num("Mac:slow:impl")}, batch ${num("Mac:slow:batch")} (ms)`, num("Mac:slow:n"), num("Mac:slow:mean"), num("Mac:slow:median"), num("Mac:slow:std"), num("Mac:slow:min"), num("Mac:slow:max")]], 0.4, 1.4, 9.2, [3.9, 0.5, 0.9, 0.9, 1.1, 0.9, 1.0], 12);
  bullets(s, [`Median coefficient of variation: ${f1("Sp:cv:median")} % (Spartan), ${f1("Mac:cv:median")} % (M4)`, `One pass above 1.5× median in the Spartan case; the run is kept`, "20 passes run back to back: not independent samples of machine state"], 0.5, 3.0, 9.0, 1.8, { fontSize: 15 });
}
{
  const s = addSlide("CONTENT", "Backup", "Backup: measured platform limits", 0,
    "Micro-benchmark results used in the analysis: PCIe bandwidth, device memory copy rate, kernel launch cost, CPU memory bandwidth and OpenMP fork-join cost. No hardware peak numbers are assumed - everything here was measured.", "Micro-benchmarks");
  table(s, [["Quantity (Spartan node)", "Measured value"]].concat(D.micro), 0.5, 1.3, 9.0, [5.6, 3.4], 14);
}

// ---------- write files ----------
(async () => {
  const out = path.join(__dirname, "CS259_Hybrid_CPU_GPU_Induru.pptx");
  await pres.writeFile({ fileName: out });
  await applyTheme(out, THEME);
  const md = LOG.map((l) => `## Slide ${l.n}: ${l.title}\n\n**Time:** ${l.minutes} min\n\n**On the slide:** ${l.text}\n\n**What to say:** ${l.notes}\n`).join("\n");
  fs.writeFileSync(path.join(__dirname, "speaker_notes.md"), "# Speaker notes (20-minute talk; slides 1-16 about 19 minutes, backups for questions)\n\n" + md);
  fs.writeFileSync(path.join(__dirname, "slide_content.md"), "# Slide content\n\n" + LOG.map((l) => `${l.n}. **${l.title}** — ${l.text}`).join("\n") + "\n");
  console.log("wrote", out, "with", LOG.length, "slides; total talk minutes:", LOG.reduce((a, l) => a + l.minutes, 0));
})();
