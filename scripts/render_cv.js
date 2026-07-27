// nova CV renderer — ATS-safe house style.
//
// CONTENT is hand-authored per application and arrives as JSON; this file only STYLES it.
// That separation is deliberate: template-driven content generation is what makes crafted CVs
// read as machine-written. Single column, real text, standard headings, no tables in the parse
// path — see references/ats-rules.md.
//
// Input JSON:
//   { name, title, contact, summary,
//     experience: [{ title, company, dates, bullets: [] }],
//     skills:     [{ label, items }],
//     education:  [{ inst, degree, dates }],
//     projects:   [],                     // optional
//     certs:      [{ name, issuer, date }] // optional
//   }
// Bullets support **bold** inline.
//
// Usage: node render_cv.js input.json output.docx
const fs = require('fs');
const {
  Document, Packer, Paragraph, TextRun, TabStopType, TabStopPosition,
  BorderStyle, AlignmentType, LevelFormat, Numbering
} = require('docx');

const IN = process.argv[2];
const OUT = process.argv[3];
const data = JSON.parse(fs.readFileSync(IN, 'utf8'));

const FONT = 'Calibri';
const ACCENT = '2E7D8A';   // teal role subtitle
const GREY = '555555';
const RULE = 'AAAAAA';
const CONTENT_W = 10466;   // A4 minus 720 twip margins each side

function sectionHeading(text) {
  return new Paragraph({
    spacing: { before: 52, after: 16 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: RULE, space: 1 } },
    children: [ new TextRun({ text: text.toUpperCase(), bold: true, size: 20, font: FONT, characterSpacing: 20, color: '1A1A1A' }) ],
  });
}

function titleDateRow(title, dates) {
  return new Paragraph({
    tabStops: [{ type: TabStopType.RIGHT, position: CONTENT_W }],
    spacing: { before: 52, after: 0 },
    children: [
      new TextRun({ text: title, bold: true, size: 21, font: FONT }),
      new TextRun({ text: '\t' + (dates || ''), size: 19, font: FONT, color: GREY }),
    ],
  });
}

function subItalic(text) {
  return new Paragraph({
    spacing: { after: 10 },
    children: [ new TextRun({ text, italics: true, size: 20, font: FONT, color: '333333' }) ],
  });
}

function bullet(text) {
  return new Paragraph({
    numbering: { reference: 'bl', level: 0 },
    spacing: { after: 8, line: 216, lineRule: 'auto' },
    children: renderRuns(text),
  });
}

// support **bold** inline
function renderRuns(text, base = {}) {
  const runs = [];
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  for (const p of parts) {
    if (!p) continue;
    if (p.startsWith('**') && p.endsWith('**')) {
      runs.push(new TextRun({ text: p.slice(2, -2), bold: true, size: 20, font: FONT, ...base }));
    } else {
      runs.push(new TextRun({ text: p, size: 20, font: FONT, ...base }));
    }
  }
  return runs;
}

const children = [];

// Header
children.push(new Paragraph({
  spacing: { after: 0 },
  children: [ new TextRun({ text: data.name, bold: true, size: 40, font: FONT, color: '1A1A1A' }) ],
}));
children.push(new Paragraph({
  spacing: { after: 30 },
  children: [ new TextRun({ text: data.title, size: 22, font: FONT, color: ACCENT }) ],
}));
children.push(new Paragraph({
  spacing: { after: 40 },
  children: [ new TextRun({ text: data.contact, size: 18, font: FONT, color: GREY }) ],
}));

// Summary
children.push(sectionHeading('Summary'));
children.push(new Paragraph({
  spacing: { after: 22, line: 220, lineRule: 'auto' },
  children: renderRuns(data.summary),
}));

// Experience
children.push(sectionHeading('Experience'));
for (const job of data.experience) {
  children.push(titleDateRow(job.title, job.dates));
  children.push(subItalic(job.company));
  for (const b of job.bullets) children.push(bullet(b));
}

// Skills
children.push(sectionHeading('Skills'));
for (const s of data.skills) {
  children.push(new Paragraph({
    spacing: { after: 16, line: 216, lineRule: 'auto' },
    children: [
      new TextRun({ text: s.label + ': ', bold: true, size: 20, font: FONT }),
      new TextRun({ text: s.items, size: 20, font: FONT }),
    ],
  }));
}

// Education
children.push(sectionHeading('Education'));
for (const e of data.education) {
  children.push(titleDateRow(e.inst, e.dates));
  children.push(subItalic(e.degree));
}

// Projects
if (data.projects && data.projects.length) {
  children.push(sectionHeading('Projects'));
  for (const p of data.projects) children.push(bullet(p));
}

// Certifications
if (data.certs && data.certs.length) {
  children.push(sectionHeading('Certifications'));
  for (const c of data.certs) {
    children.push(new Paragraph({
      tabStops: [{ type: TabStopType.RIGHT, position: CONTENT_W }],
      spacing: { after: 12 },
      children: [
        new TextRun({ text: c.name + ' — ' + c.issuer, size: 19, font: FONT }),
        new TextRun({ text: '\t' + c.date, size: 19, font: FONT, color: GREY }),
      ],
    }));
  }
}

const doc = new Document({
  numbering: {
    config: [{
      reference: 'bl',
      levels: [{
        level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 216, hanging: 180 } }, run: { size: 20, font: FONT } },
      }],
    }],
  },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 380, bottom: 300, left: 720, right: 720 } } },
    children,
  }],
});

Packer.toBuffer(doc).then((buf) => { fs.writeFileSync(OUT, buf); console.log('wrote', OUT); });
