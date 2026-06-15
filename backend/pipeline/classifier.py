"""
PDF 类型检测器 — 判断 PDF 是电子版/混合/扫描件
    python process_pdf_v2.py <textbook_dir>
"""

import os, sys, fitz
fitz.TOOLS.mupdf_warnings(False)


def classify(pdf_path: str) -> tuple[str, int, int]:
    """检测 PDF 类型 → (born_digital|mixed|scanned, text_pages, total)"""
    doc = fitz.open(pdf_path)
    total = len(doc)
    tp = sum(1 for p in doc if len(p.get_text().strip()) >= 100)
    doc.close()
    r = tp / total if total else 0
    return ("born_digital" if r >= 0.9 else ("mixed" if r > 0.1 else "scanned"), tp, total)


def scan(textbook_dir: str) -> list[dict]:
    """批量扫描目录下所有 PDF 类型"""
    results = []
    for root, _, files in os.walk(textbook_dir):
        for f in files:
            if not f.lower().endswith(".pdf"): continue
            path = os.path.join(root, f)
            try:
                ptype, tp, total = classify(path)
                results.append({"file": f, "path": path, "type": ptype, "text_pages": tp, "total_pages": total})
            except Exception as e:
                results.append({"file": f, "path": path, "error": str(e)})
    return results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python process_pdf_v2.py <textbook_dir>"); sys.exit(1)
    results = scan(sys.argv[1])
    print(f"\n{'文件':<35} {'类型':<14} {'文字页/总页'}\n" + "-" * 65)
    for r in results:
        if "error" in r: print(f"{r['file']:<35} ERROR: {r['error']}")
        else: print(f"{r['file']:<35} {r['type']:<14} {r['text_pages']}/{r['total_pages']}")
    c = {"born_digital": 0, "mixed": 0, "scanned": 0, "error": 0}
    for r in results: c[r.get("type", "error") if "error" not in r else "error"] += 1
    print(f"\n电子版:{c['born_digital']}  混合:{c['mixed']}  扫描件:{c['scanned']}  错误:{c['error']}")
