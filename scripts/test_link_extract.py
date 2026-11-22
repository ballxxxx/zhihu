# -*- coding: utf-8 -*-
"""识图取链 HTTP 测试:上传测试图 → 期待识别出链接;传非图片 → 400。"""
import httpx

BASE = "http://127.0.0.1:8000"
IMG = "D:/claude code projects/screen-link/scripts/test_screen.png"

with open(IMG, "rb") as f:
    r = httpx.post(
        f"{BASE}/api/life/link-extract",
        files={"file": ("test.png", f, "image/png")},
        timeout=180,
    )
print("图片 status:", r.status_code)
d = r.json()
print("count:", d.get("count"), "links:", d.get("links"))

# 边界:非图片文件
r2 = httpx.post(
    f"{BASE}/api/life/link-extract",
    files={"file": ("a.txt", b"hello", "text/plain")},
    timeout=30,
)
print("非图片 status:", r2.status_code, r2.text[:150])
