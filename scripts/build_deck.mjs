import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { Presentation, PresentationFile } from "@oai/artifact-tool";
import JSZip from "jszip";

const SKILL_DIR = process.env.SKILL_DIR;
const workspaceDir = process.env.WORKSPACE_DIR;
const TMP_DIR = process.env.TMP_DIR;
const FINAL_PPTX = process.env.FINAL_PPTX;
const RUNTIME_PYTHON = process.env.RUNTIME_PYTHON;

for (const [name, value] of Object.entries({ SKILL_DIR, workspaceDir, TMP_DIR, FINAL_PPTX, RUNTIME_PYTHON })) {
  if (!value || !path.isAbsolute(value)) throw new Error(`${name} must be an absolute path`);
}

const {
  applyPresentationChartFont,
  finalizePresentation,
} = await import(pathToFileURL(path.join(SKILL_DIR, "container_tools/artifact_tool_utils.mjs")).href);

const FONT = "Nimbus Sans";
const NAVY = "#0B1F3A";
const RED = "#E31937";
const BLUE = "#2D7FF9";
const SKY = "#DCEEFF";
const PALE = "#F4F7FB";
const MID = "#D8DEE9";
const INK = "#172033";
const MUTED = "#667085";
const WHITE = "#FFFFFF";
const SLIDE_W = 1280;
const SLIDE_H = 720;

const presentation = Presentation.create({ slideSize: { width: SLIDE_W, height: SLIDE_H } });

async function setCoreProperties(pptxPath) {
  const zip = await JSZip.loadAsync(await fs.readFile(pptxPath));
  const coreEntry = zip.file("docProps/core.xml");
  if (!coreEntry) throw new Error("PPTX core properties are missing");
  let core = await coreEntry.async("string");
  core = core
    .replace(/<dc:creator>[\s\S]*?<\/dc:creator>/, "<dc:creator>Oluwaseyi Caleb Folorunso</dc:creator>")
    .replace(/<lastModifiedBy>[\s\S]*?<\/lastModifiedBy>/, "<lastModifiedBy>Oluwaseyi Caleb Folorunso</lastModifiedBy>")
    .replace(/<dc:title>[\s\S]*?<\/dc:title>/, "<dc:title>Intuit Dome arena-store analysis</dc:title>");
  zip.file("docProps/core.xml", core);
  const bytes = await zip.generateAsync({ type: "nodebuffer", compression: "DEFLATE" });
  await fs.writeFile(pptxPath, bytes);
}

function addShape(slide, geometry, position, fill, line = { fill: "none", width: 0 }, radius = undefined) {
  const config = { geometry, position, fill, line };
  if (radius !== undefined) config.borderRadius = radius;
  return slide.shapes.add(config);
}

function addText(slide, text, position, options = {}) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    position,
    fill: "none",
    line: { fill: "none", width: 0 },
  });
  shape.text = text;
  shape.text.style = {
    typeface: FONT,
    fontSize: options.fontSize ?? 22,
    bold: options.bold ?? false,
    color: options.color ?? INK,
    alignment: options.alignment ?? "left",
    verticalAlignment: options.verticalAlignment ?? "top",
    autoFit: options.autoFit ?? "none",
    wrap: "square",
    lineSpacing: options.lineSpacing ?? 1.0,
    insets: options.insets ?? { top: 0, right: 0, bottom: 0, left: 0 },
  };
  return shape;
}

function addRichText(slide, paragraphs, position, options = {}) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    position,
    fill: "none",
    line: { fill: "none", width: 0 },
  });
  shape.text.set(paragraphs);
  shape.text.style = {
    typeface: FONT,
    fontSize: options.fontSize ?? 22,
    color: options.color ?? INK,
    verticalAlignment: options.verticalAlignment ?? "top",
    autoFit: "none",
    wrap: "square",
    lineSpacing: options.lineSpacing ?? 1.0,
    insets: options.insets ?? { top: 0, right: 0, bottom: 0, left: 0 },
  };
  return shape;
}

function addFooter(slide, page, source = "Source: 2025 Clippers Business Insights challenge dataset; author analysis.") {
  addText(slide, source, { left: 72, top: 685, width: 1000, height: 18 }, { fontSize: 11, color: MUTED });
  addText(slide, String(page).padStart(2, "0"), { left: 1160, top: 683, width: 48, height: 20 }, { fontSize: 12, bold: true, color: MUTED, alignment: "right" });
}

function addBase(slide, title, page, kicker = "INTUIT DOME  /  ARENA-STORE ANALYSIS", source = undefined) {
  slide.background.fill = WHITE;
  addShape(slide, "rect", { left: 0, top: 0, width: 1280, height: 12 }, NAVY);
  addShape(slide, "rect", { left: 72, top: 44, width: 42, height: 6 }, RED);
  addText(slide, kicker, { left: 126, top: 38, width: 640, height: 18 }, { fontSize: 12, bold: true, color: MUTED });
  addText(slide, title, { left: 72, top: 66, width: 1136, height: 62 }, { fontSize: 44, bold: true, color: NAVY, lineSpacing: 0.95 });
  addShape(slide, "line", { left: 72, top: 136, width: 1136, height: 0 }, "none", { style: "solid", fill: MID, width: 1 });
  addFooter(slide, page, source);
}

function addMetricCard(slide, x, y, w, h, number, label, detail, accent = BLUE) {
  addShape(slide, "roundRect", { left: x, top: y, width: w, height: h }, WHITE, { style: "solid", fill: MID, width: 1 }, 18).shadow = "shadow-sm";
  addShape(slide, "rect", { left: x, top: y, width: 8, height: h }, accent);
  addText(slide, number, { left: x + 28, top: y + 24, width: w - 52, height: 50 }, { fontSize: 38, bold: true, color: NAVY });
  addText(slide, label.toUpperCase(), { left: x + 30, top: y + 78, width: w - 52, height: 22 }, { fontSize: 14, bold: true, color: accent });
  addText(slide, detail, { left: x + 30, top: y + 112, width: w - 56, height: h - 128 }, { fontSize: 18, color: MUTED, lineSpacing: 1.05 });
}

function styleChart(chart, { legend = false } = {}) {
  applyPresentationChartFont(chart, { fontFamily: FONT });
  return chart;
}

// Slide 1 — cover
{
  const slide = presentation.slides.add();
  slide.background.fill = NAVY;
  addShape(slide, "rect", { left: 0, top: 0, width: 18, height: 720 }, RED);
  addShape(slide, "ellipse", { left: 930, top: 30, width: 350, height: 350 }, "#123A69", { fill: "none", width: 0 });
  addShape(slide, "ellipse", { left: 1000, top: 390, width: 280, height: 280 }, BLUE, { fill: "none", width: 0 });
  addShape(slide, "rect", { left: 895, top: 0, width: 16, height: 720 }, RED);
  addText(slide, "2025 BUSINESS INSIGHTS CASE STUDY", { left: 90, top: 72, width: 620, height: 28 }, { fontSize: 16, bold: true, color: SKY });
  addText(slide, "Intuit Dome\narena-store analysis", { left: 90, top: 150, width: 760, height: 170 }, { fontSize: 64, bold: true, color: WHITE, lineSpacing: 0.88 });
  addText(slide, "A defensible view of revenue mix, transaction economics, and demand timing", { left: 94, top: 350, width: 720, height: 75 }, { fontSize: 26, color: "#DCE6F3", lineSpacing: 1.05 });
  addShape(slide, "line", { left: 94, top: 458, width: 650, height: 0 }, "none", { style: "solid", fill: RED, width: 5 });
  addText(slide, "$1.156M", { left: 94, top: 496, width: 210, height: 46 }, { fontSize: 36, bold: true, color: WHITE });
  addText(slide, "NET SALES", { left: 96, top: 544, width: 200, height: 22 }, { fontSize: 13, bold: true, color: SKY });
  addText(slide, "31,346", { left: 330, top: 496, width: 210, height: 46 }, { fontSize: 36, bold: true, color: WHITE });
  addText(slide, "TRANSACTIONS", { left: 332, top: 544, width: 200, height: 22 }, { fontSize: 13, bold: true, color: SKY });
  addText(slide, "3", { left: 570, top: 496, width: 100, height: 46 }, { fontSize: 36, bold: true, color: WHITE });
  addText(slide, "PLAYOFF GAMES", { left: 572, top: 544, width: 200, height: 22 }, { fontSize: 13, bold: true, color: SKY });
  addText(slide, "Oluwaseyi Caleb Folorunso  •  Public portfolio edition", { left: 94, top: 650, width: 760, height: 22 }, { fontSize: 14, color: "#B8C6D9" });
  slide.speakerNotes.textFrame.setText("Scope: three Clippers home playoff games against Denver on Apr 24, Apr 26, and May 1, 2025. Source: LA Clippers 2025 Business Insights challenge workbook supplied for analysis.");
}

// Slide 2 — executive facts
{
  const slide = presentation.slides.add();
  addBase(slide, "Four facts replace four vague claims", 2);
  addMetricCard(slide, 72, 166, 540, 205, "$1.156M", "Net sales", "31,346 transactions from 16,835 purchasing accounts.", NAVY);
  addMetricCard(slide, 668, 166, 540, 205, "62.8%", "Food & beverage share", "Food & beverage was 1.69× retail—or 69.1% higher.", RED);
  addMetricCard(slide, 72, 402, 540, 205, "3 of 3", "Revenue peak", "The final hour before scheduled tipoff led every game.", BLUE);
  addMetricCard(slide, 668, 402, 540, 205, "0", "Matching entry IDs", "Individual entry-to-purchase conversion is not identifiable.", RED);
  addText(slide, "Descriptive window: Games 3, 4, and 6 of one playoff series", { left: 72, top: 638, width: 760, height: 26 }, { fontSize: 17, bold: true, color: MUTED });
  slide.speakerNotes.textFrame.setText("All values are calculated from the aggregate tables in data/processed. Net sales are not profit; the workbook contains no cost or margin fields.");
}

// Slide 3 — revenue mix
{
  const slide = presentation.slides.add();
  addBase(slide, "Food & beverage is the scale engine", 3);
  const chart = slide.charts.add("bar", {
    position: { left: 200, top: 172, width: 636, height: 420 },
    categories: ["Service items", "Retail", "Food & beverage"],
    series: [{
      name: "Net sales",
      values: [1435.24, 428929.50, 725426.00],
      valuesFormatCode: "$0,\"K\"",
      fill: RED,
      points: [
        { idx: 0, fill: "#89CFF0" },
        { idx: 1, fill: BLUE },
        { idx: 2, fill: RED },
      ],
    }],
    barOptions: { direction: "bar", grouping: "clustered", gapWidth: 55 },
    hasLegend: false,
    xAxis: {
      visible: false,
      min: 0,
      max: 800000,
      majorUnit: 200000,
      numberFormatCode: "$0,\"K\"",
      tickLabelPosition: "none",
      textStyle: { typeface: FONT, fontSize: 14, fill: MUTED },
      line: { fill: "none", width: 0 },
      majorGridlines: null,
    },
    yAxis: {
      textStyle: { typeface: FONT, fontSize: 17, fill: MUTED },
      line: { fill: "none", width: 0 },
      majorGridlines: null,
    },
    dataLabels: { showValue: true, position: "outEnd", textStyle: { typeface: FONT, fontSize: 16, fill: INK, bold: true } },
  });
  styleChart(chart);
  // LibreOffice exposes the hidden value-axis labels during PDF conversion;
  // a neutral mask keeps the PDF aligned with the intended editable chart.
  addShape(slide, "rect", { left: 188, top: 548, width: 668, height: 48 }, WHITE, { fill: "none", width: 0 });
  addText(slide, "Food & beverage", { left: 72, top: 236, width: 112, height: 24 }, { fontSize: 17, color: MUTED, alignment: "right" });
  addText(slide, "Retail", { left: 72, top: 363, width: 112, height: 24 }, { fontSize: 17, color: MUTED, alignment: "right" });
  addText(slide, "Service items", { left: 72, top: 489, width: 112, height: 24 }, { fontSize: 17, color: MUTED, alignment: "right" });

  addShape(slide, "roundRect", { left: 882, top: 172, width: 326, height: 420 }, PALE, { style: "solid", fill: MID, width: 1 }, 18);
  addText(slide, "$725K", { left: 914, top: 205, width: 250, height: 50 }, { fontSize: 42, bold: true, color: RED });
  addText(slide, "FOOD & BEVERAGE", { left: 916, top: 258, width: 250, height: 22 }, { fontSize: 14, bold: true, color: RED });
  addText(slide, "1.69×", { left: 914, top: 315, width: 250, height: 48 }, { fontSize: 38, bold: true, color: NAVY });
  addText(slide, "versus retail sales", { left: 916, top: 363, width: 250, height: 30 }, { fontSize: 19, color: MUTED });
  addShape(slide, "line", { left: 914, top: 417, width: 250, height: 0 }, "none", { style: "solid", fill: MID, width: 1 });
  addText(slide, "99.1%", { left: 914, top: 442, width: 250, height: 44 }, { fontSize: 36, bold: true, color: BLUE });
  addText(slide, "F&B share inside mixed-format stores", { left: 916, top: 490, width: 250, height: 62 }, { fontSize: 18, color: MUTED, lineSpacing: 1.05 });
  addText(slide, "Correct framing: 69.1% higher—not 1.7% better.", { left: 76, top: 614, width: 820, height: 30 }, { fontSize: 21, bold: true, color: NAVY });
  slide.speakerNotes.textFrame.setText("Source: business_vertical_summary.csv and mixed_store_vertical_summary.csv, built from the supplied challenge workbook. Definitions: net sales is the sum of NetAmount; shares are across all three games.");
}

// Slide 4 — store economics
{
  const slide = presentation.slides.add();
  addBase(slide, "Mixed stores win volume; retail wins ticket", 4);
  addText(slide, "TRANSACTION VOLUME", { left: 72, top: 158, width: 500, height: 24 }, { fontSize: 16, bold: true, color: MUTED });
  addText(slide, "AVERAGE TRANSACTION VALUE", { left: 668, top: 158, width: 500, height: 24 }, { fontSize: 16, bold: true, color: MUTED });
  const volume = slide.charts.add("bar", {
    position: { left: 64, top: 188, width: 552, height: 344 },
    categories: ["Concessions", "Retail", "Mixed-format"],
    series: [{
      name: "Transactions",
      values: [1282, 4790, 25274],
      valuesFormatCode: "#,##0",
      fill: NAVY,
      points: [{ idx: 0, fill: BLUE }, { idx: 1, fill: RED }, { idx: 2, fill: NAVY }],
    }],
    barOptions: { direction: "column", grouping: "clustered", gapWidth: 65 },
    hasLegend: false,
    xAxis: { textStyle: { typeface: FONT, fontSize: 14, fill: MUTED }, line: { style: "solid", fill: MID, width: 1 }, majorGridlines: null },
    yAxis: { min: 0, max: 30000, majorUnit: 10000, numberFormatCode: "0,\"K\"", textStyle: { typeface: FONT, fontSize: 13, fill: MUTED }, line: { fill: "none", width: 0 }, majorGridlines: { style: "solid", fill: MID, width: 1 } },
    dataLabels: { showValue: true, position: "outEnd", textStyle: { typeface: FONT, fontSize: 15, fill: INK, bold: true } },
  });
  styleChart(volume);

  const ticket = slide.charts.add("bar", {
    position: { left: 660, top: 188, width: 552, height: 344 },
    categories: ["Concessions", "Retail", "Mixed-format"],
    series: [{
      name: "Average transaction",
      values: [31.413674, 88.437630, 27.376045],
      valuesFormatCode: "$0.00",
      fill: NAVY,
      points: [{ idx: 0, fill: BLUE }, { idx: 1, fill: RED }, { idx: 2, fill: NAVY }],
    }],
    barOptions: { direction: "column", grouping: "clustered", gapWidth: 65 },
    hasLegend: false,
    xAxis: { textStyle: { typeface: FONT, fontSize: 14, fill: MUTED }, line: { style: "solid", fill: MID, width: 1 }, majorGridlines: null },
    yAxis: { min: 0, max: 100, majorUnit: 20, numberFormatCode: "$0", textStyle: { typeface: FONT, fontSize: 13, fill: MUTED }, line: { fill: "none", width: 0 }, majorGridlines: { style: "solid", fill: MID, width: 1 } },
    dataLabels: { showValue: true, position: "outEnd", textStyle: { typeface: FONT, fontSize: 15, fill: INK, bold: true } },
  });
  styleChart(ticket);

  addShape(slide, "roundRect", { left: 72, top: 560, width: 1136, height: 78 }, SKY, { style: "solid", fill: "#A7CCF4", width: 1 }, 14);
  addText(slide, "OPERATING IMPLICATION", { left: 98, top: 579, width: 220, height: 20 }, { fontSize: 14, bold: true, color: BLUE });
  addText(slide, "Run distinct tests: throughput at mixed stores; attach at retail.", { left: 330, top: 579, width: 836, height: 28 }, { fontSize: 21, bold: true, color: NAVY });
  addText(slide, "ATV is calculated after aggregating all line items to one transaction.", { left: 330, top: 610, width: 836, height: 20 }, { fontSize: 15, color: MUTED });
  slide.speakerNotes.textFrame.setText("Source: store_type_summary.csv. Average transaction value is net sales divided by unique transactions within each store type; it is not the mean line-item amount.");
}

// Slide 5 — timing
{
  const slide = presentation.slides.add();
  addBase(slide, "Normalize to tipoff: hour −1 is the revenue peak", 5, undefined, "Source: transaction timestamps; scheduled tipoffs and official game books in speaker notes.");
  const timing = slide.charts.add("line", {
    position: { left: 66, top: 172, width: 850, height: 430 },
    categories: ["−3", "−2", "−1", "Tipoff", "+1", "+2", "+3"],
    series: [
      { name: "Game 3 · Apr 24", values: [9185.75, 47690.68, 147462.35, 82002.29, 95514.95, 36946.00, 6221.50], valuesFormatCode: "$0,\"K\"", line: { style: "solid", fill: NAVY, width: 3 }, marker: { symbol: "circle", size: 7 } },
      { name: "Game 4 · Apr 26", values: [7450.00, 42345.24, 137713.63, 70427.75, 85715.75, 20581.75, 21817.00], valuesFormatCode: "$0,\"K\"", line: { style: "solid", fill: BLUE, width: 3 }, marker: { symbol: "circle", size: 7 } },
      { name: "Game 6 · May 1", values: [4124.50, 25616.58, 92538.17, 82734.52, 86953.94, 28733.88, 10583.25], valuesFormatCode: "$0,\"K\"", line: { style: "solid", fill: RED, width: 3 }, marker: { symbol: "circle", size: 7 } },
    ],
    lineOptions: { grouping: "standard", smooth: false },
    hasLegend: true,
    legend: { position: "bottom", overlay: false, textStyle: { typeface: FONT, fontSize: 14, fill: MUTED } },
    xAxis: { title: { text: "Hours from scheduled tipoff", textStyle: { typeface: FONT, fontSize: 15, fill: MUTED } }, textStyle: { typeface: FONT, fontSize: 14, fill: MUTED }, line: { style: "solid", fill: MID, width: 1 }, majorGridlines: null },
    yAxis: { min: 0, max: 160000, majorUnit: 40000, numberFormatCode: "$0,\"K\"", textStyle: { typeface: FONT, fontSize: 13, fill: MUTED }, line: { fill: "none", width: 0 }, majorGridlines: { style: "solid", fill: MID, width: 1 } },
  });
  styleChart(timing, { legend: true });

  addShape(slide, "roundRect", { left: 950, top: 172, width: 258, height: 430 }, PALE, { style: "solid", fill: MID, width: 1 }, 18);
  addText(slide, "HOUR −1 SHARE", { left: 976, top: 202, width: 210, height: 22 }, { fontSize: 15, bold: true, color: RED });
  addText(slide, "34.0%", { left: 976, top: 242, width: 210, height: 42 }, { fontSize: 34, bold: true, color: NAVY });
  addText(slide, "Game 3", { left: 978, top: 284, width: 190, height: 22 }, { fontSize: 17, color: MUTED });
  addText(slide, "35.6%", { left: 976, top: 330, width: 210, height: 42 }, { fontSize: 34, bold: true, color: BLUE });
  addText(slide, "Game 4", { left: 978, top: 372, width: 190, height: 22 }, { fontSize: 17, color: MUTED });
  addText(slide, "27.6%", { left: 976, top: 418, width: 210, height: 42 }, { fontSize: 34, bold: true, color: RED });
  addText(slide, "Game 6", { left: 978, top: 460, width: 190, height: 22 }, { fontSize: 17, color: MUTED });
  addShape(slide, "line", { left: 976, top: 510, width: 190, height: 0 }, "none", { style: "solid", fill: MID, width: 1 });
  addText(slide, "Peak revenue, not necessarily peak transaction count.", { left: 976, top: 530, width: 195, height: 56 }, { fontSize: 17, bold: true, color: NAVY, lineSpacing: 1.05 });
  addText(slide, "Displayed window contains 98.8% of sales.", { left: 72, top: 625, width: 600, height: 24 }, { fontSize: 17, color: MUTED });
  slide.speakerNotes.textFrame.setText("Scheduled tipoffs used: Apr 24 7:00 PM local, Apr 26 3:00 PM local, May 1 7:00 PM local. Official game durations: Apr 24 2:19 (https://statsdmz.nba.com/pdfs/20250424/20250424_DENLAC.pdf); Apr 26 2:30 (https://statsdmz.nba.com/pdfs/20250426/20250426_DENLAC.pdf); May 1 2:13 (https://statsdmz.nba.com/pdfs/20250501/20250501_DENLAC.pdf). Source data: game_hour_summary.csv.");
}

// Slide 6 — game trajectory
{
  const slide = presentation.slides.add();
  addBase(slide, "Game 6 net sales finished 22.8% below Game 3", 6);
  const trend = slide.charts.add("bar", {
    position: { left: 70, top: 180, width: 690, height: 360 },
    categories: ["Game 3\nApr 24", "Game 4\nApr 26", "Game 6\nMay 1"],
    series: [{
      name: "Net sales",
      values: [433679.02, 387335.12, 334776.60],
      valuesFormatCode: "$0,\"K\"",
      fill: NAVY,
      points: [{ idx: 0, fill: NAVY }, { idx: 1, fill: BLUE }, { idx: 2, fill: RED }],
    }],
    barOptions: { direction: "column", grouping: "clustered", gapWidth: 58 },
    hasLegend: false,
    xAxis: { textStyle: { typeface: FONT, fontSize: 16, fill: MUTED }, line: { style: "solid", fill: MID, width: 1 }, majorGridlines: null },
    yAxis: { min: 0, max: 500000, majorUnit: 100000, numberFormatCode: "$0,\"K\"", textStyle: { typeface: FONT, fontSize: 13, fill: MUTED }, line: { fill: "none", width: 0 }, majorGridlines: { style: "solid", fill: MID, width: 1 } },
    dataLabels: { showValue: true, position: "outEnd", textStyle: { typeface: FONT, fontSize: 16, fill: INK, bold: true } },
  });
  styleChart(trend);

  addShape(slide, "roundRect", { left: 806, top: 180, width: 402, height: 360 }, PALE, { style: "solid", fill: MID, width: 1 }, 18);
  addText(slide, "DECLINE, GAME 3 → GAME 6", { left: 836, top: 208, width: 340, height: 24 }, { fontSize: 15, bold: true, color: MUTED });
  addText(slide, "−22.8%", { left: 836, top: 254, width: 160, height: 46 }, { fontSize: 38, bold: true, color: RED });
  addText(slide, "net sales", { left: 1000, top: 266, width: 160, height: 26 }, { fontSize: 20, color: MUTED });
  addText(slide, "−13.7%", { left: 836, top: 322, width: 160, height: 46 }, { fontSize: 38, bold: true, color: NAVY });
  addText(slide, "transactions", { left: 1000, top: 334, width: 160, height: 26 }, { fontSize: 20, color: MUTED });
  addText(slide, "−10.6%", { left: 836, top: 390, width: 160, height: 46 }, { fontSize: 38, bold: true, color: BLUE });
  addText(slide, "average ticket", { left: 1000, top: 402, width: 170, height: 26 }, { fontSize: 20, color: MUTED });
  addShape(slide, "line", { left: 836, top: 468, width: 330, height: 0 }, "none", { style: "solid", fill: MID, width: 1 });
  addText(slide, "Cause remains unobserved", { left: 836, top: 490, width: 320, height: 28 }, { fontSize: 21, bold: true, color: NAVY });

  addShape(slide, "roundRect", { left: 72, top: 570, width: 1136, height: 78 }, SKY, { style: "solid", fill: "#A7CCF4", width: 1 }, 14);
  addText(slide, "323 accounts", { left: 98, top: 586, width: 210, height: 30 }, { fontSize: 25, bold: true, color: NAVY });
  addText(slide, "purchased in all 3 games", { left: 306, top: 590, width: 280, height: 24 }, { fontSize: 19, color: MUTED });
  addText(slide, "1.9% of customers", { left: 620, top: 586, width: 230, height: 30 }, { fontSize: 25, bold: true, color: BLUE });
  addText(slide, "13.5% of sales", { left: 920, top: 586, width: 230, height: 30 }, { fontSize: 25, bold: true, color: RED });
  addText(slide, "Descriptive cohort signal—not proof of loyalty or incremental lift.", { left: 98, top: 618, width: 990, height: 18 }, { fontSize: 15, color: MUTED });
  slide.speakerNotes.textFrame.setText("Source: game_summary.csv and customer_frequency_summary.csv. Declines: (Game 6 / Game 3) − 1. Customer cohorts count distinct game dates with a purchase; no causal loyalty claim is made.");
}

// Slide 7 — data quality
{
  const slide = presentation.slides.add();
  addBase(slide, "Conversion is not identifiable in this workbook", 7);
  addShape(slide, "roundRect", { left: 72, top: 166, width: 278, height: 94 }, PALE, { style: "solid", fill: MID, width: 1 }, 14);
  addText(slide, "49,223", { left: 96, top: 184, width: 220, height: 34 }, { fontSize: 30, bold: true, color: NAVY });
  addText(slide, "store-entry events", { left: 98, top: 221, width: 220, height: 24 }, { fontSize: 17, color: MUTED });
  addText(slide, "NBAId", { left: 386, top: 196, width: 125, height: 28 }, { fontSize: 22, bold: true, color: NAVY, alignment: "center" });
  addShape(slide, "line", { left: 350, top: 213, width: 36, height: 0 }, "none", { style: "solid", fill: BLUE, width: 3 });
  addShape(slide, "line", { left: 511, top: 213, width: 96, height: 0 }, "none", { style: "dashed", fill: RED, width: 3 });
  addText(slide, "0 matches", { left: 520, top: 172, width: 120, height: 24 }, { fontSize: 18, bold: true, color: RED, alignment: "center" });
  addText(slide, "×", { left: 550, top: 195, width: 54, height: 44 }, { fontSize: 38, bold: true, color: RED, alignment: "center" });
  addShape(slide, "roundRect", { left: 608, top: 166, width: 278, height: 94 }, SKY, { style: "solid", fill: "#A7CCF4", width: 1 }, 14);
  addText(slide, "CustomerIDs", { left: 634, top: 187, width: 224, height: 30 }, { fontSize: 28, bold: true, color: NAVY, alignment: "center" });
  addText(slide, "account crosswalk", { left: 636, top: 222, width: 220, height: 22 }, { fontSize: 16, color: MUTED, alignment: "center" });
  addShape(slide, "roundRect", { left: 928, top: 166, width: 280, height: 94 }, "#FFF1F3", { style: "solid", fill: "#F5A6B3", width: 1 }, 14);
  addText(slide, "No person-level conversion", { left: 952, top: 188, width: 232, height: 56 }, { fontSize: 22, bold: true, color: RED, alignment: "center", verticalAlignment: "middle", lineSpacing: 1.0 });

  const values = [
    ["Quality check", "Observed", "Treatment"],
    ["Sales rows mapped to stores", "100%", "PASS · many-to-one; dollars reconcile"],
    ["Store-entry mapping", "89.7%", "REVIEW · 5,088 events lack lookup rows"],
    ["Duplicate-looking sales lines", "94", "REVIEW · retained; no immutable line ID"],
    ["Missing / repeat identified entry events", "3,549 / 22,468", "REVIEW · rows are events, not attendees"],
    ["Entry IDs found in customer map", "0", "BLOCKER · do not calculate conversion"],
  ];
  const table = slide.tables.add({
    rows: values.length,
    columns: 3,
    left: 72,
    top: 296,
    width: 1136,
    height: 314,
    columnWidths: [390, 175, 571],
    values,
  });
  table.styleOptions = { headerRow: true, bandedRows: false };
  table.borders.assign({ style: "solid", fill: MID, width: 1 });
  for (let row = 0; row < values.length; row += 1) {
    for (let col = 0; col < 3; col += 1) {
      const cell = table.getCell(row, col);
      cell.fill = row === 0 ? NAVY : (row % 2 === 0 ? PALE : WHITE);
      cell.text.style = {
        typeface: FONT,
        fontSize: row === 0 ? 17 : 16,
        bold: row === 0 || (col === 1 && row > 0),
        color: row === 0 ? WHITE : (row === 5 && col === 2 ? RED : INK),
        verticalAlignment: "middle",
        alignment: col === 1 ? "center" : "left",
        autoFit: "none",
        insets: { top: 5, right: 8, bottom: 5, left: 8 },
      };
    }
  }
  addText(slide, "Also blocked: EntryScans IDs have zero overlap with CustomerIDs.", { left: 72, top: 628, width: 800, height: 24 }, { fontSize: 18, bold: true, color: RED });
  slide.speakerNotes.textFrame.setText("Source: data_quality_summary.csv, store_entry_summary.csv, and unmatched_entry_checkpoints.csv. StoreEntries contains 20,603 unique IDs, 3,549 events with missing IDs, and 22,468 repeat identified events beyond the first per person/game. CustomerIDs has 16,747 exact duplicate rows. Arena EntryScans IDs also have zero overlap with CustomerIDs.");
}

// Slide 8 — action plan
{
  const slide = presentation.slides.add();
  addBase(slide, "Test, measure, then scale", 8, undefined, "Decision plan based on three observed games; causal lift is not yet measured.");
  const cards = [
    { x: 72, y: 170, n: "01", title: "Protect hour −1", action: "Pilot incremental staffing, replenishment, and queue coverage.", measure: "Revenue/min · wait · abandonment · stockouts", color: RED },
    { x: 656, y: 170, n: "02", title: "Test retail attach", action: "Randomize or phase a merchandise-plus-concessions prompt.", measure: "Exposure · lift · basket · margin · cannibalization", color: BLUE },
    { x: 72, y: 378, n: "03", title: "Diagnose the decline", action: "Explain the Game 3-to-Game 6 drop before choosing a remedy.", measure: "Attendance · open minutes · staffing · inventory · promo", color: NAVY },
    { x: 656, y: 378, n: "04", title: "Repair measurement", action: "Complete checkpoint mapping and create a governed identity bridge.", measure: "Match rate · consent · retention · event definition", color: RED },
  ];
  for (const card of cards) {
    addShape(slide, "roundRect", { left: card.x, top: card.y, width: 552, height: 176 }, WHITE, { style: "solid", fill: MID, width: 1 }, 18).shadow = "shadow-sm";
    addShape(slide, "roundRect", { left: card.x + 22, top: card.y + 22, width: 58, height: 42 }, card.color, { fill: "none", width: 0 }, 10);
    addText(slide, card.n, { left: card.x + 22, top: card.y + 29, width: 58, height: 24 }, { fontSize: 18, bold: true, color: WHITE, alignment: "center" });
    addText(slide, card.title, { left: card.x + 98, top: card.y + 22, width: 420, height: 34 }, { fontSize: 27, bold: true, color: NAVY });
    addText(slide, card.action, { left: card.x + 26, top: card.y + 78, width: 500, height: 48 }, { fontSize: 19, color: INK, lineSpacing: 1.05 });
    addText(slide, `MEASURE  ${card.measure}`, { left: card.x + 26, top: card.y + 139, width: 500, height: 22 }, { fontSize: 14, bold: true, color: card.color });
  }
  addShape(slide, "roundRect", { left: 72, top: 586, width: 1136, height: 64 }, PALE, { style: "solid", fill: MID, width: 1 }, 14);
  addText(slide, "BOUNDARY", { left: 96, top: 607, width: 110, height: 20 }, { fontSize: 14, bold: true, color: RED });
  addText(slide, "3 games  •  net sales ≠ profit  •  no attendance, margin, inventory, queue, staffing, or exposure fields", { left: 216, top: 603, width: 950, height: 28 }, { fontSize: 18, bold: true, color: NAVY });
  slide.speakerNotes.textFrame.setText("Recommendations are test designs, not claims of causal impact. Required instrumentation: experiment exposure, attendance, operating minutes, staffing, wait time, abandonment, inventory/stockouts, promotions, cost, and margin.");
}

await fs.mkdir(TMP_DIR, { recursive: true });
await fs.mkdir(path.dirname(FINAL_PPTX), { recursive: true });
const stagingDir = path.join(TMP_DIR, "finalizer");
await fs.mkdir(stagingDir, { recursive: true });
const candidatePath = path.join(stagingDir, "intuit_dome_arena_store_analysis.candidate.pptx");
await (await PresentationFile.exportPptx(presentation)).save(candidatePath);
await setCoreProperties(candidatePath);

const requirements = {
  explicitTotalSlideCount: 8,
  requiredNativeTableOwnerSlides: [7],
  requiredNativeChartOwnerSlides: [3, 4, 5, 6],
  materializeLiteralChartWorkbooks: true,
};
const fontPolicy = { basis: "design", families: [FONT] };
const expectedSlideSizeEmu = "12192000,6858000";

const result = await finalizePresentation({
  ...requirements,
  workspaceDir,
  candidatePath,
  finalPath: FINAL_PPTX,
  pythonExecutable: RUNTIME_PYTHON,
  integrityValidatorPath: path.join(SKILL_DIR, "container_tools/inspect_presentation_package_integrity.py"),
  layoutValidatorPath: path.join(SKILL_DIR, "container_tools/inspect_presentation_layout_geometry.py"),
  layoutArgs: [
    "--expected-slide-size-emu", expectedSlideSizeEmu,
    "--validate-bullet-geometry",
    "--validate-heading-fit",
    "--require-native-table-slide", "7",
  ],
  requiredNativeTableOwnerSlides: requirements.requiredNativeTableOwnerSlides,
  fontPolicy,
  verifyArtifactToolImport: true,
  receiptPath: path.join(TMP_DIR, `${path.basename(FINAL_PPTX)}.validation.json`),
});

console.log(JSON.stringify({ finalPath: FINAL_PPTX, validation: result }, null, 2));
