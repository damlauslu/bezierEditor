"""
bezier_editor.py  –  Interactive cubic Bezier curve editor
UI language: Turkish | Code and comments: English
Python 3.8+, standard library only (tkinter + math)
"""

import tkinter as tk
from tkinter import font as tkfont
import math

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Standard cubic Bezier basis matrix (4x4)
M_BEZIER = [
    [-1,  3, -3,  1],
    [ 3, -6,  3,  0],
    [-3,  3,  0,  0],
    [ 1,  0,  0,  0],
]

# Mouse-click order -> point index.  P0=0, P1=1, P2=2, P3=3.
# User clicks: P0 first, then P3, then P1, then P2.
CLICK_ORDER = [0, 3, 1, 2]

POINT_NAMES  = ['P0', 'P1', 'P2', 'P3']
POINT_COLORS = ['#00cc44', '#ff8800', '#cc44ff', '#ff3333']  # green, orange, purple, red

STEP_MESSAGES = [
    "Adım 1/4: P0 başlangıç noktasını tıklayın",
    "Adım 2/4: P3 bitiş noktasını tıklayın",
    "Adım 3/4: P1 kontrol noktasını tıklayın",
    "Adım 4/4: P2 kontrol noktasını tıklayın",
    "Eğri çizildi. Fareyi eğri üzerinde gezdirin veya nokta düzenleyin.",
]

# Colour palette
BG_DARK  = '#0d0d1e'
BG_PANEL = '#0a0a18'
BG_BOX   = '#0e0e22'
FG_CYAN  = '#00ffff'
FG_YEL   = '#ffdd77'
FG_GREY  = '#aaaacc'

CANVAS_BG = '#1a1a2e'
GRID_COL  = '#1e1e40'
CURVE_COL = '#00ffff'


# ---------------------------------------------------------------------------
# Main application class
# ---------------------------------------------------------------------------

class BezierEditor:

    # ── Initialisation ────────────────────────────────────────────────────────

    def __init__(self, root):
        self.root = root
        self.root.title("Bezier Eğrisi Editörü")
        self.root.minsize(1100, 650)
        self.root.configure(bg=BG_DARK)

        # Application state
        self.points    = [None, None, None, None]  # indexed P0..P3
        self.input_step = 0    # 0-3: placing points; 4: all placed
        self.edit_mode  = None  # None, or int index of point being edited
        self.hover_t    = 0.0
        self.hover_bt   = None  # (x, y) last hovered curve point

        # Fonts
        self.mono   = tkfont.Font(family='Courier', size=9)
        self.mono_b = tkfont.Font(family='Courier', size=9,  weight='bold')
        self.mono_s = tkfont.Font(family='Courier', size=8)
        self.title_f = tkfont.Font(family='Courier', size=10, weight='bold')

        self._build_ui()
        self._update_status()
        self._refresh_info()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        outer = tk.Frame(self.root, bg=BG_DARK)
        outer.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # Fixed-width left panel
        self.left = tk.Frame(outer, bg=BG_PANEL, width=290)
        self.left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 4))
        self.left.pack_propagate(False)

        # Expanding right area
        self.right = tk.Frame(outer, bg=BG_DARK)
        self.right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._build_left_panel()
        self._build_canvas_area()

    # ── Left panel ────────────────────────────────────────────────────────────

    def _build_left_panel(self):
        scroll_wrap = tk.Frame(self.left, bg=BG_PANEL)
        scroll_wrap.pack(fill=tk.BOTH, expand=True)

        vsb = tk.Scrollbar(scroll_wrap, orient=tk.VERTICAL)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        self._pcv = tk.Canvas(scroll_wrap, bg=BG_PANEL,
                              yscrollcommand=vsb.set, highlightthickness=0)
        self._pcv.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.config(command=self._pcv.yview)

        self.panel = tk.Frame(self._pcv, bg=BG_PANEL)
        self._pcv.create_window((0, 0), window=self.panel, anchor='nw', width=272)
        self.panel.bind('<Configure>',
                        lambda e: self._pcv.configure(
                            scrollregion=self._pcv.bbox('all')))

        # Mouse-wheel scrolling (active when cursor is over the left panel)
        def _mw(event):
            self._pcv.yview_scroll(int(-1 * event.delta / 120), 'units')

        self._pcv.bind('<Enter>',  lambda e: self._pcv.bind_all('<MouseWheel>', _mw))
        self._pcv.bind('<Leave>',  lambda e: self._pcv.unbind_all('<MouseWheel>'))

        self._build_info_widgets()
        self._build_edit_widgets()

        # Separator + reset button
        tk.Frame(self.panel, bg='#333355', height=1).pack(
            fill=tk.X, padx=6, pady=8)
        tk.Button(self.panel, text="Sıfırla",
                  bg='#2a0000', fg='#ff6666',
                  font=self.mono_b, relief=tk.FLAT,
                  command=self._reset, pady=7
                  ).pack(fill=tk.X, padx=6, pady=(0, 10))

    # Helper: section header label
    def _sec(self, text):
        tk.Label(self.panel, text=text,
                 bg=BG_PANEL, fg='#4455aa', font=self.mono_s
                 ).pack(anchor='w', padx=8, pady=(8, 2))

    # Helper: value display label (returns widget)
    def _val_lbl(self, text=''):
        lbl = tk.Label(self.panel, text=text,
                       bg=BG_BOX, fg=FG_YEL,
                       font=self.mono, anchor='w', padx=6, pady=2)
        lbl.pack(fill=tk.X, padx=8, pady=1)
        return lbl

    def _build_info_widgets(self):
        # Title
        tk.Label(self.panel, text="BEZİER EĞRİSİ EDİTÖRÜ",
                 bg=BG_PANEL, fg=FG_CYAN, font=self.title_f
                 ).pack(pady=(10, 4))
        tk.Frame(self.panel, bg=FG_CYAN, height=1).pack(
            fill=tk.X, padx=6, pady=2)

        # ── Nokta Koordinatları ──────────────────────────────────────────────
        self._sec("── Nokta Koordinatları ──")
        self.coord_lbls = {}
        for i in range(4):
            row = tk.Frame(self.panel, bg=BG_PANEL)
            row.pack(fill=tk.X, padx=10, pady=1)
            tk.Label(row, text=f"{POINT_NAMES[i]}:",
                     bg=BG_PANEL, fg=POINT_COLORS[i],
                     font=self.mono_b, width=4, anchor='w'
                     ).pack(side=tk.LEFT)
            lbl = tk.Label(row, text="(       ?,       ?)",
                           bg=BG_PANEL, fg=FG_GREY, font=self.mono, anchor='w')
            lbl.pack(side=tk.LEFT)
            self.coord_lbls[i] = lbl

        # ── G Matrisi ─────────────────────────────────────────────────────────
        self._sec("── G Matrisi ──")
        self.g_box = tk.Text(self.panel, height=7, width=34,
                             bg=BG_BOX, fg='#ffff66',
                             font=self.mono, state=tk.DISABLED,
                             relief=tk.FLAT, padx=4, pady=3)
        self.g_box.pack(padx=8, pady=2, fill=tk.X)

        # ── Bezier Matrisi (M) ────────────────────────────────────────────────
        self._sec("── Bezier Matrisi (M) ──")
        m_box = tk.Text(self.panel, height=6, width=34,
                        bg=BG_BOX, fg='#66ff88',
                        font=self.mono, state=tk.DISABLED,
                        relief=tk.FLAT, padx=4, pady=3)
        m_box.pack(padx=8, pady=2, fill=tk.X)
        m_box.configure(state=tk.NORMAL)
        m_box.insert(tk.END,
                     "M_bezier =\n"
                     "[[-1,  3, -3,  1],\n"
                     " [ 3, -6,  3,  0],\n"
                     " [-3,  3,  0,  0],\n"
                     " [ 1,  0,  0,  0]]")
        m_box.configure(state=tk.DISABLED)

        # ── Fare Pozisyonu ────────────────────────────────────────────────────
        self._sec("── Fare Pozisyonu ──")
        self.mouse_lbl = self._val_lbl("(-, -)")

        # ── t Değeri ──────────────────────────────────────────────────────────
        self._sec("── t Değeri ──")
        self.t_lbl = self._val_lbl("t = -")

        # ── B(t) Noktası ──────────────────────────────────────────────────────
        self._sec("── B(t) Noktası ──")
        self.bt_lbl = self._val_lbl("B(t) = (-, -)")

        # ── Eğri Uzunluğu ─────────────────────────────────────────────────────
        self._sec("── Eğri Uzunluğu ──")
        self.len_lbl = self._val_lbl("L = -")

        tk.Frame(self.panel, bg=FG_CYAN, height=1).pack(
            fill=tk.X, padx=6, pady=8)

    def _build_edit_widgets(self):
        self._sec("── Nokta Düzenle ──")

        # 2x2 grid of update buttons
        self.btn_grid = tk.Frame(self.panel, bg=BG_PANEL)
        self.btn_grid.pack(padx=8, pady=4, fill=tk.X)
        self.btn_grid.columnconfigure(0, weight=1)
        self.btn_grid.columnconfigure(1, weight=1)

        self.edit_btns = {}
        for i in range(4):
            btn = tk.Button(
                self.btn_grid,
                text=f"{POINT_NAMES[i]} Güncelle",
                bg='#1a1a3a', fg=POINT_COLORS[i],
                font=self.mono, relief=tk.FLAT,
                activebackground='#2a2a5a',
                command=lambda idx=i: self._activate_edit(idx),
                pady=4)
            btn.grid(row=i // 2, column=i % 2,
                     padx=3, pady=3, sticky='ew')
            self.edit_btns[i] = btn

        # ── Entry frame (hidden until edit mode is active) ────────────────────
        self.entry_frame = tk.Frame(self.panel, bg='#0e0e28',
                                    relief=tk.FLAT, bd=1)
        # NOT packed here – packed on demand in _activate_edit

        self._ep_lbl = tk.Label(self.entry_frame, text="Nokta: -",
                                bg='#0e0e28', fg='#ffff00',
                                font=self.mono_b)
        self._ep_lbl.pack(pady=(6, 2))

        self.ex_var = tk.StringVar()
        self.ey_var = tk.StringVar()

        for axis, var, attr in [('X', self.ex_var, 'ex_entry'),
                                 ('Y', self.ey_var, 'ey_entry')]:
            row = tk.Frame(self.entry_frame, bg='#0e0e28')
            row.pack(fill=tk.X, padx=10, pady=2)
            tk.Label(row, text=f"{axis}:",
                     bg='#0e0e28', fg=FG_GREY,
                     font=self.mono, width=3
                     ).pack(side=tk.LEFT)
            ent = tk.Entry(row, textvariable=var,
                           bg='#1a1a3a', fg='white',
                           font=self.mono, insertbackground='white',
                           relief=tk.FLAT, width=11)
            ent.pack(side=tk.LEFT, padx=3)
            setattr(self, attr, ent)

        self.ex_entry.bind('<Return>', lambda e: self._apply_entry())
        self.ey_entry.bind('<Return>', lambda e: self._apply_entry())

        btn_row = tk.Frame(self.entry_frame, bg='#0e0e28')
        btn_row.pack(fill=tk.X, padx=10, pady=6)
        tk.Button(btn_row, text="Onayla",
                  bg='#003355', fg=FG_CYAN,
                  font=self.mono, relief=tk.FLAT,
                  command=self._apply_entry, pady=3
                  ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 3))
        tk.Button(btn_row, text="İptal",
                  bg='#330011', fg='#ff6666',
                  font=self.mono, relief=tk.FLAT,
                  command=self._cancel_edit, pady=3
                  ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(3, 0))

    # ── Canvas area ───────────────────────────────────────────────────────────

    def _build_canvas_area(self):
        # Status bar pinned to bottom
        self.status_var = tk.StringVar()
        tk.Label(self.right, textvariable=self.status_var,
                 bg='#080818', fg='#7777aa',
                 font=self.mono_s, anchor='w', padx=10, pady=5
                 ).pack(side=tk.BOTTOM, fill=tk.X)

        self.canvas = tk.Canvas(self.right, bg=CANVAS_BG,
                                highlightthickness=1,
                                highlightbackground='#2a2a5e',
                                cursor='crosshair')
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.canvas.bind('<Button-1>', self._on_click)
        self.canvas.bind('<Motion>',   self._on_motion)
        self.canvas.bind('<Configure>', lambda e: self._redraw())

    # ── Event handlers ────────────────────────────────────────────────────────

    def _on_click(self, event):
        x, y = event.x, event.y

        if self.edit_mode is not None:
            # Place the edited point at the clicked position
            self.points[self.edit_mode] = (x, y)
            self._finish_edit()
            return

        if self.input_step < 4:
            idx = CLICK_ORDER[self.input_step]
            self.points[idx] = (x, y)
            self.input_step += 1
            self._redraw()
            self._refresh_info()
            self._update_status()

    def _on_motion(self, event):
        x, y = event.x, event.y
        self.mouse_lbl.config(text=f"({x}, {y})")

        if self._ready():
            t, pt = self._closest_t(x, y)
            self.hover_t  = t
            self.hover_bt = pt
            self.t_lbl.config(text=f"t = {t:.4f}")
            if pt:
                self.bt_lbl.config(
                    text=f"B(t) = ({pt[0]:.1f}, {pt[1]:.1f})")
            # Lightweight update: remove old hover elements, draw new ones
            self.canvas.delete('hover')
            self._draw_hover(t, pt)

    # ── Edit mode ─────────────────────────────────────────────────────────────

    def _activate_edit(self, idx):
        self.edit_mode = idx
        name = POINT_NAMES[idx]

        # Highlight the active button
        for i, btn in self.edit_btns.items():
            if i == idx:
                btn.config(bg='#554400', fg='#ffff00')
            else:
                btn.config(bg='#1a1a3a', fg=POINT_COLORS[i])

        # Pre-fill coordinate entries from current point position
        p = self.points[idx]
        self.ex_var.set(f"{p[0]:.0f}" if p else "")
        self.ey_var.set(f"{p[1]:.0f}" if p else "")
        self._ep_lbl.config(text=f"Nokta: {name}", fg=POINT_COLORS[idx])

        # Show entry frame directly below the button grid
        self.entry_frame.pack(padx=8, pady=4, fill=tk.X,
                              after=self.btn_grid)
        self.ex_entry.focus_set()

        self.canvas.config(cursor='tcross')
        self._update_status()

    def _finish_edit(self):
        """Called after the point has been updated (click or entry)."""
        self._close_edit()
        self._redraw()
        self._refresh_info()

    def _cancel_edit(self):
        self._close_edit()

    def _close_edit(self):
        self.edit_mode = None
        for i, btn in self.edit_btns.items():
            btn.config(bg='#1a1a3a', fg=POINT_COLORS[i])
        self.entry_frame.pack_forget()
        self.canvas.config(cursor='crosshair')
        self._update_status()

    def _apply_entry(self):
        """Validate and apply manually typed coordinates."""
        try:
            x = float(self.ex_var.get())
            y = float(self.ey_var.get())
        except ValueError:
            return
        if self.edit_mode is not None:
            self.points[self.edit_mode] = (x, y)
            self._finish_edit()

    # ── Reset ─────────────────────────────────────────────────────────────────

    def _reset(self):
        self.points     = [None, None, None, None]
        self.input_step = 0
        self.edit_mode  = None
        self.hover_t    = 0.0
        self.hover_bt   = None

        for i, btn in self.edit_btns.items():
            btn.config(bg='#1a1a3a', fg=POINT_COLORS[i])
        self.entry_frame.pack_forget()
        self.canvas.config(cursor='crosshair')

        self.t_lbl.config(text="t = -")
        self.bt_lbl.config(text="B(t) = (-, -)")
        self.len_lbl.config(text="L = -")
        self.mouse_lbl.config(text="(-, -)")

        self._update_status()
        self._refresh_info()
        self._redraw()

    # ── Info panel updates ────────────────────────────────────────────────────

    def _refresh_info(self):
        # Point coordinate labels
        for i in range(4):
            p = self.points[i]
            text = (f"({p[0]:8.1f},{p[1]:8.1f})" if p
                    else "(        ?,        ?)")
            self.coord_lbls[i].config(text=text)

        # G matrix text box
        self.g_box.configure(state=tk.NORMAL)
        self.g_box.delete('1.0', tk.END)
        lines = ["G  [ x          y      ]"]
        for i in range(4):
            p = self.points[i]
            n = POINT_NAMES[i]
            if p:
                lines.append(f"  {n} [{p[0]:9.2f},{p[1]:9.2f} ]")
            else:
                lines.append(f"  {n} [        ?,        ? ]")
        self.g_box.insert(tk.END, '\n'.join(lines))
        self.g_box.configure(state=tk.DISABLED)

        # Arc length
        if self._ready():
            L = self._arc_length()
            self.len_lbl.config(text=f"L ≈ {L:.2f} piksel")
        else:
            self.len_lbl.config(text="L = -")

    def _update_status(self):
        if self.edit_mode is not None:
            name = POINT_NAMES[self.edit_mode]
            msg = (f"Düzenleme modu: [{name}] için "
                   "yeni konumu tıklayın veya koordinat girin")
        else:
            msg = STEP_MESSAGES[min(self.input_step, 4)]
        self.status_var.set(msg)

    # ── Bezier mathematics ────────────────────────────────────────────────────

    def _ready(self):
        """Return True when all four control points have been placed."""
        return all(p is not None for p in self.points)

    def _bezier(self, t):
        """Evaluate B(t) using the Bernstein basis formula."""
        p0, p1, p2, p3 = self.points
        mt  = 1.0 - t
        c0  = mt * mt * mt
        c1  = 3.0 * mt * mt * t
        c2  = 3.0 * mt * t  * t
        c3  = t  * t  * t
        x = c0*p0[0] + c1*p1[0] + c2*p2[0] + c3*p3[0]
        y = c0*p0[1] + c1*p1[1] + c2*p2[1] + c3*p3[1]
        return (x, y)

    def _closest_t(self, mx, my, n=200):
        """
        Find the parameter t whose curve point is closest to (mx, my).
        Returns (t, point).
        """
        best_t, best_d, best_pt = 0.0, float('inf'), None
        for i in range(n + 1):
            t  = i / n
            pt = self._bezier(t)
            d  = (pt[0] - mx)**2 + (pt[1] - my)**2
            if d < best_d:
                best_t, best_d, best_pt = t, d, pt
        return best_t, best_pt

    def _arc_length(self, n=200):
        """Approximate arc length via cumulative chord summation."""
        total = 0.0
        prev  = self._bezier(0.0)
        for i in range(1, n + 1):
            curr = self._bezier(i / n)
            dx, dy = curr[0] - prev[0], curr[1] - prev[1]
            total += math.sqrt(dx*dx + dy*dy)
            prev = curr
        return total

    # ── Canvas drawing ────────────────────────────────────────────────────────

    def _redraw(self):
        """Full canvas redraw (called on structural changes)."""
        self.canvas.delete('all')
        self._draw_grid()

        if self._ready():
            self._draw_control_polygon()
            self._draw_curve()
            self._draw_tangent_arrows()

        self._draw_points()

        # Restore hover marker if one was visible
        if self._ready() and self.hover_bt:
            self._draw_hover(self.hover_t, self.hover_bt)

    def _draw_grid(self):
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 2 or h < 2:
            return
        step = 50
        for x in range(0, w + step, step):
            self.canvas.create_line(x, 0, x, h, fill=GRID_COL, width=1)
        for y in range(0, h + step, step):
            self.canvas.create_line(0, y, w, y, fill=GRID_COL, width=1)

    def _draw_control_polygon(self):
        """Draw dashed lines P0→P1→P2→P3."""
        pts = self.points  # [P0, P1, P2, P3]
        for i in range(3):
            a, b = pts[i], pts[i + 1]
            self.canvas.create_line(
                a[0], a[1], b[0], b[1],
                fill='#445566', dash=(5, 5), width=1)

    def _draw_curve(self):
        """Sample the curve at 200 steps and draw as a polyline."""
        coords = []
        for i in range(201):
            coords.extend(self._bezier(i / 200))
        self.canvas.create_line(*coords, fill=CURVE_COL, width=2, smooth=False)

    def _draw_tangent_arrows(self):
        """Draw tangent arrows at P0 (towards P1) and P3 (towards P2)."""
        p0, p1, p2, p3 = self.points
        self._arrow(p0, p1, '#00ff88')   # start tangent
        self._arrow(p3, p2, '#ff4466')   # end tangent

    def _arrow(self, src, dst, color):
        """Draw an arrow starting at src and pointing toward dst."""
        dx = dst[0] - src[0]
        dy = dst[1] - src[1]
        length = math.hypot(dx, dy)
        if length < 1:
            return
        arrow_len = min(50.0, max(15.0, length * 0.35))
        ux, uy = dx / length, dy / length
        ex = src[0] + ux * arrow_len
        ey = src[1] + uy * arrow_len
        self.canvas.create_line(
            src[0], src[1], ex, ey,
            fill=color, width=2,
            arrow=tk.LAST, arrowshape=(10, 12, 4))

    def _draw_points(self):
        """Draw filled circles and coordinate labels for each placed point."""
        r = 6
        for i in range(4):
            p = self.points[i]
            if p is None:
                continue
            color = POINT_COLORS[i]
            name  = POINT_NAMES[i]

            # Yellow highlight ring when this point is in edit mode
            if self.edit_mode == i:
                self.canvas.create_oval(
                    p[0]-r-4, p[1]-r-4, p[0]+r+4, p[1]+r+4,
                    outline='#ffff00', width=2, fill='')

            # Filled circle
            self.canvas.create_oval(
                p[0]-r, p[1]-r, p[0]+r, p[1]+r,
                fill=color, outline='white', width=1)

            # Coordinate label
            self.canvas.create_text(
                p[0]+r+6, p[1]-r-4,
                text=f"{name}({p[0]:.0f},{p[1]:.0f})",
                fill=color, font=('Courier', 8), anchor='w')

    def _draw_hover(self, t, pt):
        """Draw a small marker at the hovered curve point (tag='hover')."""
        if pt is None:
            return
        x, y = pt
        r = 4
        self.canvas.create_oval(
            x-r, y-r, x+r, y+r,
            fill='white', outline=FG_CYAN, width=2,
            tags='hover')
        self.canvas.create_text(
            x+r+6, y,
            text=f"t={t:.3f}",
            fill='white', font=('Courier', 8),
            anchor='w', tags='hover')


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    root = tk.Tk()
    BezierEditor(root)
    root.mainloop()


if __name__ == '__main__':
    main()
