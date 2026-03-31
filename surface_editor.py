"""
surface_editor.py  –  Parametrik Yüzey Editörü (3B)
Bezier / B-Spline / NURBS tensor-product yüzeyleri

UI dili: Türkçe | Kod ve yorumlar: İngilizce
Python 3.8+  –  yalnızca standart kütüphane (tkinter + math)

Ders notuna göre matematiksel formüller:
  Bezier:   S(u,v) = Σᵢ Σⱼ Pᵢⱼ · Bᵢₙ(u) · Bⱼₘ(v)
  B-Spline: P(u,v) = Σᵢ Σⱼ Pᵢⱼ · Nᵢₖ(u) · Nⱼₗ(v)
  NURBS:    S(u,v) = Σᵢ Σⱼ Pᵢⱼ · Rᵢₖⱼₗ(u,v)
            Rᵢₖⱼₗ = Wᵢⱼ·Nᵢₖ(u)·Nⱼₗ(v) / Σᵣ Σₛ Wᵣₛ·Nᵣₖ(u)·Nₛₗ(v)

3B → 2B projeksiyon (ders notundan):
  p'(y', z') = [0.7071(−x+y),  0.4082(x+y+2z)]
"""

import tkinter as tk
from tkinter import font as tkfont
import math
import copy

# ── Renk paleti (diğer editörlerle uyumlu) ────────────────────────────────────
BG_DARK   = '#0d0d1e'
BG_PANEL  = '#0a0a18'
BG_BOX    = '#0e0e22'
FG_CYAN   = '#00ffff'
FG_YEL    = '#ffdd77'
FG_GREY   = '#aaaacc'

CANVAS_BG = '#1a1a2e'
GRID_COL  = '#1e1e40'

SURF_COL  = {'bezier': '#00ffff', 'bspline': '#00ff88', 'nurbs': '#ff8800'}
MESH_COL  = '#2a3d55'
PT_NORMAL = '#ffdd44'
PT_SEL    = '#ff4444'

U_STEPS = 20   # her u-parametrik eğrisi örnekleme sayısı
V_STEPS = 20   # her v-parametrik eğrisi örnekleme sayısı


# ──────────────────────────────────────────────────────────────────────────────
# Matematik
# ──────────────────────────────────────────────────────────────────────────────

def _comb(n, k):
    if k < 0 or k > n:
        return 0
    if k == 0 or k == n:
        return 1
    k = min(k, n - k)
    r = 1
    for j in range(k):
        r = r * (n - j) // (j + 1)
    return r


def bernstein(n, i, t):
    """Bernstein baz polinomu B_{i,n}(t)."""
    if t == 0.0:
        return 1.0 if i == 0 else 0.0
    if t == 1.0:
        return 1.0 if i == n else 0.0
    return _comb(n, i) * (t ** i) * ((1.0 - t) ** (n - i))


def cox_de_boor(t, i, p, knots):
    """Özyinelemli Cox–de Boor B-Spline baz fonksiyonu N_{i,p}(t)."""
    if p == 0:
        if knots[i] <= t < knots[i + 1]:
            return 1.0
        if t == knots[-1] and knots[i] <= t <= knots[i + 1]:
            return 1.0
        return 0.0
    d1 = knots[i + p]     - knots[i]
    d2 = knots[i + p + 1] - knots[i + 1]
    c1 = (t - knots[i])          / d1 * cox_de_boor(t, i,     p - 1, knots) if d1 else 0.0
    c2 = (knots[i + p + 1] - t)  / d2 * cox_de_boor(t, i + 1, p - 1, knots) if d2 else 0.0
    return c1 + c2


def make_knots(n_pts, degree):
    """Açık/sıkıştırılmış düzgün düğüm vektörü üretir."""
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


def eval_surface(u, v, ctrl, weights, ku, kv, du, dv, stype):
    """
    (u,v) parametresinde yüzey noktasını hesapla.
    Döndürür: (x, y, z)
    """
    rows = len(ctrl)
    cols = len(ctrl[0])

    if stype == 'bezier':
        n, m = rows - 1, cols - 1
        sx = sy = sz = 0.0
        for i in range(rows):
            bu = bernstein(n, i, u)
            if bu == 0.0:
                continue
            for j in range(cols):
                bv = bernstein(m, j, v)
                w  = bu * bv
                sx += w * ctrl[i][j][0]
                sy += w * ctrl[i][j][1]
                sz += w * ctrl[i][j][2]
        return (sx, sy, sz)

    elif stype == 'bspline':
        sx = sy = sz = 0.0
        for i in range(rows):
            nu = cox_de_boor(u, i, du, ku)
            if nu == 0.0:
                continue
            for j in range(cols):
                nv = cox_de_boor(v, j, dv, kv)
                w  = nu * nv
                sx += w * ctrl[i][j][0]
                sy += w * ctrl[i][j][1]
                sz += w * ctrl[i][j][2]
        return (sx, sy, sz)

    else:  # nurbs
        wx = wy = wz = ws = 0.0
        for i in range(rows):
            nu = cox_de_boor(u, i, du, ku)
            if nu == 0.0:
                continue
            for j in range(cols):
                nv  = cox_de_boor(v, j, dv, kv)
                wij = weights[i][j]
                bw  = nu * nv * wij
                wx += bw * ctrl[i][j][0]
                wy += bw * ctrl[i][j][1]
                wz += bw * ctrl[i][j][2]
                ws += bw
        if ws == 0.0:
            return (ctrl[0][0][0], ctrl[0][0][1], ctrl[0][0][2])
        return (wx / ws, wy / ws, wz / ws)


# ── 3B → 2B projeksiyon ───────────────────────────────────────────────────────

def project(x, y, z, angle_y, scale, cx, cy):
    """
    Y ekseninde döndür, ardından ders notundaki izometrik projeksiyonu uygula:
      p'(y', z') = [0.7071(−x+y),  0.4082(x+y+2z)]
    Ekran y'si tersine çevrilir (+z yukarı yönde görünür).
    """
    ca, sa = math.cos(angle_y), math.sin(angle_y)
    rx =  ca * x + sa * z
    ry =  y
    rz = -sa * x + ca * z
    sx = 0.7071  * (-rx + ry)         * scale + cx
    sy = -0.4082 * (rx  + ry + 2*rz)  * scale + cy
    return (sx, sy)


# ── Ön tanımlı yüzeyler (ders notundan) ──────────────────────────────────────

def _make_preset_1():
    """Ders notundaki birinci NURBS yüzeyi (5×2 kontrol ağı, derece 3×1)."""
    return {
        'name'   : 'NURBS Yüzey 1 (Ders Notu)',
        'ctrl'   : [
            [[  0,   0,   0], [  0, 200,   0]],
            [[ 50,   0,  50], [ 50, 200,  50]],
            [[100,   0,   0], [100, 200,   0]],
            [[150,   0,  50], [150, 200,  50]],
            [[200,   0,   0], [200, 200,   0]],
        ],
        'weights': [[1.0, 1.0] for _ in range(5)],
        'knots_u': [0, 0, 0, 0, 0.5, 1, 1, 1, 1],
        'knots_v': [0, 0, 1, 1],
        'deg_u'  : 3,
        'deg_v'  : 1,
        'stype'  : 'nurbs',
    }


def _make_preset_2():
    """Ders notundaki ikinci NURBS yüzeyi (5×2 kontrol ağı, derece 3×1)."""
    return {
        'name'   : 'NURBS Yüzey 2 (Ders Notu)',
        'ctrl'   : [
            [[100,   0,  100], [100, 200,  100]],
            [[150,   0,   50], [150, 200,   50]],
            [[100,   0,    0], [100, 200,    0]],
            [[150,   0,  -50], [150, 200,  -50]],
            [[100,   0, -100], [100, 200, -100]],
        ],
        'weights': [[1.0, 1.0] for _ in range(5)],
        'knots_u': [0, 0, 0, 0, 0.5, 1, 1, 1, 1],
        'knots_v': [0, 0, 1, 1],
        'deg_u'  : 3,
        'deg_v'  : 1,
        'stype'  : 'nurbs',
    }


def _make_default():
    """4×4 bikübik Bezier yüzeyi – dalgalı varsayılan şekil."""
    pts = []
    for i in range(4):
        row = []
        for j in range(4):
            x = (i - 1.5) * 60
            z = (j - 1.5) * 60
            y = 40.0 * math.sin(i * math.pi / 3.0) * math.cos(j * math.pi / 3.0)
            row.append([x, y, z])
        pts.append(row)
    ku = make_knots(4, 3)
    kv = make_knots(4, 3)
    return {
        'name'   : 'Bezier 4×4 (Varsayılan)',
        'ctrl'   : pts,
        'weights': [[1.0] * 4 for _ in range(4)],
        'knots_u': ku,
        'knots_v': kv,
        'deg_u'  : 3,
        'deg_v'  : 3,
        'stype'  : 'bezier',
    }


# ──────────────────────────────────────────────────────────────────────────────
# Ana editör sınıfı
# ──────────────────────────────────────────────────────────────────────────────

class SurfaceEditor:

    def __init__(self, root):
        self.root = root
        self.root.title("Parametrik Yüzey Editörü – Bezier / B-Spline / NURBS")
        self.root.minsize(1200, 680)
        self.root.configure(bg=BG_DARK)

        # Görünüm durumu
        self.angle_y = math.radians(-25)
        self.scale   = 2.2
        self._drag_x = None

        # Yüzey verisi
        data = _make_default()
        self.ctrl    = data['ctrl']
        self.weights = data['weights']
        self.knots_u = data['knots_u']
        self.knots_v = data['knots_v']
        self.deg_u   = data['deg_u']
        self.deg_v   = data['deg_v']
        self.stype   = data['stype']

        # Seçim
        self.sel_i = None
        self.sel_j = None

        # Fontlar
        self.mono    = tkfont.Font(family='Courier', size=9)
        self.mono_b  = tkfont.Font(family='Courier', size=9,  weight='bold')
        self.mono_s  = tkfont.Font(family='Courier', size=8)
        self.title_f = tkfont.Font(family='Courier', size=10, weight='bold')

        self._build_ui()
        self._refresh_panel()

    # ── UI yapısı ─────────────────────────────────────────────────────────────

    def _build_ui(self):
        outer = tk.Frame(self.root, bg=BG_DARK)
        outer.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        self.left = tk.Frame(outer, bg=BG_PANEL, width=305)
        self.left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 4))
        self.left.pack_propagate(False)

        self.right = tk.Frame(outer, bg=BG_DARK)
        self.right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._build_left_panel()
        self._build_canvas_area()

    # ── Sol panel ─────────────────────────────────────────────────────────────

    def _build_left_panel(self):
        vsb = tk.Scrollbar(self.left, orient=tk.VERTICAL)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        self._pcv = tk.Canvas(self.left, bg=BG_PANEL,
                              yscrollcommand=vsb.set, highlightthickness=0)
        self._pcv.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.config(command=self._pcv.yview)

        self.panel = tk.Frame(self._pcv, bg=BG_PANEL)
        self._pcv.create_window((0, 0), window=self.panel, anchor='nw', width=287)
        self.panel.bind('<Configure>',
                        lambda e: self._pcv.configure(
                            scrollregion=self._pcv.bbox('all')))

        def _mw(ev):
            self._pcv.yview_scroll(int(-1 * ev.delta / 120), 'units')
        self._pcv.bind('<Enter>', lambda e: self._pcv.bind_all('<MouseWheel>', _mw))
        self._pcv.bind('<Leave>', lambda e: self._pcv.unbind_all('<MouseWheel>'))

        self._build_panel_content()

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

    def _build_panel_content(self):
        # Başlık
        tk.Label(self.panel, text="YÜZEY EDİTÖRÜ",
                 bg=BG_PANEL, fg=FG_CYAN, font=self.title_f
                 ).pack(pady=(10, 4))
        tk.Frame(self.panel, bg=FG_CYAN, height=1).pack(fill=tk.X, padx=6, pady=2)

        # ── Yüzey tipi ────────────────────────────────────────────────────────
        self._sec("── Yüzey Tipi ──")
        self.stype_var = tk.StringVar(value=self.stype)
        tf = tk.Frame(self.panel, bg=BG_PANEL)
        tf.pack(padx=8, pady=4, fill=tk.X)
        for lbl, val, col in [
            ('Bezier',   'bezier',  '#00ffff'),
            ('B-Spline', 'bspline', '#00ff88'),
            ('NURBS',    'nurbs',   '#ff8800'),
        ]:
            tk.Radiobutton(tf, text=lbl, variable=self.stype_var, value=val,
                           bg=BG_PANEL, fg=col, selectcolor='#1a1a44',
                           activebackground=BG_PANEL, font=self.mono,
                           command=self._on_type_change,
                           ).pack(side=tk.LEFT, padx=4)

        # ── Ön tanımlı yüzeyler ───────────────────────────────────────────────
        self._sec("── Ön Tanımlı Yüzeyler ──")
        pf = tk.Frame(self.panel, bg=BG_PANEL)
        pf.pack(padx=8, pady=4, fill=tk.X)
        for name, fn in [
            ('Varsayılan', _make_default),
            ('Yüzey 1',   _make_preset_1),
            ('Yüzey 2',   _make_preset_2),
        ]:
            tk.Button(pf, text=name, bg='#1a1a3a', fg=FG_YEL,
                      font=self.mono, relief=tk.FLAT,
                      command=lambda f=fn: self._load_preset(f()),
                      pady=3
                      ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        # ── Derece ────────────────────────────────────────────────────────────
        self._sec("── Derece (u / v) ──")
        df = tk.Frame(self.panel, bg=BG_PANEL)
        df.pack(padx=8, pady=4, fill=tk.X)

        tk.Label(df, text="u:", bg=BG_PANEL, fg=FG_GREY, font=self.mono, width=3
                 ).pack(side=tk.LEFT)
        self.deg_u_var = tk.IntVar(value=self.deg_u)
        tk.Spinbox(df, from_=1, to=9, textvariable=self.deg_u_var, width=4,
                   bg='#1a1a3a', fg='white', font=self.mono,
                   command=self._on_degree_change, relief=tk.FLAT
                   ).pack(side=tk.LEFT, padx=4)

        tk.Label(df, text="v:", bg=BG_PANEL, fg=FG_GREY, font=self.mono, width=3
                 ).pack(side=tk.LEFT, padx=(6, 0))
        self.deg_v_var = tk.IntVar(value=self.deg_v)
        tk.Spinbox(df, from_=1, to=9, textvariable=self.deg_v_var, width=4,
                   bg='#1a1a3a', fg='white', font=self.mono,
                   command=self._on_degree_change, relief=tk.FLAT
                   ).pack(side=tk.LEFT, padx=4)

        tk.Label(df, text="(Bezier'de\netki yok)",
                 bg=BG_PANEL, fg='#554455', font=self.mono_s
                 ).pack(side=tk.LEFT, padx=6)

        # ── Kontrol ağı boyutu ────────────────────────────────────────────────
        self._sec("── Kontrol Ağı ──")
        self.grid_lbl = self._val_lbl("? × ? nokta")

        # ── Düğüm vektörleri ──────────────────────────────────────────────────
        self._sec("── u Düğüm Vektörü ──")
        self.ku_box = tk.Text(self.panel, height=2, width=34,
                              bg=BG_BOX, fg='#aaffaa', font=self.mono_s,
                              state=tk.DISABLED, relief=tk.FLAT, padx=4, pady=3)
        self.ku_box.pack(padx=8, pady=2, fill=tk.X)

        self._sec("── v Düğüm Vektörü ──")
        self.kv_box = tk.Text(self.panel, height=2, width=34,
                              bg=BG_BOX, fg='#aaffcc', font=self.mono_s,
                              state=tk.DISABLED, relief=tk.FLAT, padx=4, pady=3)
        self.kv_box.pack(padx=8, pady=2, fill=tk.X)

        tk.Frame(self.panel, bg=FG_CYAN, height=1).pack(fill=tk.X, padx=6, pady=8)

        # ── Seçili kontrol noktası ────────────────────────────────────────────
        self._sec("── Seçili Kontrol Noktası ──")
        self.sel_lbl = self._val_lbl("Seçili: -")

        cf = tk.Frame(self.panel, bg=BG_PANEL)
        cf.pack(padx=8, pady=4, fill=tk.X)

        self.ex_var = tk.StringVar()
        self.ey_var = tk.StringVar()
        self.ez_var = tk.StringVar()
        self.ew_var = tk.StringVar()

        for axis, var, attr, col in [
            ('X', self.ex_var, 'ex_entry', '#ff8888'),
            ('Y', self.ey_var, 'ey_entry', '#88ff88'),
            ('Z', self.ez_var, 'ez_entry', '#8888ff'),
            ('W', self.ew_var, 'ew_entry', '#ffdd44'),
        ]:
            row = tk.Frame(cf, bg=BG_PANEL)
            row.pack(fill=tk.X, pady=1)
            tk.Label(row, text=f"{axis}:", bg=BG_PANEL, fg=col,
                     font=self.mono_b, width=3
                     ).pack(side=tk.LEFT)
            ent = tk.Entry(row, textvariable=var,
                           bg='#1a1a3a', fg='white', font=self.mono,
                           insertbackground='white', relief=tk.FLAT, width=10)
            ent.pack(side=tk.LEFT, padx=3)
            ent.bind('<Return>', lambda e: self._apply_edit())
            setattr(self, attr, ent)

        tk.Button(self.panel, text="Uygula  [Enter]",
                  bg='#003355', fg=FG_CYAN, font=self.mono,
                  relief=tk.FLAT, command=self._apply_edit, pady=4
                  ).pack(fill=tk.X, padx=8, pady=(0, 4))

        # ── Projeksiyon formülü ───────────────────────────────────────────────
        tk.Frame(self.panel, bg='#333355', height=1).pack(fill=tk.X, padx=6, pady=8)
        self._sec("── 3B → 2B Projeksiyon ──")
        pb = tk.Text(self.panel, height=3, width=34,
                     bg=BG_BOX, fg='#88aaff', font=self.mono_s,
                     state=tk.DISABLED, relief=tk.FLAT, padx=4, pady=3)
        pb.pack(padx=8, pady=2, fill=tk.X)
        pb.configure(state=tk.NORMAL)
        pb.insert(tk.END,
                  "p'(y',z') =\n"
                  "  [0.7071(−x+y),\n"
                  "   0.4082(x+y+2z)]")
        pb.configure(state=tk.DISABLED)

        # ── Görünüm ipuçları ──────────────────────────────────────────────────
        self._sec("── Kontroller ──")
        tk.Label(self.panel,
                 text="Sol tık+sürükle : döndür\n"
                      "Fare tekerleği  : yakınlaştır\n"
                      "Sol tık (nokta) : seç / düzenle",
                 bg=BG_PANEL, fg=FG_GREY, font=self.mono_s,
                 justify=tk.LEFT, padx=8
                 ).pack(anchor='w', padx=8)

        # ── Sıfırla ───────────────────────────────────────────────────────────
        tk.Frame(self.panel, bg='#333355', height=1).pack(fill=tk.X, padx=6, pady=8)
        tk.Button(self.panel, text="Varsayılana Sıfırla",
                  bg='#2a0000', fg='#ff6666', font=self.mono_b,
                  relief=tk.FLAT, pady=7,
                  command=lambda: self._load_preset(_make_default())
                  ).pack(fill=tk.X, padx=6, pady=(0, 10))

    # ── Canvas alanı ──────────────────────────────────────────────────────────

    def _build_canvas_area(self):
        self.status_var = tk.StringVar(
            value="Sol tık ile kontrol noktası seçin  |  Sürükle: döndür  |  Tekerlek: yakınlaştır")
        tk.Label(self.right, textvariable=self.status_var,
                 bg='#080818', fg='#7777aa',
                 font=self.mono_s, anchor='w', padx=10, pady=5
                 ).pack(side=tk.BOTTOM, fill=tk.X)

        self.canvas = tk.Canvas(self.right, bg=CANVAS_BG,
                                highlightthickness=1,
                                highlightbackground='#2a2a5e',
                                cursor='crosshair')
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.canvas.bind('<Button-1>',        self._on_click)
        self.canvas.bind('<B1-Motion>',       self._on_drag)
        self.canvas.bind('<ButtonRelease-1>', self._on_release)
        self.canvas.bind('<MouseWheel>',      self._on_wheel)
        self.canvas.bind('<Configure>',       lambda e: self._redraw())

    # ── Olay işleyicileri ─────────────────────────────────────────────────────

    def _on_click(self, event):
        self._drag_x = event.x
        nearest = self._nearest_ctrl_pt(event.x, event.y)
        if nearest is not None:
            self.sel_i, self.sel_j = nearest
            self._refresh_panel()
            self._redraw()
            self.status_var.set(
                f"Seçili: P({self.sel_i},{self.sel_j}) = "
                f"({self.ctrl[self.sel_i][self.sel_j][0]:.1f}, "
                f"{self.ctrl[self.sel_i][self.sel_j][1]:.1f}, "
                f"{self.ctrl[self.sel_i][self.sel_j][2]:.1f})  "
                f"– X/Y/Z/W alanlarını düzenleyip Enter'a basın")

    def _on_drag(self, event):
        if self._drag_x is not None:
            dx = event.x - self._drag_x
            self.angle_y += dx * 0.007
            self._drag_x  = event.x
            self._redraw()

    def _on_release(self, event):
        self._drag_x = None

    def _on_wheel(self, event):
        factor = 1.1 if event.delta > 0 else 0.9
        self.scale *= factor
        self._redraw()

    # ── En yakın kontrol noktası ──────────────────────────────────────────────

    def _nearest_ctrl_pt(self, sx, sy, threshold=18):
        cx, cy   = self._canvas_center()
        best_d2  = threshold * threshold
        best     = None
        for i, row in enumerate(self.ctrl):
            for j, pt in enumerate(row):
                px, py = project(pt[0], pt[1], pt[2],
                                 self.angle_y, self.scale, cx, cy)
                d2 = (px - sx) ** 2 + (py - sy) ** 2
                if d2 < best_d2:
                    best_d2, best = d2, (i, j)
        return best

    def _canvas_center(self):
        w = max(self.canvas.winfo_width(),  2)
        h = max(self.canvas.winfo_height(), 2)
        return w // 2, h // 2

    # ── Preset yükleme ────────────────────────────────────────────────────────

    def _load_preset(self, data):
        self.ctrl    = copy.deepcopy(data['ctrl'])
        self.weights = copy.deepcopy(data['weights'])
        self.knots_u = list(data['knots_u'])
        self.knots_v = list(data['knots_v'])
        self.deg_u   = data['deg_u']
        self.deg_v   = data['deg_v']
        self.stype   = data['stype']
        self.sel_i   = None
        self.sel_j   = None
        self.stype_var.set(self.stype)
        self.deg_u_var.set(self.deg_u)
        self.deg_v_var.set(self.deg_v)
        self._auto_scale()
        self._refresh_panel()
        self._redraw()

    def _auto_scale(self):
        """Canvas'a sığacak şekilde ölçeği otomatik ayarlar."""
        cx, cy = self._canvas_center()
        pts = []
        for row in self.ctrl:
            for pt in row:
                px, py = project(pt[0], pt[1], pt[2], self.angle_y, 1.0, 0, 0)
                pts.append((px, py))
        if not pts:
            return
        span_x = max(p[0] for p in pts) - min(p[0] for p in pts) + 1
        span_y = max(p[1] for p in pts) - min(p[1] for p in pts) + 1
        w = max(self.canvas.winfo_width(),  400)
        h = max(self.canvas.winfo_height(), 400)
        self.scale = min(0.65 * w / span_x, 0.65 * h / span_y)

    # ── Tip / derece değişimi ─────────────────────────────────────────────────

    def _on_type_change(self):
        self.stype = self.stype_var.get()
        self._refresh_panel()
        self._redraw()

    def _on_degree_change(self):
        rows = len(self.ctrl)
        cols = len(self.ctrl[0])
        du = max(1, min(self.deg_u_var.get(), rows - 1))
        dv = max(1, min(self.deg_v_var.get(), cols - 1))
        self.deg_u = du
        self.deg_v = dv
        self.deg_u_var.set(du)
        self.deg_v_var.set(dv)
        self.knots_u = make_knots(rows, du)
        self.knots_v = make_knots(cols, dv)
        self._refresh_panel()
        self._redraw()

    # ── Nokta düzenleme ───────────────────────────────────────────────────────

    def _apply_edit(self):
        if self.sel_i is None:
            return
        try:
            x = float(self.ex_var.get())
            y = float(self.ey_var.get())
            z = float(self.ez_var.get())
            w = float(self.ew_var.get())
        except ValueError:
            return
        i, j = self.sel_i, self.sel_j
        self.ctrl[i][j]    = [x, y, z]
        self.weights[i][j] = max(1e-4, w)
        self._refresh_panel()
        self._redraw()

    # ── Panel yenileme ────────────────────────────────────────────────────────

    def _refresh_panel(self):
        rows = len(self.ctrl)
        cols = len(self.ctrl[0])
        self.grid_lbl.config(text=f"{rows} × {cols} kontrol noktası")

        def _set_box(box, vals):
            box.configure(state=tk.NORMAL)
            box.delete('1.0', tk.END)
            box.insert(tk.END,
                       '{' + ', '.join(f'{v:.4g}' for v in vals) + '}')
            box.configure(state=tk.DISABLED)

        # Ensure knot vectors are valid for current grid/degree
        if len(self.knots_u) != rows + self.deg_u + 1:
            self.knots_u = make_knots(rows, self.deg_u)
        if len(self.knots_v) != cols + self.deg_v + 1:
            self.knots_v = make_knots(cols, self.deg_v)

        _set_box(self.ku_box, self.knots_u)
        _set_box(self.kv_box, self.knots_v)

        if self.sel_i is not None:
            i, j = self.sel_i, self.sel_j
            pt   = self.ctrl[i][j]
            self.sel_lbl.config(text=f"Seçili: P({i},{j})")
            self.ex_var.set(f"{pt[0]:.2f}")
            self.ey_var.set(f"{pt[1]:.2f}")
            self.ez_var.set(f"{pt[2]:.2f}")
            self.ew_var.set(f"{self.weights[i][j]:.4f}")
        else:
            self.sel_lbl.config(text="Seçili: -")
            for v in (self.ex_var, self.ey_var, self.ez_var, self.ew_var):
                v.set("")

    # ── Yüzey hesaplama ───────────────────────────────────────────────────────

    def _compute_wireframe(self):
        """
        İzometrik eğri noktalarını hesaplar.
        Döndürür: (u_lines, v_lines)
        Her biri (x,y,z) üçlülerinden oluşan liste listesidir.
        """
        rows = len(self.ctrl)
        cols = len(self.ctrl[0])
        stype = self.stype
        du = min(self.deg_u, rows - 1)
        dv = min(self.deg_v, cols - 1)
        ku = self.knots_u if len(self.knots_u) == rows + du + 1 else make_knots(rows, du)
        kv = self.knots_v if len(self.knots_v) == cols + dv + 1 else make_knots(cols, dv)

        # Bezier için parametrik alan her zaman [0,1]
        if stype == 'bezier':
            u0, u1, v0, v1 = 0.0, 1.0, 0.0, 1.0
        else:
            u0, u1 = ku[du], ku[-(du + 1)]
            v0, v1 = kv[dv], kv[-(dv + 1)]

        # Sabit-v eğrileri (u boyunca tarama)
        u_lines = []
        for vi in range(V_STEPS + 1):
            tv = v0 + (v1 - v0) * vi / V_STEPS
            line = []
            for ui in range(U_STEPS + 1):
                tu = u0 + (u1 - u0) * ui / U_STEPS
                pt = eval_surface(tu, tv,
                                  self.ctrl, self.weights,
                                  ku, kv, du, dv, stype)
                line.append(pt)
            u_lines.append(line)

        # Sabit-u eğrileri (v boyunca tarama)
        v_lines = []
        for ui in range(U_STEPS + 1):
            tu = u0 + (u1 - u0) * ui / U_STEPS
            line = []
            for vi in range(V_STEPS + 1):
                tv = v0 + (v1 - v0) * vi / V_STEPS
                pt = eval_surface(tu, tv,
                                  self.ctrl, self.weights,
                                  ku, kv, du, dv, stype)
                line.append(pt)
            v_lines.append(line)

        return u_lines, v_lines

    # ── Canvas çizimi ─────────────────────────────────────────────────────────

    def _redraw(self):
        self.canvas.delete('all')
        self._draw_bg_grid()

        cx, cy  = self._canvas_center()
        ang     = self.angle_y
        sc      = self.scale
        col     = SURF_COL[self.stype]

        u_lines, v_lines = self._compute_wireframe()

        # Yüzey tel kafes – sabit-v eğrileri
        for line in u_lines:
            coords = []
            for x, y, z in line:
                px, py = project(x, y, z, ang, sc, cx, cy)
                coords.extend([px, py])
            if len(coords) >= 4:
                self.canvas.create_line(*coords, fill=col, width=1, smooth=False)

        # Yüzey tel kafes – sabit-u eğrileri
        for line in v_lines:
            coords = []
            for x, y, z in line:
                px, py = project(x, y, z, ang, sc, cx, cy)
                coords.extend([px, py])
            if len(coords) >= 4:
                self.canvas.create_line(*coords, fill=col, width=1, smooth=False)

        self._draw_control_mesh(cx, cy, ang, sc)
        self._draw_control_points(cx, cy, ang, sc)
        self._draw_axes_indicator(cx, cy, ang)
        self._draw_legend()

    def _draw_bg_grid(self):
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 2 or h < 2:
            return
        step = 50
        for x in range(0, w + step, step):
            self.canvas.create_line(x, 0, x, h, fill=GRID_COL, width=1)
        for y in range(0, h + step, step):
            self.canvas.create_line(0, y, w, y, fill=GRID_COL, width=1)

    def _draw_control_mesh(self, cx, cy, ang, sc):
        rows = len(self.ctrl)
        cols = len(self.ctrl[0])

        def proj(pt):
            return project(pt[0], pt[1], pt[2], ang, sc, cx, cy)

        # Satır çizgileri
        for i in range(rows):
            for j in range(cols - 1):
                a = proj(self.ctrl[i][j])
                b = proj(self.ctrl[i][j + 1])
                self.canvas.create_line(
                    a[0], a[1], b[0], b[1],
                    fill=MESH_COL, width=1, dash=(5, 4))

        # Sütun çizgileri
        for j in range(cols):
            for i in range(rows - 1):
                a = proj(self.ctrl[i][j])
                b = proj(self.ctrl[i + 1][j])
                self.canvas.create_line(
                    a[0], a[1], b[0], b[1],
                    fill=MESH_COL, width=1, dash=(5, 4))

    def _draw_control_points(self, cx, cy, ang, sc):
        r = 5
        for i, row in enumerate(self.ctrl):
            for j, pt in enumerate(row):
                px, py   = project(pt[0], pt[1], pt[2], ang, sc, cx, cy)
                selected = (self.sel_i == i and self.sel_j == j)
                color    = PT_SEL if selected else PT_NORMAL

                if selected:
                    self.canvas.create_oval(
                        px - r - 4, py - r - 4,
                        px + r + 4, py + r + 4,
                        outline='#ffff00', width=2, fill='')

                self.canvas.create_oval(
                    px - r, py - r, px + r, py + r,
                    fill=color, outline='white', width=1)

                self.canvas.create_text(
                    px + r + 4, py - r - 2,
                    text=f"P{i},{j}",
                    fill=color, font=('Courier', 7), anchor='w')

    def _draw_axes_indicator(self, cx, cy, ang):
        """Sol alt köşede küçük XYZ ekseni göstergesi."""
        h  = self.canvas.winfo_height()
        ox = 55
        oy = h - 55
        L  = 32
        for dx, dy, dz, col, lbl in [
            (L, 0, 0, '#ff5555', 'X'),
            (0, L, 0, '#55ff55', 'Y'),
            (0, 0, L, '#5555ff', 'Z'),
        ]:
            ex, ey = project(dx, dy, dz, ang, 1.0, ox, oy)
            self.canvas.create_line(ox, oy, ex, ey, fill=col, width=2,
                                    arrow=tk.LAST, arrowshape=(8, 10, 3))
            self.canvas.create_text(ex, ey - 7, text=lbl,
                                    fill=col, font=('Courier', 8, 'bold'))

    def _draw_legend(self):
        """Sağ üst köşede yüzey tipi etiketi."""
        labels = {
            'bezier':  ('BEZİER YÜZEYİ',  '#00ffff'),
            'bspline': ('B-SPLİNE YÜZEYİ', '#00ff88'),
            'nurbs':   ('NURBS YÜZEYİ',    '#ff8800'),
        }
        text, col = labels[self.stype]
        w = self.canvas.winfo_width()
        self.canvas.create_text(
            w - 12, 12,
            text=text, fill=col,
            font=('Courier', 10, 'bold'), anchor='ne')


# ──────────────────────────────────────────────────────────────────────────────
# Giriş noktası
# ──────────────────────────────────────────────────────────────────────────────

def main():
    root = tk.Tk()
    SurfaceEditor(root)
    root.mainloop()


if __name__ == '__main__':
    main()
