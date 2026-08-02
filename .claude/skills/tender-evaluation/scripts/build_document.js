#!/usr/bin/env node
/*
 * build_document.js — build a formatted Word document from a JSON spec.
 *
 * Written for procurement correspondence: a title block, section headings,
 * sub-headings, justified body paragraphs and bulleted lists. Driving it from
 * JSON rather than hand-writing a script per vendor is what stops the general
 * section drifting between copies when there are five of them.
 *
 *   node build_document.js spec.json
 *
 * Spec format:
 * {
 *   "output":   "/path/to/Clarification_Requirements_Vendor.docx",
 *   "title":    "IKEJA CITY MALL — FIRE DETECTION AND ALARM SYSTEM OVERHAUL",
 *   "subtitle": "Clarification Requirements — Vendor Name",
 *   "docTitle": "Clarification Requirements — Vendor Name",   // optional, file metadata
 *   "blocks": [
 *     { "type": "section", "text": "SECTION A — GENERAL REQUIREMENTS" },
 *     { "type": "heading", "text": "A1. Revised quotation" },
 *     { "type": "body",    "text": "Please re-submit..." },
 *     { "type": "bullet",  "text": "the exact product model;" },
 *     { "type": "bullet",  "text": "the product code.", "gap": true }
 *   ]
 * }
 *
 * "gap": true adds extra space after a bullet — use it on the last bullet of a
 * list that is followed by more body text, so the paragraph does not crowd the
 * list above it.
 *
 * Requires the `docx` npm package: npm install docx
 */

const fs = require('fs');
const path = require('path');

// Node resolves modules relative to this file, but `npm install docx` is
// usually run in whatever directory the work is happening in. Try both, so the
// script works from a scratch directory without being copied there first.
function loadDocx() {
  try {
    return require('docx');
  } catch (err) {
    try {
      const { createRequire } = require('module');
      return createRequire(path.join(process.cwd(), 'index.js'))('docx');
    } catch (_) {
      throw new Error(
        'the "docx" package was not found next to this script or in ' +
        `${process.cwd()} — run: npm install docx`
      );
    }
  }
}

const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  BorderStyle, LevelFormat, convertInchesToTwip,
} = loadDocx();

const FONT = 'Calibri';
const BULLET_REF = 'dash-list';

const primitives = {
  title: (text) => new Paragraph({
    spacing: { after: 60 },
    children: [new TextRun({ text, bold: true, size: 26, font: FONT, color: '1A1A1A' })],
  }),

  subtitle: (text) => new Paragraph({
    spacing: { after: 240 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 6, space: 8, color: '999999' } },
    children: [new TextRun({ text, size: 22, font: FONT, color: '444444' })],
  }),

  section: (text) => new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 360, after: 160 },
    children: [new TextRun({ text, bold: true, size: 24, font: FONT, color: '1A1A1A' })],
  }),

  heading: (text) => new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 240, after: 100 },
    keepNext: true,
    children: [new TextRun({ text, bold: true, size: 22, font: FONT, color: '1A1A1A' })],
  }),

  body: (text) => new Paragraph({
    spacing: { after: 140 },
    alignment: AlignmentType.JUSTIFIED,
    children: [new TextRun({ text, size: 22, font: FONT })],
  }),

  bullet: (text, gap) => new Paragraph({
    numbering: { reference: BULLET_REF, level: 0 },
    spacing: { after: gap ? 160 : 60 },
    children: [new TextRun({ text, size: 22, font: FONT })],
  }),
};

function buildChildren(spec) {
  const children = [];
  if (spec.title) children.push(primitives.title(spec.title));
  if (spec.subtitle) children.push(primitives.subtitle(spec.subtitle));

  for (const [i, block] of (spec.blocks || []).entries()) {
    const fn = primitives[block.type];
    if (!fn) throw new Error(`block ${i}: unknown type "${block.type}"`);
    if (typeof block.text !== 'string' || !block.text.trim()) {
      throw new Error(`block ${i} (${block.type}): missing text`);
    }
    children.push(block.type === 'bullet' ? fn(block.text, block.gap) : fn(block.text));
  }
  return children;
}

function buildDocument(spec) {
  return new Document({
    creator: spec.creator || 'Tender evaluation',
    title: spec.docTitle || spec.subtitle || spec.title || 'Document',
    description: spec.description || '',
    numbering: {
      config: [{
        reference: BULLET_REF,
        levels: [{
          level: 0,
          format: LevelFormat.BULLET,
          text: '–',
          alignment: AlignmentType.LEFT,
          style: {
            paragraph: {
              indent: {
                left: convertInchesToTwip(0.32),
                hanging: convertInchesToTwip(0.2),
              },
            },
            run: { font: FONT, size: 22 },
          },
        }],
      }],
    },
    sections: [{
      properties: {
        page: {
          margin: {
            top: convertInchesToTwip(0.9),
            bottom: convertInchesToTwip(0.9),
            left: convertInchesToTwip(1),
            right: convertInchesToTwip(1),
          },
        },
      },
      children: buildChildren(spec),
    }],
  });
}

async function main() {
  const specPath = process.argv[2];
  if (!specPath) {
    console.error('usage: node build_document.js <spec.json>');
    process.exit(1);
  }
  const spec = JSON.parse(fs.readFileSync(specPath, 'utf8'));
  const out = spec.output || process.argv[3];
  if (!out) throw new Error('spec has no "output" path');

  fs.mkdirSync(path.dirname(path.resolve(out)), { recursive: true });
  fs.writeFileSync(out, await Packer.toBuffer(buildDocument(spec)));
  console.log(`written: ${out}`);
}

if (require.main === module) {
  main().catch((err) => {
    console.error(`error: ${err.message}`);
    process.exit(1);
  });
}

module.exports = { primitives, buildDocument, buildChildren };
