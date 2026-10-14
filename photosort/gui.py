"""JPG/RAW 분류기 GUI (Tkinter). 폴더 끌어다 놓기는 tkinterdnd2가 있을 때만 활성화."""

from __future__ import annotations

import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from . import core

try:  # 선택 사항: pip install tkinterdnd2
    from tkinterdnd2 import DND_FILES, TkinterDnD

    _Root = TkinterDnD.Tk
except Exception:  # noqa: BLE001 - 없으면 버튼으로만 폴더 선택
    DND_FILES = None
    _Root = tk.Tk


class App:
    def __init__(self) -> None:
        self.root = _Root()
        self.root.title("JPG / RAW 분류기")
        self.root.geometry("560x520")
        self.folder = tk.StringVar()
        self.move = tk.BooleanVar(value=False)
        self.by_date = tk.BooleanVar(value=False)
        self.recursive = tk.BooleanVar(value=False)
        self.q: queue.Queue = queue.Queue()
        self.busy = False
        self._build()
        self.root.after(100, self._poll)

    def _build(self) -> None:
        pad = {"padx": 12, "pady": 6}
        hint = "여기에 폴더를 끌어다 놓거나 [폴더 선택]을 누르세요" if DND_FILES else "[폴더 선택]을 눌러 사진 폴더를 고르세요"
        self.drop = tk.Label(self.root, text=hint, relief="groove", height=4)
        self.drop.pack(fill="x", **pad)
        if DND_FILES:
            self.drop.drop_target_register(DND_FILES)
            self.drop.dnd_bind("<<Drop>>", self._on_drop)

        row = ttk.Frame(self.root)
        row.pack(fill="x", **pad)
        ttk.Entry(row, textvariable=self.folder).pack(side="left", fill="x", expand=True)
        ttk.Button(row, text="폴더 선택", command=self._choose).pack(side="left", padx=(8, 0))

        opts = ttk.LabelFrame(self.root, text="옵션")
        opts.pack(fill="x", **pad)
        ttk.Checkbutton(opts, text="이동하기 (끄면 복사 — 원본 유지, 권장)", variable=self.move).pack(anchor="w", padx=8, pady=2)
        ttk.Checkbutton(opts, text="날짜별 폴더로 나누기 (2026-10-14/JPG, RAW)", variable=self.by_date).pack(anchor="w", padx=8, pady=2)
        ttk.Checkbutton(opts, text="하위 폴더 포함 (SD카드 DCIM 등)", variable=self.recursive).pack(anchor="w", padx=8, pady=2)

        btns = ttk.Frame(self.root)
        btns.pack(fill="x", **pad)
        self.btn_preview = ttk.Button(btns, text="미리보기", command=lambda: self._start(dry=True))
        self.btn_preview.pack(side="left")
        self.btn_run = ttk.Button(btns, text="분류 실행", command=lambda: self._start(dry=False))
        self.btn_run.pack(side="left", padx=8)

        self.bar = ttk.Progressbar(self.root, mode="determinate")
        self.bar.pack(fill="x", **pad)

        self.log = tk.Text(self.root, height=12, state="disabled", wrap="word")
        self.log.pack(fill="both", expand=True, **pad)

    # --- 입력 ---
    def _choose(self) -> None:
        d = filedialog.askdirectory(title="사진 폴더 선택")
        if d:
            self.folder.set(d)

    def _on_drop(self, event) -> None:
        paths = self.root.tk.splitlist(event.data)
        if paths:
            p = Path(paths[0])
            self.folder.set(str(p if p.is_dir() else p.parent))

    # --- 실행 ---
    def _options(self) -> core.Options:
        return core.Options(move=self.move.get(), by_date=self.by_date.get(), recursive=self.recursive.get())

    def _start(self, dry: bool) -> None:
        if self.busy:
            return
        folder = Path(self.folder.get())
        if not folder.is_dir():
            messagebox.showwarning("폴더 없음", "먼저 사진 폴더를 선택해 주세요.")
            return
        opts = self._options()
        self._clear_log()
        self.busy = True
        self.btn_preview.state(["disabled"])
        self.btn_run.state(["disabled"])
        threading.Thread(target=self._work, args=(folder, opts, dry), daemon=True).start()

    def _work(self, folder: Path, opts: core.Options, dry: bool) -> None:
        try:
            plan = core.build_plan(folder, opts)
            self.q.put(("log", self._summary(plan)))
            if dry or not plan.items:
                if not plan.items:
                    self.q.put(("log", "정리할 사진이 없습니다."))
                self.q.put(("done", None))
                return
            res = core.execute(plan, opts, lambda i, n, it: self.q.put(("progress", (i, n))))
            verb = "이동" if opts.move else "복사"
            self.q.put(("log", f"\n완료: {res.done}개 {verb}됨" + (f", 오류 {len(res.errors)}개" if res.errors else "")))
            for e in res.errors:
                self.q.put(("log", f"  ! {e}"))
        except Exception as e:  # noqa: BLE001 - 사용자에게 보여주기 위함
            self.q.put(("log", f"오류: {e}"))
        self.q.put(("done", None))

    @staticmethod
    def _summary(plan: core.Plan) -> str:
        lines = [
            f"JPG {plan.jpg_count}장 / RAW {plan.raw_count}장 (JPG+RAW 짝 {plan.pairs}쌍)",
            f"JPG만 있는 사진 {len(plan.jpg_only)}장, RAW만 있는 사진 {len(plan.raw_only)}장",
        ]
        for label, files in (("JPG만", plan.jpg_only), ("RAW만", plan.raw_only)):
            for f in files[:10]:
                lines.append(f"  [{label}] {f.name}")
            if len(files) > 10:
                lines.append(f"  [{label}] ... 외 {len(files) - 10}장")
        return "\n".join(lines)

    # --- UI 갱신 ---
    def _poll(self) -> None:
        try:
            while True:
                kind, val = self.q.get_nowait()
                if kind == "log":
                    self._append(val)
                elif kind == "progress":
                    i, n = val
                    self.bar.configure(maximum=n, value=i)
                elif kind == "done":
                    self.busy = False
                    self.btn_preview.state(["!disabled"])
                    self.btn_run.state(["!disabled"])
        except queue.Empty:
            pass
        self.root.after(100, self._poll)

    def _append(self, text: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", text + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _clear_log(self) -> None:
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")
        self.bar.configure(value=0)

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    App().run()
