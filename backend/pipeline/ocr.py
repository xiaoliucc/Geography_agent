"""
扫描件 OCR 处理管道（Qwen-VL）

输出结构对齐原 PaddleOCRVL 项目:
    pdf_extracted/
    ├── pages/page_N.json     ← 每页结构化识别结果
    ├── markdown/page_N.md    ← 每页 Markdown
    ├── images/               ← Qwen-VL 引用的图片不可提取（API限制），保留目录
    └── full_pages/page_N.png ← 整页渲染图（用 generate_full_pages.py 生成）

用法:
    python pipeline_ocr.py <pdf_path> <output_dir> [start_page] [end_page]
"""

import os, sys, base64, json, time, fitz
from pipeline import ask
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
fitz.TOOLS.mupdf_warnings(False)


def render_page(pdf_path: str, page_num: int, scale: float = 1.5) -> str:
    """渲染 PDF 单页为 PNG base64"""
    doc = fitz.open(pdf_path)
    page = doc[page_num - 1]
    pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale))
    doc.close()
    return base64.b64encode(pix.tobytes("png")).decode()


_OCR_PROMPT = (
    "请提取这张教材页面中的所有文字内容。\n"
    "输出 JSON：\n"
    '{"title": "章节标题", "blocks": ['
    '{"label": "paragraph_title|text|figure_title|table", "content": "文字"}, ...'
    '], "images": [{"bbox": [x0,y0,x1,y1], "description": "简述"}, ...]}'
    "\n保持原文结构，地图/示意图/表格标注 bbox，不要添加解释"
)


def ocr_page(image_b64: str) -> dict:
    content = ask(_OCR_PROMPT, image_b64, max_tokens=3000)
    return _parse_ocr_response(content)


def _parse_ocr_response(raw: str) -> dict:
    """解析 Qwen-VL 返回的 JSON（可能被 markdown 包裹）"""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
        if raw.endswith("```"):
            raw = raw[:-3]
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # 回退：全部当文本
        return {"title": "", "blocks": [{"label": "text", "content": raw}], "images": []}


def page_json_to_markdown(page_data: dict, page_num: int) -> str:
    """将结构化 JSON 转为 Markdown"""
    lines = []
    title = page_data.get("title", "")
    if title:
        lines.append(f"## {title}\n")

    for b in page_data.get("blocks", []):
        label = b.get("label", "text")
        content = b.get("content", "")
        if not content:
            continue
        if label == "paragraph_title":
            lines.append(f"### {content}\n")
        elif label == "table":
            lines.append(f"```\n{content}\n```\n")
        else:
            lines.append(f"{content}\n")

    for i, img in enumerate(page_data.get("images", [])):
        desc = img.get("description", "图片")
        lines.append(f"> 📷 图片 {i+1}: {desc}\n")

    return "\n".join(lines)


def process(pdf_path: str, output_dir: str, start_page: int = 1, end_page: int = None):
    """处理扫描件 PDF → pages/*.json + markdown/*.md"""
    pages_dir = os.path.join(output_dir, "pages")
    md_dir = os.path.join(output_dir, "markdown")
    images_dir = os.path.join(output_dir, "images")
    for d in [pages_dir, md_dir, images_dir]:
        os.makedirs(d, exist_ok=True)

    doc = fitz.open(pdf_path)
    total = len(doc)
    if end_page is None:
        end_page = total
    doc.close()

    pages_data = []
    for page_num in range(start_page, min(end_page, total) + 1):
        print(f"  OCR {page_num}/{total}...", end=" ", flush=True)
        start = time.time()

        try:
            img_b64 = render_page(pdf_path, page_num)
            parsed = ocr_page(img_b64)
            elapsed = time.time() - start

            # 保存 page_N.json
            json_path = os.path.join(pages_dir, f"page_{page_num}.json")
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(parsed, f, ensure_ascii=False, indent=2)

            # 保存 page_N.md
            md = page_json_to_markdown(parsed, page_num)
            md_path = os.path.join(md_dir, f"page_{page_num}.md")
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(md)

            text = md.replace("#", "").replace("*", "").replace("`", "").strip()
            pages_data.append({
                "page_num": page_num,
                "title": parsed.get("title", ""),
                "content": text,
                "image_count": len(parsed.get("images", [])),
            })
            print(f"OK ({len(text)}字, {elapsed:.1f}s)")

        except Exception as e:
            print(f"失败: {e}")

        time.sleep(0.5)

    # 索引文件
    index = {
        "source": pdf_path,
        "total_pages": total,
        "processed_pages": len(pages_data),
        "pages": pages_data,
    }
    with open(os.path.join(output_dir, "index.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    print(f"\n✅ OCR 完成: {len(pages_data)}/{total} 页")
    return pages_data


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python pipeline_ocr.py <pdf_path> <output_dir> [start] [end]")
        sys.exit(1)

    pdf_path = sys.argv[1]
    output_dir = sys.argv[2]
    start = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    end = int(sys.argv[4]) if len(sys.argv) > 4 else None

    if not os.path.exists(pdf_path):
        print(f"PDF 不存在: {pdf_path}")
        sys.exit(1)

    print(f"📄 {pdf_path}\n📁 {output_dir}\n")
    process(pdf_path, output_dir, start, end)
