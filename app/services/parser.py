# -*- coding: utf-8 -*-
"""文档解析:PDF / Word / txt → 纯文本。

统一入口 parse_file(path):按扩展名自动分发。
图片 OCR 在 D3 加入。
"""
from pathlib import Path


class ParseError(RuntimeError):
    pass


def parse_pdf(path: str | Path) -> str:
    """pdfplumber 提取 PDF 文本层(扫描件需 OCR,D3 处理)。"""
    try:
        import pdfplumber
    except ImportError as exc:  # pragma: no cover
        raise ParseError("缺少 pdfplumber,请先安装依赖") from exc
    parts: list[str] = []
    try:
        with pdfplumber.open(str(path)) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                if text.strip():
                    parts.append(text)
    except Exception as exc:
        raise ParseError(f"PDF 解析失败 {path}: {exc}") from exc
    if not parts:
        raise ParseError(f"PDF 未提取到文本(可能是扫描件,需要 OCR): {path}")
    return "\n\n".join(parts)


def parse_docx(path: str | Path) -> str:
    """python-docx 提取段落与表格文本。"""
    try:
        from docx import Document
    except ImportError as exc:  # pragma: no cover
        raise ParseError("缺少 python-docx,请先安装依赖") from exc
    try:
        doc = Document(str(path))
    except Exception as exc:
        raise ParseError(f"Word 解析失败 {path}: {exc}") from exc
    lines: list[str] = []
    for para in doc.paragraphs:
        if para.text.strip():
            lines.append(para.text.strip())
    for table in doc.tables:
        for row in table.rows:
            cells = [c.text.strip() for c in row.cells if c.text.strip()]
            if cells:
                lines.append(" | ".join(cells))
    return "\n".join(lines)


def parse_txt(path: str | Path) -> str:
    """txt 按 utf-8 / gbk 顺序尝试解码。"""
    raw = Path(path).read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "gbk"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ParseError(f"txt 编码无法识别: {path}")


_ocr_engine = None


def parse_image(path: str | Path) -> str:
    """图片 OCR(RapidOCR,自带中文模型)。引擎为单例,避免重复加载模型。"""
    global _ocr_engine
    try:
        from rapidocr_onnxruntime import RapidOCR
    except ImportError as exc:  # pragma: no cover
        raise ParseError("缺少 rapidocr-onnxruntime,请先安装依赖") from exc
    if _ocr_engine is None:
        _ocr_engine = RapidOCR()
    try:
        result, _ = _ocr_engine(str(path))
    except Exception as exc:
        raise ParseError(f"图片 OCR 失败 {path}: {exc}") from exc
    if not result:
        raise ParseError(f"图片未识别到文字(可能模糊或无文字): {path}")
    return "\n".join(item[1] for item in result)


def parse_file(path: str | Path) -> str:
    """按扩展名分发解析。返回纯文本。"""
    suffix = Path(path).suffix.lower()
    handlers = {
        ".pdf": parse_pdf,
        ".docx": parse_docx,
        ".doc": None,  # 老格式 .doc 暂不支持,提示转存 docx
        ".txt": parse_txt,
        ".md": parse_txt,
        ".png": parse_image,
        ".jpg": parse_image,
        ".jpeg": parse_image,
        ".bmp": parse_image,
        ".webp": parse_image,
    }
    if suffix not in handlers:
        raise ParseError(f"不支持的文件类型: {suffix}(支持 pdf/docx/txt/md/png/jpg)")
    if handlers[suffix] is None:
        raise ParseError("暂不支持 .doc 老格式,请另存为 .docx 后上传")
    return handlers[suffix](path)
