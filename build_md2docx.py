# -*- coding: utf-8 -*-
"""极简 markdown -> docx 转换器(支持标题/段落/表格/列表/代码块/加粗)"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn


def set_run(run, size=11, bold=False, mono=False):
    run.font.size = Pt(size)
    run.font.bold = bold
    if mono:
        run.font.name = 'Consolas'
    else:
        run.font.name = 'Times New Roman'
        run._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')


def add_rich(doc, text, size=11, indent=None):
    p = doc.add_paragraph()
    if indent:
        p.paragraph_format.left_indent = Pt(indent)
    # 处理 **加粗**
    parts = text.split('**')
    for i, part in enumerate(parts):
        if part:
            r = p.add_run(part)
            set_run(r, size, bold=(i % 2 == 1))
    return p


def convert(md_path, docx_path):
    doc = Document()
    with open(md_path, encoding='utf-8') as f:
        lines = f.read().splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith('```'):
            i += 1
            code = []
            while i < len(lines) and not lines[i].startswith('```'):
                code.append(lines[i])
                i += 1
            i += 1
            p = doc.add_paragraph()
            r = p.add_run('\n'.join(code))
            set_run(r, 9, mono=True)
            continue
        if line.startswith('|'):
            rows = [line]
            i += 1
            while i < len(lines) and lines[i].startswith('|'):
                if not all(c in '-: |' for c in lines[i]):
                    rows.append(lines[i])
                i += 1
            t = doc.add_table(rows=len(rows), cols=rows[0].count('|') - 1)
            t.style = 'Table Grid'
            for ri, row in enumerate(rows):
                cells = [c.strip() for c in row.strip('|').split('|')]
                for ci, cell in enumerate(cells[:rows[0].count('|') - 1]):
                    c = t.cell(ri, ci)
                    c.text = ''
                    for pi, part in enumerate(cell.split('**')):
                        if part:
                            set_run(c.paragraphs[0].add_run(part), 9.5, bold=(pi % 2 == 1) or ri == 0)
            continue
        if line.startswith('# '):
            p = doc.add_paragraph()
            set_run(p.add_run(line[2:]), 16, bold=True)
        elif line.startswith('## '):
            p = doc.add_paragraph()
            set_run(p.add_run(line[3:]), 13, bold=True)
        elif line.startswith('### '):
            p = doc.add_paragraph()
            set_run(p.add_run(line[4:]), 11.5, bold=True)
        elif line.startswith('- '):
            add_rich(doc, line[2:], indent=12)
        elif line.strip():
            add_rich(doc, line)
        i += 1
    doc.save(docx_path)
    print(f'OK: {docx_path}')


if __name__ == '__main__':
    convert(sys.argv[1], sys.argv[2])
