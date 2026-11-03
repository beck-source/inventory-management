// CSV export utilities
const BOM = "﻿";
const EOL = "\r\n";
const FORMULA_TRIGGERS = /^[=+\-@\t\r]/;

// Escape a single cell. Numbers are written as-is; text is guarded against
// formula injection and quoted when it contains a delimiter, quote or newline.
function escapeCell(value) {
  if (value === null || value === undefined) return "";
  if (typeof value === "number")
    return Number.isFinite(value) ? String(value) : "";

  let text = String(value);
  if (FORMULA_TRIGGERS.test(text)) text = `'${text}`;
  if (/[",\r\n]/.test(text)) text = `"${text.replace(/"/g, '""')}"`;
  return text;
}

export function toCsv(headers, rows) {
  const lines = [headers, ...rows].map((row) => row.map(escapeCell).join(","));
  return BOM + lines.join(EOL) + EOL;
}

export function downloadCsv(filename, csvString) {
  const blob = new Blob([csvString], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.style.display = "none";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
