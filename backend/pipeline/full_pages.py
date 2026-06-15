"""
生成全页教材图片（前端 PDF 查看器用）
    python generate_full_pages.py <pdf_path> <output_dir>
"""

import os
import sys
import fitz

fitz.TOOLS.mupdf_warnings(False)


def generate(pdf_path: str, output_dir: str, scale: float = 2.0):
    """渲染所有页面为 PNG"""
    full_pages_dir = os.path.join(output_dir, "full_pages")
    os.makedirs(full_pages_dir, exist_ok=True)

    doc = fitz.open(pdf_path)
    total = len(doc)
    for i, page in enumerate(doc):
        page_num = i + 1
        pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale))
        out_path = os.path.join(full_pages_dir, f"page_{page_num}.png")
        pix.save(out_path)
        if (i + 1) % 10 == 0:
            print(f"  {i + 1}/{total}")

    doc.close()
    print(f"✅ {total} 页 → {full_pages_dir}/")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python generate_full_pages.py <pdf_path> <output_dir>")
        sys.exit(1)
    generate(sys.argv[1], sys.argv[2])
