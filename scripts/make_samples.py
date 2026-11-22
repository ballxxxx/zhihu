# -*- coding: utf-8 -*-
"""生成高数样例课件(txt / docx / pdf 三格式),供解析与管线测试使用。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import config

CONTENT = """高等数学(上)期末复习课件

第一章 函数与极限

§1.1 函数

函数定义:设 D 是非空实数集,若对每个 x∈D,按确定法则 f 有唯一 y 与之对应,则称 f 为定义在 D 上的函数,y=f(x)。D 称为定义域,f(D) 称为值域。
基本初等函数:幂函数、指数函数、对数函数、三角函数、反三角函数。
复合函数:y=f(u), u=g(x), 若 g 的值域与 f 的定义域交集非空,则 y=f(g(x)) 为复合函数。
初等函数:由基本初等函数经有限次四则运算与复合构成的函数。
有界性、单调性、奇偶性、周期性是函数的四大基本性质,判断单调性常用定义法或导数法。

§1.2 数列与函数的极限

数列极限定义(ε-N):lim(n→∞) x_n = a,若对任意 ε>0,存在正整数 N,当 n>N 时恒有 |x_n-a|<ε。
函数极限定义(ε-δ):lim(x→x0) f(x) = A,若对任意 ε>0,存在 δ>0,当 0<|x-x0|<δ 时恒有 |f(x)-A|<ε。
极限四则运算法则:两函数极限均存在时,和差积商的极限等于极限的和差积商(分母极限不为零)。
两个重要极限:
lim(x→0) sinx/x = 1
lim(x→∞) (1+1/x)^x = e
夹逼准则:若 g(x)≤f(x)≤h(x) 且 lim g = lim h = A,则 lim f = A。
单调有界准则:单调有界数列必有极限。
极限存在的充要条件:左右极限存在且相等。

§1.3 无穷小与无穷大

无穷小:极限为零的变量。有限个无穷小的和、积仍为无穷小;无穷小与有界函数的乘积是无穷小。
无穷小比较:设 α、β 是同一过程中的无穷小。
若 lim β/α = 0,称 β 是 α 的高阶无穷小;
若 lim β/α = ∞,称 β 是 α 的低阶无穷小;
若 lim β/α = c(非零常数),称二者为同阶无穷小;
若 lim β/α = 1,称二者为等价无穷小,记 α~β。
等价无穷小替换(x→0):
sinx~x, tanx~x, arcsinx~x, arctanx~x,
1-cosx~x²/2, ln(1+x)~x, e^x-1~x, (1+x)^a-1~ax。
注意:等价无穷小替换只能用于乘除因子,不能用于加减项,否则易出错。
无穷大:绝对值无限增大的变量。无穷大与无穷小互为倒数关系。

§1.4 函数的连续性

连续定义:lim(x→x0) f(x) = f(x0),即函数在点 x0 处有定义、极限存在且等于函数值。
间断点分类:
可去间断点:左右极限存在相等但不等于函数值(或函数在该点无定义);
跳跃间断点:左右极限存在但不相等;
无穷间断点:极限为无穷大;
振荡间断点:极限不存在且振荡(如 sin(1/x) 在 x=0 处)。
闭区间上连续函数的性质:
最值定理:闭区间上连续函数必有最大值与最小值;
介值定理:闭区间上连续函数可取到介于两端函数值之间的任意值;
零点定理:若 f(a)·f(b)<0,则 (a,b) 内至少存在一点 ξ 使 f(ξ)=0。

高频考点提示:
1. 求极限的方法:重要极限、等价无穷小替换、有理化、夹逼准则、洛必达法则;
2. 间断点类型的判断(常考选择/填空);
3. 零点定理证明方程根的存在性(常考证明题);
4. 无穷小比较与等价无穷小的正确使用(常考计算题陷阱)。
"""


def write_txt(path: Path) -> None:
    path.write_text(CONTENT, encoding="utf-8")


def write_docx(path: Path) -> None:
    from docx import Document

    doc = Document()
    for para in CONTENT.split("\n\n"):
        if para.startswith(("§", "高频")):
            doc.add_heading(para.strip(), level=2)
        elif para.strip().startswith(("第一章", "高等数学")):
            doc.add_heading(para.strip(), level=1)
        else:
            doc.add_paragraph(para.strip())
    doc.save(str(path))


def write_pdf(path: Path) -> None:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

    pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    styles = getSampleStyleSheet()
    body = ParagraphStyle("body", parent=styles["BodyText"], fontName="STSong-Light", fontSize=11, leading=18)

    doc = SimpleDocTemplate(str(path), pagesize=A4)
    story = []
    for para in CONTENT.split("\n\n"):
        story.append(Paragraph(para.replace("\n", "<br/>"), body))
        story.append(Spacer(1, 8))
    doc.build(story)


if __name__ == "__main__":
    out_dir = config.DATA_DIR / "samples"
    out_dir.mkdir(exist_ok=True)
    write_txt(out_dir / "高等数学第一章课件.txt")
    write_docx(out_dir / "高等数学第一章课件.docx")
    write_pdf(out_dir / "高等数学第一章课件.pdf")
    print(f"samples -> {out_dir}")
    for f in sorted(out_dir.iterdir()):
        print(f"  {f.name} ({f.stat().st_size} bytes)")
