"""
nurbs_editor.py  –  Interactive NURBS (Non-Uniform Rational B-Spline) curve editor
UI language: Turkish | Code and comments: English
Python 3.8+, standard library only (tkinter + math)

Mathematical basis:
    C(u) = Σ [Ni,p(u) * wi * Pi]  /  Σ [Ni,p(u) * wi]

Key additions over B-Spline:
  - Per-control-point weights (wi)
  - Rational evaluation: weighted sum / sum-of-weights
  - Weight editing via panel (index + value) and scroll wheel on points
  - Visual weight indicator: circle radius ∝ weight
  - Weight = 0 → point has no influence on curve
  - All curve parameters (degree, knot vector, weights) are live-editable
"""

import tkinter as tk
from tkinter import font as tkfont
import math

# ---------------------------------------------------------------------------
# Constants / Colour palette
# ---------------------------------------------------------------------------

BG_DARK   = '#0d0d1e'
BG_PANEL  = '#0a0a18'
BG_BOX    = '#0e0e22'
FG_CYAN   = '#00ffff'
FG_YEL    = '#ffdd77'
FG_GREY   = '#aaaacc'
FG_ORANGE = '#ffaa44'

CANVAS_BG  = '#1a1a2e'
GRID_COL   = '#1e1e40'
CURVE_COL  = '#ff6600'   # orange — distinct from B-Spline cyan
WEIGHT_COL = '#ffaa00'   # weight indicator ring colour
POLY_COL   = '#445566'

POINT_PALETTE = [
    '#00cc44', '#ff8800', '#cc44ff', '#ff3333',
    '#00aaff', '#ffff00', '#ff66aa', '#44ffcc',
    '#ff6600', '#aaffaa', '#6688ff', '#ffaa33',
]

STEPS         = 400    # curve polyline sample count
BASE_RADIUS   = 6      # base pixel radius for control-point circles
WEIGHT_SCALE  = 4      # extra radius pixels per unit weight (visual only)
DEFAULT_W     = 1.0    # default weight for new control points


# ---------------------------------------------------------------------------
# NURBS mathematics
# ---------------------------------------------------------------------------

def cox_de_boor(t, i, p, knots):
    """Recursive Cox–de Boor basis function N_{i,p}(t)."""
    if p == 0:
        if knots[i] <= t < knots[i + 1]:
            return 1.0
        if t == knots[-1] and knots[i] <= t <= knots[i + 1]:
            return 1.0   # clamp at last knot
        return 0.0
    d1 = knots[i + p]     - knots[i]
    d2 = knots[i + p + 1] - knots[i + 1]
    c1 = ((t - knots[i])          / d1 * cox_de_boor(t, i,     p - 1, knots)
          if d1 != 0 else 0.0)
    c2 = ((knots[i + p + 1] - t)  / d2 * cox_de_boor(t, i + 1, p - 1, knots)
          if d2 != 0 else 0.0)
    return c1 + c2


def nurbs_point(t, ctrl_pts, weights, knots, degree):
    """
    Evaluate NURBS curve at parameter t using the rational formula:
        C(t) = Σ(Ni,p * wi * Pi) / Σ(Ni,p * wi)
    """
    n = len(ctrl_pts) - 1
    wx, wy, wsum = 0.0, 0.0, 0.0
    for i in range(n + 1):
        b = cox_de_boor(t, i, degree, knots)
        w = weights[i]
        bw = b * w
        wx   += bw * ctrl_pts[i][0]
        wy   += bw * ctrl_pts[i][1]
        wsum += bw
    if wsum == 0.0:
        return ctrl_pts[0]   # degenerate guard
    return (wx / wsum, wy / wsum)


def make_uniform_knots(n_pts, degree):
    """Generate a uniform (open/clamped) knot vector for n_pts points."""
    order   = degree + 1
    n_knots = n_pts + order
    knots   = []
    for i in range(n_knots):
        if i < order:
            knots.append(0.0)
        elif i >= n_pts:
            knots.append(1.0)
        else:
            knots.append((i - degree) / (n_pts - degree))
    return knots


def parse_float_list(text):
    """Parse a space/comma separated float list. Returns list[float] or None."""
    text = text.replace(',', ' ')
    parts = text.split()
    try:
        return [float(v) for v in parts]
    except ValueError:
        return None


def validate_knots(knots, n_pts, degree):
    """Validate knot vector length and monotonicity."""
    required = n_pts + degree + 1
    if len(knots) != required:
        return False, f"Düğüm vektörü uzunluğu {required} olmalı, {len(knots)} girildi."
    for i in range(1, len(knots)):
        if knots[i] < knots[i - 1]:
            return False, f"Düğüm vektörü azalmayan sırada olmalı (indeks {i})."
    return True, "Geçerli"


# ---------------------------------------------------------------------------
# Main application class
# ---------------------------------------------------------------------------

class NURBSEditor:

    def __init__(self, root):
        self.root = root
        self.root.title("NURBS Eğrisi Editörü")
        self.root.minsize(1180, 700)
        self.root.configure(bg=BG_DARK)

        # --- Application state ---
        self.ctrl_pts  = []      # list of (x, y)
        self.weights   = []      # list of float (wi ≥ 0)
        self.degree    = 3       # curve degree p
        self.knots     = []      # knot vector
        self.knot_mode = 'auto'  # 'auto' | 'manual'
        self.drag_idx       = None    # index being dragged
        self.hover_t        = None
        self.hover_pt       = None
        self.click_edit_idx = None   # index awaiting canvas-click placement

        # --- Fonts ---
        self.mono    = tkfont.Font(family='Courier', size=9)
        self.mono_b  = tkfont.Font(family='Courier', size=9,  weight='bold')
        self.mono_s  = tkfont.Font(family='Courier', size=8)
        self.title_f = tkfont.Font(family='Courier', size=10, weight='bold')

        self._build_ui()
        self._auto_knots()
        self._refresh_all()

    # ── UI construction ────────────────────────────────────────────────────

    def _build_ui(self):
        outer = tk.Frame(self.root, bg=BG_DARK)
        outer.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        self.left = tk.Frame(outer, bg=BG_PANEL, width=310)
        self.left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 4))
        self.left.pack_propagate(False)

        self.right = tk.Frame(outer, bg=BG_DARK)
        self.right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._build_left_panel()
        self._build_canvas_area()

    # ── Left panel ────────────────────────────────────────────────────────

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
        self._pcv.create_window((0, 0), window=self.panel, anchor='nw', width=292)
        self.panel.bind('<Configure>',
                        lambda e: self._pcv.configure(
                            scrollregion=self._pcv.bbox('all')))

        def _mw(ev):
            self._pcv.yview_scroll(int(-1 * ev.delta / 120), 'units')
        self._pcv.bind('<Enter>', lambda e: self._pcv.bind_all('<MouseWheel>', _mw))
        self._pcv.bind('<Leave>', lambda e: self._pcv.unbind_all('<MouseWheel>'))

        self._build_param_section()
        self._build_knot_section()
        self._build_weight_section()
        self._build_info_section()
        self._build_points_section()

        tk.Frame(self.panel, bg='#333355', height=1).pack(fill=tk.X, padx=6, pady=8)
        tk.Button(self.panel, text="Sıfırla",
                  bg='#2a0000', fg='#ff6666',
                  font=self.mono_b, relief=tk.FLAT,
                  command=self._reset, pady=7
                  ).pack(fill=tk.X, padx=6, pady=(0, 10))

    # ── Helpers ───────────────────────────────────────────────────────────

    def _sec(self, text):
        tk.Label(self.panel, text=text,
                 bg=BG_PANEL, fg='#4455aa', font=self.mono_s
                 ).pack(anchor='w', padx=8, pady=(8, 2))

    def _val_lbl(self, text=''):
        lbl = tk.Label(self.panel, text=text,
                       bg=BG_BOX, fg=FG_YEL,
                       font=self.mono, anchor='w', padx=6, pady=2)
        lbl.pack(fill=tk.X, padx=8, pady=1)
        return lbl

    # ── Degree / order section ─────────────────────────────────────────────

    def _build_param_section(self):
        tk.Label(self.panel, text="NURBS EĞRİSİ EDİTÖRÜ",
                 bg=BG_PANEL, fg=FG_ORANGE, font=self.title_f
                 ).pack(pady=(10, 4))
        tk.Frame(self.panel, bg=FG_ORANGE, height=1).pack(fill=tk.X, padx=6, pady=2)

        self._sec("── Derece / Order ──")

        row = tk.Frame(self.panel, bg=BG_PANEL)
        row.pack(fill=tk.X, padx=10, pady=3)
        tk.Label(row, text="Derece (p):", bg=BG_PANEL, fg=FG_GREY,
                 font=self.mono, width=12, anchor='w').pack(side=tk.LEFT)
        self.degree_var = tk.IntVar(value=self.degree)
        self._deg_spin  = tk.Spinbox(
            row, from_=1, to=20, textvariable=self.degree_var,
            width=5, font=self.mono,
            bg='#1a1a3a', fg='white', buttonbackground='#2a2a5a',
            relief=tk.FLAT, insertbackground='white',
            command=self._on_degree_change)
        self._deg_spin.pack(side=tk.LEFT, padx=4)
        self._deg_spin.bind('<Return>', lambda e: self._on_degree_change())

        row2 = tk.Frame(self.panel, bg=BG_PANEL)
        row2.pack(fill=tk.X, padx=10, pady=1)
        tk.Label(row2, text="Order (k=p+1):", bg=BG_PANEL, fg=FG_GREY,
                 font=self.mono, width=14, anchor='w').pack(side=tk.LEFT)
        self.order_lbl = tk.Label(row2, text="4", bg=BG_BOX, fg='#66ff88',
                                   font=self.mono_b, width=5)
        self.order_lbl.pack(side=tk.LEFT, padx=4)

        self.degree_err_lbl = tk.Label(self.panel, text='',
                                        bg=BG_PANEL, fg='#ff4444',
                                        font=self.mono_s, wraplength=270)
        self.degree_err_lbl.pack(fill=tk.X, padx=8)

        self._sec("── Eğri Bilgisi ──")
        self.npts_lbl  = self._val_lbl("Kontrol noktası: 0")
        self.deg_lbl   = self._val_lbl("Derece: 3  Order: 4")
        self.t_lbl     = self._val_lbl("u = -")
        self.bt_lbl    = self._val_lbl("C(u) = (-, -)")
        self.len_lbl   = self._val_lbl("L ≈ -")
        self.mouse_lbl = self._val_lbl("Fare: (-, -)")

    # ── Knot vector section ────────────────────────────────────────────────

    def _build_knot_section(self):
        tk.Frame(self.panel, bg=FG_ORANGE, height=1).pack(fill=tk.X, padx=6, pady=6)
        self._sec("── Düğüm Vektörü ──")

        mode_row = tk.Frame(self.panel, bg=BG_PANEL)
        mode_row.pack(fill=tk.X, padx=10, pady=2)

        self.knot_mode_var = tk.StringVar(value='auto')
        tk.Radiobutton(mode_row, text="Otomatik (uniform clamped)",
                       variable=self.knot_mode_var, value='auto',
                       bg=BG_PANEL, fg=FG_GREY, selectcolor='#1a1a3a',
                       font=self.mono_s, command=self._on_knot_mode_change
                       ).pack(anchor='w')
        tk.Radiobutton(mode_row, text="Manuel giriş",
                       variable=self.knot_mode_var, value='manual',
                       bg=BG_PANEL, fg=FG_GREY, selectcolor='#1a1a3a',
                       font=self.mono_s, command=self._on_knot_mode_change
                       ).pack(anchor='w')

        self.knot_display = tk.Text(self.panel, height=3, width=34,
                                    bg=BG_BOX, fg='#ffff66',
                                    font=self.mono_s, state=tk.DISABLED,
                                    relief=tk.FLAT, padx=4, pady=3, wrap=tk.WORD)
        self.knot_display.pack(padx=8, pady=2, fill=tk.X)

        # Manual knot entry (hidden until manual mode chosen)
        self.knot_entry_frame = tk.Frame(self.panel, bg='#0e0e28')

        tk.Label(self.knot_entry_frame,
                 text="Düğüm değerlerini girin\n(boşluk veya virgülle ayırın):",
                 bg='#0e0e28', fg=FG_GREY, font=self.mono_s,
                 justify=tk.LEFT).pack(anchor='w', padx=6, pady=(4, 0))

        self.knot_entry_var = tk.StringVar()
        self.knot_entry_w   = tk.Entry(
            self.knot_entry_frame, textvariable=self.knot_entry_var,
            bg='#1a1a3a', fg='white', font=self.mono_s,
            insertbackground='white', relief=tk.FLAT)
        self.knot_entry_w.pack(fill=tk.X, padx=6, pady=2)
        self.knot_entry_w.bind('<Return>', lambda e: self._apply_manual_knots())

        kbr = tk.Frame(self.knot_entry_frame, bg='#0e0e28')
        kbr.pack(fill=tk.X, padx=6, pady=4)
        tk.Button(kbr, text="Uygula", bg='#003355', fg=FG_CYAN,
                  font=self.mono, relief=tk.FLAT,
                  command=self._apply_manual_knots, pady=2
                  ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 2))
        tk.Button(kbr, text="Otomatiğe Dön", bg='#330033', fg='#cc88ff',
                  font=self.mono, relief=tk.FLAT,
                  command=self._revert_auto_knots, pady=2
                  ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(2, 0))

        self.knot_err_lbl = tk.Label(self.panel, text='',
                                      bg=BG_PANEL, fg='#ff4444',
                                      font=self.mono_s, wraplength=270)
        self.knot_err_lbl.pack(fill=tk.X, padx=8)

    # ── Weight section (NURBS-specific) ───────────────────────────────────

    def _build_weight_section(self):
        tk.Frame(self.panel, bg=FG_ORANGE, height=1).pack(fill=tk.X, padx=6, pady=6)
        self._sec("── Ağırlıklar (wi) ──")

        # Live weight list
        self.wt_list_box = tk.Text(self.panel, height=6, width=34,
                                   bg=BG_BOX, fg='#ffcc55',
                                   font=self.mono_s, state=tk.DISABLED,
                                   relief=tk.FLAT, padx=4, pady=3)
        self.wt_list_box.pack(padx=8, pady=2, fill=tk.X)

        self._sec("── Ağırlık Düzenle ──")

        # Index
        row = tk.Frame(self.panel, bg=BG_PANEL)
        row.pack(fill=tk.X, padx=10, pady=2)
        tk.Label(row, text="İndeks:", bg=BG_PANEL, fg=FG_GREY,
                 font=self.mono, width=8, anchor='w').pack(side=tk.LEFT)
        self.wt_idx_var = tk.StringVar(value='0')
        tk.Entry(row, textvariable=self.wt_idx_var,
                 bg='#1a1a3a', fg='white', font=self.mono,
                 insertbackground='white', relief=tk.FLAT, width=5
                 ).pack(side=tk.LEFT, padx=3)

        # Weight value
        row2 = tk.Frame(self.panel, bg=BG_PANEL)
        row2.pack(fill=tk.X, padx=10, pady=2)
        tk.Label(row2, text="Ağırlık (w):", bg=BG_PANEL, fg=FG_GREY,
                 font=self.mono, width=12, anchor='w').pack(side=tk.LEFT)
        self.wt_val_var = tk.StringVar(value='1.0')
        self.wt_entry   = tk.Entry(row2, textvariable=self.wt_val_var,
                                   bg='#1a1a3a', fg='white', font=self.mono,
                                   insertbackground='white', relief=tk.FLAT, width=8)
        self.wt_entry.pack(side=tk.LEFT, padx=3)
        self.wt_entry.bind('<Return>', lambda e: self._apply_weight_edit())

        # Info label about weight effect
        tk.Label(self.panel,
                 text="w>1 → eğri yaklaşır  |  w<1 → uzaklaşır\n"
                      "w=0 → nokta etkisiz  |  w=1 → standart",
                 bg=BG_PANEL, fg='#888888', font=self.mono_s,
                 justify=tk.LEFT
                 ).pack(anchor='w', padx=10, pady=(0, 2))

        tk.Button(self.panel, text="Ağırlığı Güncelle",
                  bg='#332200', fg=FG_ORANGE,
                  font=self.mono, relief=tk.FLAT,
                  command=self._apply_weight_edit, pady=4
                  ).pack(fill=tk.X, padx=8, pady=3)

        # Reset all weights to 1.0
        tk.Button(self.panel, text="Tüm Ağırlıkları 1.0 Yap",
                  bg='#1a1a00', fg='#aaaaaa',
                  font=self.mono_s, relief=tk.FLAT,
                  command=self._reset_weights, pady=3
                  ).pack(fill=tk.X, padx=8, pady=(0, 4))

        self.wt_err_lbl = tk.Label(self.panel, text='',
                                    bg=BG_PANEL, fg='#ff4444',
                                    font=self.mono_s, wraplength=270)
        self.wt_err_lbl.pack(fill=tk.X, padx=8)

    # ── Control-points list section ────────────────────────────────────────

    def _build_info_section(self):
        tk.Frame(self.panel, bg=FG_ORANGE, height=1).pack(fill=tk.X, padx=6, pady=6)
        self._sec("── Kontrol Noktaları ──")
        self.pts_list_box = tk.Text(self.panel, height=8, width=34,
                                    bg=BG_BOX, fg='#aaffcc',
                                    font=self.mono_s, state=tk.DISABLED,
                                    relief=tk.FLAT, padx=4, pady=3)
        self.pts_list_box.pack(padx=8, pady=2, fill=tk.X)

    # ── Edit / delete section ──────────────────────────────────────────────

    def _build_points_section(self):
        tk.Frame(self.panel, bg=FG_ORANGE, height=1).pack(fill=tk.X, padx=6, pady=6)
        self._sec("── Son Noktayı Sil ──")

        tk.Button(self.panel, text="Son Noktayı Sil",
                  bg='#2a0000', fg='#ff8888',
                  font=self.mono, relief=tk.FLAT,
                  command=self._delete_last, pady=4
                  ).pack(fill=tk.X, padx=8, pady=3)

        self._sec("── Nokta Koordinatı Düzenle ──")

        row = tk.Frame(self.panel, bg=BG_PANEL)
        row.pack(fill=tk.X, padx=10, pady=2)
        tk.Label(row, text="İndeks:", bg=BG_PANEL, fg=FG_GREY,
                 font=self.mono, width=8, anchor='w').pack(side=tk.LEFT)
        self.edit_idx_var = tk.StringVar(value='0')
        tk.Entry(row, textvariable=self.edit_idx_var,
                 bg='#1a1a3a', fg='white', font=self.mono,
                 insertbackground='white', relief=tk.FLAT, width=5
                 ).pack(side=tk.LEFT, padx=3)

        for axis, attr in [('X', 'edit_x_var'), ('Y', 'edit_y_var')]:
            r2 = tk.Frame(self.panel, bg=BG_PANEL)
            r2.pack(fill=tk.X, padx=10, pady=1)
            tk.Label(r2, text=f"{axis}:", bg=BG_PANEL, fg=FG_GREY,
                     font=self.mono, width=3, anchor='w').pack(side=tk.LEFT)
            var = tk.StringVar()
            setattr(self, attr, var)
            tk.Entry(r2, textvariable=var,
                     bg='#1a1a3a', fg='white', font=self.mono,
                     insertbackground='white', relief=tk.FLAT, width=10
                     ).pack(side=tk.LEFT, padx=3)

        btn_row = tk.Frame(self.panel, bg=BG_PANEL)
        btn_row.pack(fill=tk.X, padx=8, pady=4)
        tk.Button(btn_row, text="Koordinatı Güncelle",
                  bg='#003322', fg='#44ffaa',
                  font=self.mono, relief=tk.FLAT,
                  command=self._apply_coord_edit, pady=4
                  ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 2))
        self.mouse_edit_btn = tk.Button(
                  btn_row, text="Mouse ile Güncelle",
                  bg='#1a1a00', fg='#ffff44',
                  font=self.mono, relief=tk.FLAT,
                  command=self._activate_click_edit, pady=4)
        self.mouse_edit_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(2, 0))

        self.edit_err_lbl = tk.Label(self.panel, text='',
                                      bg=BG_PANEL, fg='#ff4444',
                                      font=self.mono_s, wraplength=270)
        self.edit_err_lbl.pack(fill=tk.X, padx=8)

    # ── Canvas area ────────────────────────────────────────────────────────

    def _build_canvas_area(self):
        self.status_var = tk.StringVar()
        tk.Label(self.right, textvariable=self.status_var,
                 bg='#080818', fg='#7777aa',
                 font=self.mono_s, anchor='w', padx=10, pady=5
                 ).pack(side=tk.BOTTOM, fill=tk.X)

        self.canvas = tk.Canvas(self.right, bg=CANVAS_BG,
                                highlightthickness=1,
                                highlightbackground='#3a2a1e',
                                cursor='crosshair')
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.canvas.bind('<Button-1>',        self._on_click)
        self.canvas.bind('<B1-Motion>',       self._on_drag)
        self.canvas.bind('<ButtonRelease-1>', self._on_release)
        self.canvas.bind('<Motion>',          self._on_motion)
        self.canvas.bind('<Configure>',       lambda e: self._redraw())
        # Scroll wheel over canvas → change weight of nearest point
        self.canvas.bind('<MouseWheel>',      self._on_canvas_scroll)
        self.root.bind('<Escape>',            lambda _: self._cancel_click_edit())

    # ── Canvas event handlers ──────────────────────────────────────────────

    def _on_click(self, event):
        x, y = float(event.x), float(event.y)

        # Click-edit mode: move the selected point to the clicked position
        if self.click_edit_idx is not None:
            self.ctrl_pts[self.click_edit_idx] = (x, y)
            self._cancel_click_edit()
            self._auto_knots()
            self._refresh_all()
            self._redraw()
            return

        # Hit-test existing points (drag start)
        for i, p in enumerate(self.ctrl_pts):
            if math.hypot(p[0] - x, p[1] - y) <= 12:
                self.drag_idx = i
                return
        # Add new control point with default weight
        self.ctrl_pts.append((x, y))
        self.weights.append(DEFAULT_W)
        self._auto_knots()
        self._refresh_all()
        self._redraw()

    def _on_drag(self, event):
        if self.drag_idx is None:
            return
        self.ctrl_pts[self.drag_idx] = (float(event.x), float(event.y))
        self._auto_knots()
        self._refresh_all()
        self._redraw()

    def _on_release(self, event):
        self.drag_idx = None

    def _on_motion(self, event):
        x, y = event.x, event.y
        self.mouse_lbl.config(text=f"Fare: ({x}, {y})")
        if self._can_draw():
            t, pt = self._closest_t(x, y)
            self.hover_t  = t
            self.hover_pt = pt
            self.t_lbl.config(text=f"u = {t:.4f}")
            if pt:
                self.bt_lbl.config(text=f"C(u) = ({pt[0]:.1f}, {pt[1]:.1f})")
            self.canvas.delete('hover')
            self._draw_hover(t, pt)

    def _on_canvas_scroll(self, event):
        """Mouse wheel on canvas changes the weight of the nearest control point."""
        if not self.ctrl_pts:
            return
        x, y = float(event.x), float(event.y)
        # Find nearest point
        idx = min(range(len(self.ctrl_pts)),
                  key=lambda i: math.hypot(self.ctrl_pts[i][0] - x,
                                           self.ctrl_pts[i][1] - y))
        delta = 0.1 if event.delta > 0 else -0.1
        new_w = max(0.0, round(self.weights[idx] + delta, 4))
        self.weights[idx] = new_w
        # Sync the weight edit fields
        self.wt_idx_var.set(str(idx))
        self.wt_val_var.set(f"{new_w:.3f}")
        self._refresh_all()
        self._redraw()

    # ── Degree change ──────────────────────────────────────────────────────

    def _on_degree_change(self):
        try:
            d = int(self.degree_var.get())
        except (ValueError, tk.TclError):
            return
        n = len(self.ctrl_pts)
        if d < 1:
            d = 1
        max_deg = max(1, n - 1) if n > 1 else 1
        if n > 1 and d > max_deg:
            self.degree_err_lbl.config(
                text=f"Uyarı: {n} nokta için maks. derece {max_deg}.")
        else:
            self.degree_err_lbl.config(text='')
        self.degree = d
        self.degree_var.set(d)
        self.order_lbl.config(text=str(d + 1))
        if self.knot_mode == 'auto':
            self._auto_knots()
        self._refresh_all()
        self._redraw()

    # ── Knot vector management ─────────────────────────────────────────────

    def _auto_knots(self):
        n = len(self.ctrl_pts)
        if n == 0:
            self.knots = []
            return
        max_deg = n - 1
        if self.degree > max_deg:
            self.degree = max(1, max_deg)
            self.degree_var.set(self.degree)
            self.order_lbl.config(text=str(self.degree + 1))
        self.knots = make_uniform_knots(n, self.degree)

    def _on_knot_mode_change(self):
        mode = self.knot_mode_var.get()
        self.knot_mode = mode
        if mode == 'manual':
            self.knot_entry_frame.pack(padx=8, pady=4, fill=tk.X,
                                       after=self.knot_display)
            self.knot_entry_var.set(
                ' '.join(f'{v:.4g}' for v in self.knots))
        else:
            self.knot_entry_frame.pack_forget()
            self._auto_knots()
            self.knot_err_lbl.config(text='')
            self._refresh_all()
            self._redraw()

    def _apply_manual_knots(self):
        vals = parse_float_list(self.knot_entry_var.get())
        if vals is None:
            self.knot_err_lbl.config(text="Hata: Geçersiz sayı formatı.")
            return
        ok, msg = validate_knots(vals, len(self.ctrl_pts), self.degree)
        if not ok:
            self.knot_err_lbl.config(text=f"Hata: {msg}")
            return
        self.knot_err_lbl.config(text='')
        self.knots     = vals
        self.knot_mode = 'manual'
        self._refresh_all()
        self._redraw()

    def _revert_auto_knots(self):
        self.knot_mode_var.set('auto')
        self.knot_mode = 'auto'
        self.knot_entry_frame.pack_forget()
        self.knot_err_lbl.config(text='')
        self._auto_knots()
        self._refresh_all()
        self._redraw()

    # ── Weight management ──────────────────────────────────────────────────

    def _apply_weight_edit(self):
        self.wt_err_lbl.config(text='')
        try:
            idx = int(self.wt_idx_var.get())
            w   = float(self.wt_val_var.get())
        except ValueError:
            self.wt_err_lbl.config(text="Hata: Geçersiz değer.")
            return
        if idx < 0 or idx >= len(self.weights):
            self.wt_err_lbl.config(
                text=f"Hata: İndeks 0–{len(self.weights)-1} arasında olmalı.")
            return
        if w < 0:
            self.wt_err_lbl.config(text="Hata: Ağırlık ≥ 0 olmalı.")
            return
        self.weights[idx] = w
        self._refresh_all()
        self._redraw()

    def _reset_weights(self):
        self.weights = [DEFAULT_W] * len(self.ctrl_pts)
        self._refresh_all()
        self._redraw()

    # ── Click-edit mode ────────────────────────────────────────────────────

    def _activate_click_edit(self):
        self.edit_err_lbl.config(text='')
        try:
            idx = int(self.edit_idx_var.get())
        except ValueError:
            self.edit_err_lbl.config(text="Hata: Geçersiz indeks.")
            return
        if idx < 0 or idx >= len(self.ctrl_pts):
            self.edit_err_lbl.config(
                text=f"Hata: İndeks 0–{len(self.ctrl_pts)-1} arasında olmalı.")
            return
        self.click_edit_idx = idx
        self.canvas.config(cursor='tcross')
        self.mouse_edit_btn.config(bg='#554400', fg='#ffff00',
                                    text="İptal (ESC)")
        self.mouse_edit_btn.config(command=self._cancel_click_edit)
        self._refresh_all()
        self._redraw()

    def _cancel_click_edit(self):
        self.click_edit_idx = None
        self.canvas.config(cursor='crosshair')
        self.mouse_edit_btn.config(bg='#1a1a00', fg='#ffff44',
                                    text="Mouse ile Güncelle")
        self.mouse_edit_btn.config(command=self._activate_click_edit)
        self._refresh_all()
        self._redraw()

    # ── Control-point edit / delete ────────────────────────────────────────

    def _delete_last(self):
        if self.ctrl_pts:
            self.ctrl_pts.pop()
            self.weights.pop()
            self._auto_knots()
            self._refresh_all()
            self._redraw()

    def _apply_coord_edit(self):
        self.edit_err_lbl.config(text='')
        try:
            idx = int(self.edit_idx_var.get())
            x   = float(self.edit_x_var.get())
            y   = float(self.edit_y_var.get())
        except ValueError:
            self.edit_err_lbl.config(text="Hata: Geçersiz değer.")
            return
        if idx < 0 or idx >= len(self.ctrl_pts):
            self.edit_err_lbl.config(
                text=f"Hata: İndeks 0–{len(self.ctrl_pts)-1} arasında olmalı.")
            return
        self.ctrl_pts[idx] = (x, y)
        self._auto_knots()
        self._refresh_all()
        self._redraw()

    # ── Reset ──────────────────────────────────────────────────────────────

    def _reset(self):
        self.ctrl_pts       = []
        self.weights        = []
        self.degree         = 3
        self.knots          = []
        self.knot_mode      = 'auto'
        self.drag_idx       = None
        self.hover_t        = None
        self.hover_pt       = None
        self.click_edit_idx = None

        self.degree_var.set(3)
        self.order_lbl.config(text='4')
        self.knot_mode_var.set('auto')
        self.knot_entry_frame.pack_forget()
        self.canvas.config(cursor='crosshair')
        self.mouse_edit_btn.config(bg='#1a1a00', fg='#ffff44',
                                    text="Mouse ile Güncelle",
                                    command=self._activate_click_edit)

        for lbl in (self.degree_err_lbl, self.knot_err_lbl,
                    self.wt_err_lbl, self.edit_err_lbl):
            lbl.config(text='')

        self.t_lbl.config(text="u = -")
        self.bt_lbl.config(text="C(u) = (-, -)")
        self.len_lbl.config(text="L ≈ -")
        self.mouse_lbl.config(text="Fare: (-, -)")

        self._refresh_all()
        self._redraw()

    # ── Info panel refresh ─────────────────────────────────────────────────

    def _refresh_all(self):
        n = len(self.ctrl_pts)
        self.npts_lbl.config(text=f"Kontrol noktası: {n}")
        self.deg_lbl.config(text=f"Derece: {self.degree}  Order: {self.degree+1}")
        self.order_lbl.config(text=str(self.degree + 1))

        # Knot vector display
        self.knot_display.configure(state=tk.NORMAL)
        self.knot_display.delete('1.0', tk.END)
        self.knot_display.insert(
            tk.END,
            ('[ ' + '  '.join(f'{v:.3g}' for v in self.knots) + ' ]')
            if self.knots else '(henüz yok)')
        self.knot_display.configure(state=tk.DISABLED)

        # Weight list
        self.wt_list_box.configure(state=tk.NORMAL)
        self.wt_list_box.delete('1.0', tk.END)
        if self.weights:
            lines = [f"w{i:2d}: {w:7.4f}  {'█' * min(20, max(1, round(w*4)))}"
                     for i, w in enumerate(self.weights)]
            self.wt_list_box.insert(tk.END, '\n'.join(lines))
        else:
            self.wt_list_box.insert(tk.END, '(henüz ağırlık yok)')
        self.wt_list_box.configure(state=tk.DISABLED)

        # Control-point coordinate list
        self.pts_list_box.configure(state=tk.NORMAL)
        self.pts_list_box.delete('1.0', tk.END)
        if self.ctrl_pts:
            lines = [f"P{i:2d}: ({p[0]:7.1f},{p[1]:7.1f})  w={self.weights[i]:.3f}"
                     for i, p in enumerate(self.ctrl_pts)]
            self.pts_list_box.insert(tk.END, '\n'.join(lines))
        else:
            self.pts_list_box.insert(tk.END, '(henüz nokta yok)')
        self.pts_list_box.configure(state=tk.DISABLED)

        # Arc length
        if self._can_draw():
            self.len_lbl.config(text=f"L ≈ {self._arc_length():.1f} piksel")
        else:
            self.len_lbl.config(text="L ≈ -")

        # Status bar
        min_pts = self.degree + 1
        if self.click_edit_idx is not None:
            msg = (f"Mouse düzenleme modu: P{self.click_edit_idx} için "
                   f"yeni konumu tıklayın  |  ESC veya İptal ile çıkın")
        elif n == 0:
            msg = "Tuvale tıklayarak kontrol noktası ekleyin."
        elif n < min_pts:
            msg = f"{n} nokta var. Derece {self.degree} için en az {min_pts} nokta gerekli."
        else:
            msg = (f"{n} nokta  |  Derece: {self.degree}"
                   f"  |  Sürükle: taşı  |  Tekerlek: ağırlık değiştir  |  Tıkla: yeni nokta")
        self.status_var.set(msg)

    # ── NURBS evaluation helpers ───────────────────────────────────────────

    def _can_draw(self):
        n = len(self.ctrl_pts)
        return (n >= self.degree + 1
                and len(self.knots) == n + self.degree + 1
                and len(self.weights) == n)

    def _eval(self, t):
        return nurbs_point(t, self.ctrl_pts, self.weights, self.knots, self.degree)

    def _closest_t(self, mx, my, n=300):
        t0 = self.knots[self.degree]
        t1 = self.knots[-(self.degree + 1)]
        if t0 >= t1:
            return 0.0, None
        best_t, best_d, best_pt = t0, float('inf'), None
        for i in range(n + 1):
            t  = t0 + (t1 - t0) * i / n
            pt = self._eval(t)
            d  = (pt[0] - mx)**2 + (pt[1] - my)**2
            if d < best_d:
                best_t, best_d, best_pt = t, d, pt
        return best_t, best_pt

    def _arc_length(self, n=300):
        t0   = self.knots[self.degree]
        t1   = self.knots[-(self.degree + 1)]
        if t0 >= t1:
            return 0.0
        total = 0.0
        prev  = self._eval(t0)
        for i in range(1, n + 1):
            t    = t0 + (t1 - t0) * i / n
            curr = self._eval(t)
            dx, dy = curr[0] - prev[0], curr[1] - prev[1]
            total += math.sqrt(dx * dx + dy * dy)
            prev = curr
        return total

    # ── Canvas drawing ─────────────────────────────────────────────────────

    def _redraw(self):
        self.canvas.delete('all')
        self._draw_grid()
        if self._can_draw():
            self._draw_control_polygon()
            self._draw_curve()
        self._draw_points()
        if self._can_draw() and self.hover_pt:
            self._draw_hover(self.hover_t, self.hover_pt)

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
        if len(self.ctrl_pts) < 2:
            return
        for i in range(len(self.ctrl_pts) - 1):
            a, b = self.ctrl_pts[i], self.ctrl_pts[i + 1]
            self.canvas.create_line(
                a[0], a[1], b[0], b[1],
                fill=POLY_COL, dash=(5, 5), width=1)

    def _draw_curve(self):
        t0 = self.knots[self.degree]
        t1 = self.knots[-(self.degree + 1)]
        if t0 >= t1:
            return
        coords = []
        for i in range(STEPS + 1):
            t = t0 + (t1 - t0) * i / STEPS
            coords.extend(self._eval(t))
        if len(coords) >= 4:
            self.canvas.create_line(*coords, fill=CURVE_COL, width=2, smooth=False)

    def _draw_points(self):
        for i, p in enumerate(self.ctrl_pts):
            color         = POINT_PALETTE[i % len(POINT_PALETTE)]
            w             = self.weights[i] if i < len(self.weights) else DEFAULT_W
            # Radius grows with weight; zero-weight → very small ring
            r_fill        = max(3, min(BASE_RADIUS + int(w * WEIGHT_SCALE), 20))
            is_drag       = (i == self.drag_idx)
            is_click_edit = (i == self.click_edit_idx)

            # Drag highlight ring (yellow)
            if is_drag:
                self.canvas.create_oval(
                    p[0]-r_fill-5, p[1]-r_fill-5,
                    p[0]+r_fill+5, p[1]+r_fill+5,
                    outline='#ffff00', width=2, fill='')

            # Click-edit double ring
            if is_click_edit:
                self.canvas.create_oval(
                    p[0]-r_fill-8, p[1]-r_fill-8,
                    p[0]+r_fill+8, p[1]+r_fill+8,
                    outline='#ffff00', width=2, fill='')
                self.canvas.create_oval(
                    p[0]-r_fill-3, p[1]-r_fill-3,
                    p[0]+r_fill+3, p[1]+r_fill+3,
                    outline='#ffaa00', width=1, fill='')

            # Weight indicator ring (orange, radius proportional to weight)
            if abs(w - DEFAULT_W) > 0.001:
                r_ring = max(r_fill + 3, int(r_fill * 1.4))
                self.canvas.create_oval(
                    p[0]-r_ring, p[1]-r_ring,
                    p[0]+r_ring, p[1]+r_ring,
                    outline=WEIGHT_COL,
                    width=max(1, min(3, int(w))),
                    fill='')

            # Zero-weight: draw with cross
            if w == 0.0:
                self.canvas.create_line(
                    p[0]-r_fill, p[1], p[0]+r_fill, p[1],
                    fill='#888888', width=2)
                self.canvas.create_line(
                    p[0], p[1]-r_fill, p[0], p[1]+r_fill,
                    fill='#888888', width=2)
                self.canvas.create_oval(
                    p[0]-r_fill, p[1]-r_fill, p[0]+r_fill, p[1]+r_fill,
                    fill='', outline='#888888', width=1)
            else:
                self.canvas.create_oval(
                    p[0]-r_fill, p[1]-r_fill, p[0]+r_fill, p[1]+r_fill,
                    fill=color, outline='white', width=1)

            # Label: point name + weight
            self.canvas.create_text(
                p[0]+r_fill+6, p[1]-r_fill-4,
                text=f"P{i}({p[0]:.0f},{p[1]:.0f}) w={w:.2f}",
                fill=color, font=('Courier', 8), anchor='w')

    def _draw_hover(self, t, pt):
        if pt is None:
            return
        x, y = pt
        r = 4
        self.canvas.create_oval(
            x-r, y-r, x+r, y+r,
            fill='white', outline=CURVE_COL, width=2,
            tags='hover')
        self.canvas.create_text(
            x+r+6, y,
            text=f"u={t:.3f}",
            fill='white', font=('Courier', 8),
            anchor='w', tags='hover')


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    root = tk.Tk()
    NURBSEditor(root)
    root.mainloop()


if __name__ == '__main__':
    main()
