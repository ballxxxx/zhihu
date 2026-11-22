# -*- coding: utf-8 -*-
"""识图取链:从图片中提取可跳转链接(文字网址 OCR + 二维码识别)。

网页功能(D7):参谋页粘贴截图(Ctrl+V)或上传图片 → 返回链接清单。
核心逻辑与本地工具 screen-link/grab.py 同源。
"""
import re

from PIL import Image

# 全角 → 半角(OCR 常把网址字符读成全角)
_FULLWIDTH = str.maketrans(
    "：．／－＿～（）！？，",
    ":./-_~()!?,",
)

# OCR 常把 https 误读成 htps/httpa/htts 等
_SCHEME_FIXES = {
    "htps": "https", "httpa": "https", "htts": "https",
    "htp": "http", "hps": "https", "ttp": "http",
}

# 带协议的完整 URL;截止于空白/中文/常见全角标点
URL_RE = re.compile(
    r"https?://[^\s　一-鿿，。；、！？【】（）「」『』\"'<>]+"
)
# 裸域名短链(b23.tv/xxx 等):首标签必须字母开头,数字开头的 OCR 噪音自动排除
BARE_URL_RE = re.compile(
    r"[A-Za-z][\w-]*(?:\.[\w-]+)*\.(?:com|cn|tv|net|org|cc|xyz|io|me|top"
    r"|live|app|moe|club|shop|store|link|dev|space|site)"
    r"(?:/[^\s　一-鿿，。；、！？【】（）「」『』\"'<>]*)?"
)

_ocr_engine = None


def _normalize(text: str) -> str:
    text = text.translate(_FULLWIDTH)
    text = re.sub(r"\s+", "", text)  # OCR 常在网址里插空格
    for bad, good in _SCHEME_FIXES.items():
        text = re.sub(rf"(?<![A-Za-z]){bad}(?=:?//)", good, text)
    return text


def _clean_url(url: str) -> str:
    """去掉 OCR 误粘在末尾的标点。"""
    return url.rstrip(".,;:!?()[]{}|\\'\"<>")


def _trim_noise(url: str) -> str:
    """剪掉 OCR 噪音前缀:首标签含数字时(如把中文误读成 a1a88www),
    只保留最后 3 个标签。正常域名首标签为纯字母,不受影响。"""
    host, _, rest = url.partition("/")
    labels = host.split(".")
    if len(labels) > 3 and re.search(r"\d", labels[0]):
        return ".".join(labels[-3:]) + ("/" + rest if rest else "")
    return url


def _ocr_lines(img: Image.Image) -> list[tuple[str, float]]:
    """RapidOCR 识别文字,返回 [(文本, 置信度)]。引擎单例,避免重复加载模型。"""
    global _ocr_engine
    import numpy as np
    from rapidocr_onnxruntime import RapidOCR

    if _ocr_engine is None:
        _ocr_engine = RapidOCR()
    result, _ = _ocr_engine(np.array(img))
    return [(item[1], item[2]) for item in (result or [])]


def _text_links(img: Image.Image) -> list[str]:
    """从 OCR 文本行提取网址(完整 URL + 裸域名短链)。

    只做行内匹配:跨行拼接会粘连出假链接(自动打开错误网址比漏识别更糟)。
    """
    links: list[str] = []
    for line, _score in _ocr_lines(img):
        s = _normalize(str(line))
        for m in URL_RE.finditer(s):
            links.append(_clean_url(m.group(0)))
        # 裸域名:排除已被完整 URL 覆盖的部分
        for m in BARE_URL_RE.finditer(s):
            candidate = _trim_noise(_clean_url(m.group(0)))
            if not any(candidate in l for l in links):
                links.append("https://" + candidate)
    return links


def _qr_links(img: Image.Image) -> list[str]:
    """识别图片里的二维码:多码→单码→灰度二值化三道兜底,返回 http(s) 链接。"""
    try:
        import cv2
        import numpy as np
    except ImportError:
        return []
    arr = np.array(img.convert("RGB"))[:, :, ::-1]  # PIL RGB → BGR
    detector = cv2.QRCodeDetector()
    results: list[str] = []
    try:
        ok, decoded, _points, _straight = detector.detectAndDecodeMulti(arr)
        if ok and decoded:
            results.extend(d for d in decoded if isinstance(d, str))
    except Exception:
        pass
    if not results:
        try:
            d2, _p2, _s2 = detector.detectAndDecode(arr)
            if d2 and isinstance(d2, str):
                results.append(d2)
        except Exception:
            pass
    if not results:
        # 视频截图里的二维码常低对比度,灰度 + OTSU 二值化再试
        try:
            gray = cv2.cvtColor(arr, cv2.COLOR_BGR2GRAY)
            _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            d3, _p3, _s3 = detector.detectAndDecode(th)
            if d3 and isinstance(d3, str):
                results.append(d3)
        except Exception:
            pass
    return [d for d in results if d.startswith(("http://", "https://"))]


def extract_links(img: Image.Image) -> list[dict]:
    """主入口:返回 [{"url": ..., "source": "文字"|"二维码"}, ...],去重保序。"""
    out: list[dict] = []
    seen: set[str] = set()
    for url in _text_links(img):
        if url not in seen:
            seen.add(url)
            out.append({"url": url, "source": "文字"})
    for url in _qr_links(img):
        if url not in seen:
            seen.add(url)
            out.append({"url": url, "source": "二维码"})
    return out
