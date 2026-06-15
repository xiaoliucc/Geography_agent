"""
地理教材导入工具（图形化）
    cd backend && python -m pipeline.gui
"""

import os, json, threading, tkinter as tk
from tkinter import ttk, messagebox, filedialog
import fitz, chromadb, dashscope
from dotenv import load_dotenv

fitz.TOOLS.mupdf_warnings(False)
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

MATERIALS = os.path.join(os.path.dirname(__file__), "..", "..", "materials")
TEXTBOOKS = os.path.join(MATERIALS, "textbooks")
PROCESSED = os.path.join(MATERIALS, "processed")

# ── 所有导入提前到顶部 ──
from pipeline.digital import process as digital_process, build_chunks
from pipeline.ocr import process as ocr_process
from pipeline.full_pages import generate as gen_full_pages


class ImportGUI:
    def __init__(self, root):
        self.root = root; self.root.title("地理教材导入工具"); self.root.geometry("750x550")
        self._build_ui()
        threading.Thread(target=self._scan, daemon=True).start()

    # ── UI ──
    def _build_ui(self):
        ttk.Label(self.root, text="📚 地理教材导入", font=("", 16, "bold")).pack(pady=(16, 0))
        self._build_target(); self._build_list()
        self.progress = ttk.Progressbar(self.root, mode="determinate"); self.progress.pack(fill=tk.X, padx=16, pady=(8, 0))
        self.status = ttk.Label(self.root, text="正在扫描..."); self.status.pack(pady=(2, 0))
        self._build_btns()

    def _build_target(self):
        f = ttk.LabelFrame(self.root, text="目标位置", padding=8); f.pack(fill=tk.X, padx=16, pady=(8, 4))
        r = ttk.Frame(f); r.pack(fill=tk.X)
        ttk.Label(r, text="出版社:").pack(side=tk.LEFT)
        self.pub_var = tk.StringVar(value="renjiao")
        self.pub = ttk.Combobox(r, textvariable=self.pub_var, width=20); self.pub.pack(side=tk.LEFT, padx=8)
        ttk.Button(r, text="新建", command=self._new_pub).pack(side=tk.LEFT, padx=4)
        r2 = ttk.Frame(f); r2.pack(fill=tk.X, pady=(6, 0))
        ttk.Label(r2, text="教材名:").pack(side=tk.LEFT)
        self.book_var = tk.StringVar(value="")
        ttk.Entry(r2, textvariable=self.book_var, width=30).pack(side=tk.LEFT, padx=8)
        ttk.Label(r2, text="如 bixiu_1", foreground="gray").pack(side=tk.LEFT)
        self._refresh_pubs()

    def _build_list(self):
        f = ttk.LabelFrame(self.root, text="可用 PDF", padding=8); f.pack(fill=tk.BOTH, expand=True, padx=16, pady=(4, 0))
        self.tree = ttk.Treeview(f, columns=("文件", "页数", "类型"), show="headings", height=10)
        for col, w in [("文件", 400), ("页数", 80), ("类型", 130)]:
            self.tree.heading(col, text=col); self.tree.column(col, width=w, anchor="center" if col != "文件" else "w")
        s = ttk.Scrollbar(f, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=s.set); self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True); s.pack(side=tk.RIGHT, fill=tk.Y)

    def _build_btns(self):
        f = ttk.Frame(self.root); f.pack(fill=tk.X, padx=16, pady=10)
        ttk.Button(f, text="🔄 刷新", command=lambda: threading.Thread(target=self._scan, daemon=True).start()).pack(side=tk.LEFT, padx=3)
        for l, m in [("📥 电子版", "digital"), ("✨ 增强", "enhanced"), ("📸 OCR", "ocr"), ("📋 混合", "mixed")]:
            ttk.Button(f, text=l, command=lambda m=m: self._start(m)).pack(side=tk.LEFT, padx=3)
        ttk.Button(f, text="📂 外部", command=self._open).pack(side=tk.LEFT, padx=3)

    # ── 工具方法 ──
    def _refresh_pubs(self):
        ds = [d for d in os.listdir(PROCESSED) if os.path.isdir(os.path.join(PROCESSED, d))] if os.path.exists(PROCESSED) else ["renjiao"]
        self.pub["values"] = ds

    def _new_pub(self):
        dlg = tk.Toplevel(self.root); dlg.title("新建出版社"); dlg.geometry("300x120")
        ttk.Label(dlg, text="目录名:").pack(pady=12); e = ttk.Entry(dlg, width=25); e.pack()
        def ok():
            n = e.get().strip()
            if n: os.makedirs(os.path.join(PROCESSED, n), exist_ok=True); self._refresh_pubs(); self.pub_var.set(n); dlg.destroy()
        ttk.Button(dlg, text="确定", command=ok).pack(pady=10)

    def _scan(self):
        self.tree.delete(*self.tree.get_children())
        for root, _, files in os.walk(TEXTBOOKS):
            for f in files:
                if not f.lower().endswith(".pdf"): continue
                p = os.path.join(root, f)
                try:
                    doc = fitz.open(p); t = len(doc)
                    tp = sum(1 for pg in doc if len(pg.get_text().strip()) >= 100); doc.close()
                    r = tp / t if t else 0
                    pt = "📄 电子版" if r >= 0.9 else ("📋 混合" if r > 0.1 else "📸 扫描件")
                    self.root.after(0, lambda v=(f, t, pt), x=p: self.tree.insert("", tk.END, values=v, tags=(x,)))
                except Exception: continue
        self.root.after(0, lambda: self.status.config(text=f"{len(self.tree.get_children())} 个 PDF"))

    def _start(self, mode):
        sel = self.tree.selection()
        if not sel: messagebox.showwarning("提示", "请先选择 PDF"); return
        it = self.tree.item(sel[0]); path = it["tags"][0]; fn = it["values"][0]
        pub = self.pub_var.get().strip()
        book = self.book_var.get().strip() or os.path.splitext(fn)[0].replace(" ", "_")[:30]
        if os.path.exists(os.path.join(PROCESSED, pub, book, "vector_db")):
            if not messagebox.askyesno("确认", f"{pub}/{book} 已有数据，覆盖？"): return
        lbs = {"digital": "PyMuPDF提取", "enhanced": "文字+图+Qwen-VL", "ocr": "Qwen-VL逐页", "mixed": "智能分流"}
        if not messagebox.askyesno("确认", f"{pub}/{book}\n{lbs[mode]}\n开始？"): return
        threading.Thread(target=self._import, args=(path, pub, book, mode), daemon=True).start()

    def _open(self):
        path = filedialog.askopenfilename(title="选择 PDF", filetypes=[("PDF", "*.pdf")])
        if not path: return
        pub = self.pub_var.get().strip()
        book = self.book_var.get().strip() or os.path.splitext(os.path.basename(path))[0].replace(" ", "_")[:30]
        threading.Thread(target=self._import, args=(path, pub, book, "digital"), daemon=True).start()

    # ── 导入 ──
    def _import(self, pdf_path, pub, book, mode):
        self._ui(False)
        out = os.path.join(PROCESSED, pub, book)
        pe = os.path.join(out, "pdf_extracted"); os.makedirs(pe, exist_ok=True)

        pages = self._extract(pdf_path, pe, mode)
        if not pages: self._msg("❌ 无文字"); self._ui(True); return

        self._step("2/5 全页图片", 20)
        try: gen_full_pages(pdf_path, pe)
        except Exception: pass

        chunks = self._load_chunks(pe) if mode == "enhanced" else self._chunk(pages, pe)
        embedded = self._embed(chunks, pe)
        if not embedded: return
        self._build_db(embedded, pub, book, out)
        self._msg(f"✅ {pub}/{book} — {len(embedded)} chunks"); self._refresh_pubs(); self._ui(True)

    def _extract(self, pdf_path, pe, mode):
        pages = []
        if mode == "enhanced":
            pages, figures, _ = digital_process(pdf_path, pe)
            build_chunks(pages, figures, pe)
            return pages
        if mode in ("digital", "mixed"):
            doc = fitz.open(pdf_path)
            for p in doc:
                t = p.get_text().strip()
                if t: pages.append({"page_num": p.number + 1, "content": t})
            doc.close()
        if mode == "ocr" or (mode == "mixed"):
            ocr_process(pdf_path, pe)
            pd = os.path.join(pe, "pages")
            if os.path.exists(pd):
                for f in sorted(os.listdir(pd)):
                    if f.endswith(".json"):
                        with open(os.path.join(pd, f), encoding="utf-8") as fp:
                            d = json.load(fp)
                        pages.append({"page_num": int(f[5:-5]), "content": json.dumps(d, ensure_ascii=False)})
        return pages

    def _load_chunks(self, pe):
        with open(os.path.join(pe, "chunks.json"), encoding="utf-8") as f:
            return json.load(f)

    def _chunk(self, pages, pe):
        chunks = []
        for p in pages:
            for i, para in enumerate(p["content"].split("\n\n")):
                para = para.strip()
                if len(para) >= 100:
                    chunks.append({"page_num": p["page_num"], "chunk_num": i, "content": para})
        with open(os.path.join(pe, "chunks.json"), "w", encoding="utf-8") as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)
        return chunks

    def _embed(self, chunks, pe):
        self._step(f"嵌入 (0/{len(chunks)})", 50)
        embedded = []
        for i, c in enumerate(chunks):
            try:
                r = dashscope.TextEmbedding.call(model="text-embedding-v4", input=c["content"],
                                                  api_key=os.getenv("DASHSCOPE_API_KEY"))
                if r.status_code == 200:
                    embedded.append({**c, "embedding": r.output["embeddings"][0]["embedding"]})
                if (i + 1) % 20 == 0:
                    self._step(f"嵌入 ({i+1}/{len(chunks)})", 50 + int(20*(i+1)/len(chunks)))
            except Exception as e:
                self._msg(f"嵌入失败: {e}"); self._ui(True); return None
        with open(os.path.join(pe, "embeddings.json"), "w", encoding="utf-8") as f:
            json.dump(embedded, f, ensure_ascii=False)
        return embedded

    def _build_db(self, embedded, pub, book, out):
        self._step("构建向量库", 75)
        dp = os.path.join(out, "vector_db"); os.makedirs(dp, exist_ok=True)
        cl = chromadb.PersistentClient(path=dp)
        try: cl.delete_collection("geography_full")
        except: pass
        col = cl.create_collection("geography_full")
        bs, name = 100, f"{pub}_{book}"
        for s in range(0, len(embedded), bs):
            b = embedded[s:s+bs]
            col.add(ids=[f"chunk_{i}" for i in range(s, s+len(b))],
                    documents=[x["content"] for x in b],
                    embeddings=[x["embedding"] for x in b],
                    metadatas=[{"page_num": x.get("page_num",0), "type": x.get("type","text"),
                                "textbook": name} for x in b])
            self._step(f"入库 ({s+len(b)}/{len(embedded)})", 75+int(25*(s+len(b))/len(embedded)))

    def _step(self, msg, pct):
        self.root.after(0, lambda: self.status.config(text=msg)); self.root.after(0, lambda: self.progress.configure(value=pct))
    def _msg(self, msg):
        self.root.after(0, lambda: self.status.config(text=msg))
    def _ui(self, on):
        self.root.after(0, lambda: self.progress.configure(value=0))


if __name__ == "__main__":
    ImportGUI(tk.Tk()); tk.mainloop()
