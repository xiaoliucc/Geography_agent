"""
电子版教材增强导入 — PyMuPDF 文字 + 矢量图提取 + 标题匹配 + Qwen-VL 图描述

用法:
    python pipeline_digital_enhanced.py <pdf_path> <publisher> <book_name>

流程:
    PDF → PyMuPDF 提取正文（100%准确）
        → PyMuPDF 提取矢量图 xref → 渲染为 PNG
        → 识别图标题（"图X-X-X ..." 模式）
        → 位置匹配：标题 ↔ 图片
        → Qwen-VL 描述每张图
        → 图片描述作为独立 chunk 加入索引
"""

import os, sys, re, json, time, fitz, base64
from pipeline import ask
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
fitz.TOOLS.mupdf_warnings(False)


# ── 图标题识别 ──

FIGURE_PATTERN = re.compile(r"图\s*(\d+[-.]\d+[-.]\d+)\s*(.*)")

def is_figure_caption(text: str) -> tuple:
    """判断文本是否为图标题，返回 (编号, 描述) 或 None"""
    m = FIGURE_PATTERN.match(text.strip())
    if m:
        return (m.group(1), m.group(2).strip() or text.strip())
    return None


# ── 矢量图提取 ──

def extract_page_images(page) -> list[dict]:
    """从 PDF 页提取位图 + 检测非文字区域（矢量图）"""
    images = []

    # 1. 嵌入位图
    for img in page.get_image_info():
        xref = img.get("xref", 0)
        bbox = img.get("bbox", [])
        if xref and bbox:
            try:
                base = page.parent.extract_image(xref)
                images.append({
                    "xref": xref,
                    "bbox": bbox,
                    "width": img.get("width", 0),
                    "height": img.get("height", 0),
                    "ext": base.get("ext", "png"),
                    "image_bytes": base.get("image", b""),
                    "source": "embedded",
                })
            except Exception:
                pass

    # 2. 非文字区域（矢量图/表格/示意图）
    # 获取文字覆盖区域，找出无文字的大片空白 → 可能是图
    text_blocks = page.get_text("blocks")
    text_rects = [(b[0], b[1], b[2], b[3]) for b in text_blocks if b[4].strip()]

    if not text_rects:
        return images

    page_w = page.rect.width
    page_h = page.rect.height
    non_text_regions = _find_non_text_regions(text_rects, page_w, page_h)

    for region in non_text_regions:
        x0, y0, x1, y1 = region
        w, h = x1 - x0, y1 - y0
        # 过滤太小的区域（< 页面 10%）和太窄的（可能是页边距）
        if w < page_w * 0.1 or h < page_h * 0.05:
            continue
        # 渲染该区域为图片
        clip = fitz.Rect(x0, y0, x1, y1)
        pix = page.get_pixmap(clip=clip, matrix=fitz.Matrix(1.5, 1.5))
        images.append({
            "xref": 0,
            "bbox": [x0, y0, x1, y1],
            "width": pix.width,
            "height": pix.height,
            "ext": "png",
            "image_bytes": pix.tobytes("png"),
            "source": "vector_region",
        })

    return images


def _find_non_text_regions(text_rects: list, page_w: float, page_h: float) -> list:
    """找到页面上未被文字覆盖的区域（可能是图/表）"""
    # 简化版：按 y 坐标排序文字块，找到文字块之间的大间隙
    sorted_blocks = sorted(text_rects, key=lambda r: r[1])  # 按 y0 排序
    regions = []
    prev_bottom = 0
    margin = page_h * 0.05  # 5% 容差

    for rect in sorted_blocks:
        gap = rect[1] - prev_bottom
        if gap > page_h * 0.08:  # 超过 8% 页高算间隙
            regions.append([0, prev_bottom, page_w, rect[1]])
        prev_bottom = max(prev_bottom, rect[3])

    # 最后一块下面的区域
    if page_h - prev_bottom > page_h * 0.08:
        regions.append([0, prev_bottom, page_w, page_h])

    return regions


# ── 标题与图片关联 ──

def match_captions_to_images(text_blocks: list, images: list, page_num: int) -> list[dict]:
    """
    将图标题与图片按 y 坐标关联。
    规则：图片的 y1（底部）在标题的 y0（顶部）之上 → 该图属于该标题。
          如果多张图在一个标题上方 → 它们都属于同一个标题。
    """
    # 找出所有图标题
    captions = []
    for b in text_blocks:
        cap = is_figure_caption(b.get("text", ""))
        if cap:
            captions.append({
                "caption_id": f"图{cap[0]}",
                "caption_text": b["text"].strip(),
                "description_hint": cap[1],
                "bbox": b["bbox"],
                "y_top": b["bbox"][1],
            })

    if not captions or not images:
        return []

    # 按 y 排序
    images_sorted = sorted(images, key=lambda i: i["bbox"][1])   # 从上到下
    captions_sorted = sorted(captions, key=lambda c: c["y_top"])  # 从上到下

    matched = []
    img_idx = 0

    for cap in captions_sorted:
        cap_images = []
        # 收集该标题上方的所有图（图的底部在标题顶部之上）
        while img_idx < len(images_sorted):
            img = images_sorted[img_idx]
            img_bottom = img["bbox"][3]
            if img_bottom < cap["y_top"] + 20:  # 图在标题上方（20px容差）
                cap_images.append(img)
                img_idx += 1
            else:
                break

        if cap_images:
            matched.append({
                **cap,
                "page_num": page_num,
                "images": cap_images,
                "image_count": len(cap_images),
            })

    # 没有被任何标题关联的图（可能是装饰图）
    orphan_images = []
    while img_idx < len(images_sorted):
        orphan_images.append(images_sorted[img_idx])
        img_idx += 1

    return matched


def describe_image(image_bytes: bytes, caption: str = "") -> str:
    """用 Qwen-VL 描述图片内容"""
    prompt = f"这张图的标题是「{caption}」。请用1-3句话描述图中展示的地理信息、数据或原理。" if caption else "请简要描述这张图片的地理内容。"
    return ask(prompt, base64.b64encode(image_bytes).decode(), max_tokens=300)


# ── 完整处理 ──

def process(pdf_path: str, output_dir: str):
    """处理电子版 PDF → 正文 + 图描述"""
    images_dir = os.path.join(output_dir, "images")
    figures_dir = os.path.join(output_dir, "figures")
    pages_dir = os.path.join(output_dir, "pages")
    md_dir = os.path.join(output_dir, "markdown")
    for d in [output_dir, images_dir, figures_dir, pages_dir, md_dir]:
        os.makedirs(d, exist_ok=True)

    doc = fitz.open(pdf_path)
    total = len(doc)

    all_pages = []
    all_figures = []

    for i, page in enumerate(doc):
        page_num = i + 1
        text = page.get_text().strip()
        text_blocks = page.get_text("blocks")
        blocks = [
            {"bbox": [b[0], b[1], b[2], b[3]], "text": b[4].strip()}
            for b in text_blocks if b[4].strip()
        ]

        # 提取矢量图
        images = extract_page_images(page)

        # 匹配标题 ↔ 图片
        matched = match_captions_to_images(blocks, images, page_num)

        # 保存提取的图片
        saved_images = []
        for j, img in enumerate(images):
            ext = img.get("ext", "png")
            fname = f"page_{page_num}_img_{j}.{ext}"
            fpath = os.path.join(images_dir, fname)
            with open(fpath, "wb") as f:
                f.write(img["image_bytes"])
            saved_images.append({"file": fname, "bbox": img["bbox"]})

        # 保存 page_N.json + page_N.md
        page_json = {"page_num": page_num, "content": text, "images": saved_images}
        with open(os.path.join(pages_dir, f"page_{page_num}.json"), "w", encoding="utf-8") as f:
            json.dump(page_json, f, ensure_ascii=False, indent=2)
        with open(os.path.join(md_dir, f"page_{page_num}.md"), "w", encoding="utf-8") as f:
            f.write(text)

        # 收集页面数据
        page_data = {
            "page_num": page_num,
            "content": text,
            "text_blocks": len(blocks),
            "images_found": len(images),
            "figures_matched": len(matched),
            "saved_images": saved_images,
        }
        all_pages.append(page_data)

        # 对每个匹配到的图组，调 Qwen-VL 描述
        for m in matched:
            print(f"  图 {m['caption_id']} (p{page_num}, {m['image_count']}张图)...", end=" ", flush=True)
            start = time.time()
            descriptions = []
            for k, img_info in enumerate(m["images"]):
                try:
                    desc = describe_image(img_info["image_bytes"], m["description_hint"])
                    descriptions.append(desc)
                except Exception as e:
                    print(f"图{k+1}描述失败(审核拦截): {e}")
                    descriptions.append(f"[图片描述失败: 内容审核限制] {m['description_hint']}")
            elapsed = time.time() - start
            print(f"OK ({elapsed:.1f}s)")

            figure_entry = {
                "figure_id": f"page_{page_num}_{m['caption_id'].replace('图', 'fig_').replace('-', '_')}",
                "page_num": page_num,
                "caption": m["caption_text"],
                "description": " ".join(descriptions),
                "image_count": m["image_count"],
            }
            all_figures.append(figure_entry)

            # 保存图组数据
            with open(os.path.join(figures_dir, f"{figure_entry['figure_id']}.json"), "w", encoding="utf-8") as f:
                json.dump(figure_entry, f, ensure_ascii=False, indent=2)

        print(f"  p{page_num}: {len(text)}字, {len(images)}图, {len(matched)}组匹配")

    doc.close()

    # 保存索引
    index = {"total_pages": total, "total_figures": len(all_figures), "figures": all_figures}
    with open(os.path.join(output_dir, "figures_index.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 完成: {total}页, {len(all_figures)}个图组")
    return all_pages, all_figures, index


def build_chunks(pages, figures, output_dir):
    """将正文 + 图描述混合分块，保存 chunks.json"""
    chunks = []

    # 正文分块
    for p in pages:
        for i, para in enumerate(p["content"].split("\n\n")):
            para = para.strip()
            if len(para) >= 100:
                chunks.append({
                    "page_num": p["page_num"],
                    "chunk_num": i,
                    "content": para,
                    "type": "text",
                })

    # 图描述作为独立 chunk
    for fig in figures:
        chunks.append({
            "page_num": fig["page_num"],
            "chunk_num": 999,
            "content": f"{fig['caption']}\n{fig['description']}",
            "type": "figure",
            "figure_id": fig["figure_id"],
        })

    with open(os.path.join(output_dir, "chunks.json"), "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    print(f"  分块: {len(chunks)} (正文 + {len(figures)}图)")
    return chunks


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python pipeline_digital_enhanced.py <pdf_path> <output_dir>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    output_dir = sys.argv[2]

    if not os.path.exists(pdf_path):
        print(f"PDF 不存在: {pdf_path}")
        sys.exit(1)

    print(f"📄 {pdf_path}\n📁 {output_dir}\n")
    pages, figures, index = process(pdf_path, output_dir)
    chunks = build_chunks(pages, figures, output_dir)
    print(f"\n下一步: python pipeline_import.py 生成嵌入和向量库")
