"""Gera os SVGs do README do perfil (assets/*.svg).

Uso:  pip install fonttools pillow
      python scripts/build_assets.py

Os textos ficam nos blocos de dados (HERO, ABOUT, NOW, PILLARS, PROJECTS, LINKS).
As fontes (Poppins e JetBrains Mono, licença OFL) vão embutidas em cada SVG,
recortadas só com os caracteres usados, para renderizar igual em qualquer sistema.
"""
import base64
import io
import re
from collections import defaultdict
from pathlib import Path
from xml.sax.saxutils import escape

from fontTools import subset
from PIL import ImageFont

ROOT = Path(__file__).resolve().parent
OUT = ROOT.parent / "assets"
FONTS = ROOT / "fonts"

# ── Paleta ─────────────────────────────────────────────────────────────────
SURF_TOP, SURF_BOT = "#0f1729", "#0a101d"
BORDER = "#1c2740"
CHIP_BORDER = "#26324c"
TEXT = "#f1f4f9"
BODY = "#aab6cb"
MUTED = "#6b7896"
LABEL = "#8a97b2"

BLUE = "#60a5fa"
AMBER = "#f5b14c"
VIOLET = "#c084fc"
CYAN = "#22d3ee"
GREEN = "#34d399"
ROSE = "#f472b6"
LIME = "#a3e635"

# ── Tipografia ─────────────────────────────────────────────────────────────
FACES = {  # chave: (família, peso, itálico, arquivo)
    "r": ("P", 400, False, "Poppins-Regular.ttf"),
    "m": ("P", 500, False, "Poppins-Medium.ttf"),
    "s": ("P", 600, False, "Poppins-SemiBold.ttf"),
    "i": ("P", 400, True, "Poppins-Italic.ttf"),
    "mono": ("M", 400, False, "JetBrainsMono-Regular.ttf"),
}
STACK = {"P": "P, 'Segoe UI', -apple-system, sans-serif", "M": "M, Consolas, Menlo, monospace"}
_pil = {}


def width(s, face, size, ls=0):
    key = (face, size)
    if key not in _pil:
        _pil[key] = ImageFont.truetype(str(FONTS / FACES[face][3]), size)
    return _pil[key].getlength(s) + ls * len(s)


def wrap(s, face, size, maxw):
    out, cur = [], ""
    for word in s.split():
        test = f"{cur} {word}".strip()
        if cur and width(test, face, size) > maxw:
            out.append(cur)
            cur = word
        else:
            cur = test
    return out + [cur] if cur else out


def font_b64(face, chars):
    opts = subset.Options()
    opts.flavor = "woff"
    opts.layout_features = ["kern", "liga"]
    opts.hinting = False
    opts.name_IDs = []
    font = subset.load_font(str(FONTS / FACES[face][3]), opts)
    sub = subset.Subsetter(opts)
    sub.populate(text="".join(sorted(chars)) + " ")
    sub.subset(font)
    buf = io.BytesIO()
    subset.save_font(font, buf, opts)
    return base64.b64encode(buf.getvalue()).decode()


class Doc:
    """Acumula os caracteres usados por fonte para embutir só o necessário."""

    def __init__(self):
        self.used = defaultdict(set)

    def t(self, x, y, s, size, fill, face="r", ls=0, anchor=None, extra=""):
        self.used[face].update(s)
        fam, wt, it, _ = FACES[face]
        attrs = f'font-family="{STACK[fam]}" font-size="{size}" font-weight="{wt}"'
        if it:
            attrs += ' font-style="italic"'
        if ls:
            attrs += f' letter-spacing="{ls}"'
        if anchor:
            attrs += f' text-anchor="{anchor}"'
        return f'<text x="{x:.1f}" y="{y:.1f}" {attrs} fill="{fill}" {extra}>{escape(s)}</text>'

    def svg(self, w, h, title, body, defs=""):
        faces = []
        for face, chars in self.used.items():
            fam, wt, it, _ = FACES[face]
            faces.append(f"@font-face{{font-family:{fam};font-weight:{wt};font-style:{'italic' if it else 'normal'};"
                         f"src:url(data:font/woff;base64,{font_b64(face, chars)}) format('woff');}}")
        return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{escape(title)}">
<title>{escape(title)}</title>
<style>{"".join(faces)}</style>
<defs>
  <linearGradient id="surf" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="{SURF_TOP}"/><stop offset="1" stop-color="{SURF_BOT}"/>
  </linearGradient>
  <linearGradient id="hl" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#fff" stop-opacity="0"/>
    <stop offset="0.5" stop-color="#fff" stop-opacity="0.09"/>
    <stop offset="1" stop-color="#fff" stop-opacity="0"/>
  </linearGradient>
  <linearGradient id="rule" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="{BORDER}"/><stop offset="1" stop-color="{BORDER}" stop-opacity="0"/>
  </linearGradient>
  {defs}
</defs>
{body}
</svg>
"""


def panel(w, h, r=16, x=0, y=0, tint=None, horizontal=False, strength=0.10):
    """Superfície plana, borda fina e um brilho sutil na aresta superior.
    Com `tint`, ganha um véu suave da cor (de cima para baixo, ou da esquerda) e a borda levemente tingida."""
    stroke = f'stroke="{tint}" stroke-opacity="0.26"' if tint else f'stroke="{BORDER}"'
    out = f'<rect x="{x + .5}" y="{y + .5}" width="{w - 1}" height="{h - 1}" rx="{r}" fill="url(#surf)" {stroke}/>'
    if tint:
        gid = f"t{tint[1:]}{'h' if horizontal else 'v'}"
        x2, y2 = ("1", "0") if horizontal else ("0", "1")
        out += (f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="{x2}" y2="{y2}">'
                f'<stop offset="0" stop-color="{tint}" stop-opacity="{strength}"/>'
                f'<stop offset="1" stop-color="{tint}" stop-opacity="0"/></linearGradient></defs>'
                f'<rect x="{x + 1}" y="{y + 1}" width="{w - 2}" height="{h - 2}" rx="{r - .5}" fill="url(#{gid})"/>')
    return out + f'<rect x="{x + r}" y="{y + .5}" width="{w - 2 * r}" height="1" fill="url(#hl)"/>'


def tile(x, y, size, color, inner, r=10):
    """Quadrado com tinta da cor de destaque e ícone em traço."""
    k = (size - 28) / 2
    return (f'<rect x="{x + .5}" y="{y + .5}" width="{size - 1}" height="{size - 1}" rx="{r}" fill="{color}" fill-opacity="0.10" stroke="{color}" stroke-opacity="0.32"/>'
            f'<g transform="translate({x + k} {y + k})" fill="none" stroke="{color}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">{inner}</g>')


# logos das instituições (PNG dos sites oficiais): arquivo e margem interna
INST_LOGOS = {
    "Instituto Infnet": ("infnet-selo.png", 0),
    "UniSociesc": ("unisociesc.png", 0.2),
}


def seal(x, y, size, inst="Instituto Infnet"):
    """Logo da instituição num círculo, com um aro sutil."""
    file, pad = INST_LOGOS[inst]
    b64 = base64.b64encode((ROOT / file).read_bytes()).decode()
    r = size / 2
    out = f'<circle cx="{x + r}" cy="{y + r}" r="{r + 2.5}" fill="none" stroke="{CHIP_BORDER}"/>'
    if pad:
        out += f'<circle cx="{x + r}" cy="{y + r}" r="{r}" fill="#fff"/>'
    inner = size * (1 - 2 * pad)
    return out + f'<image x="{x + size * pad:.1f}" y="{y + size * pad:.1f}" width="{inner:.1f}" height="{inner:.1f}" href="data:image/png;base64,{b64}"/>'


# bandeiras em vetor (18 × 12, cantos arredondados)
def flag(x, baseline, code):
    y = baseline - 10.5
    cid = f"fl{code}"
    if code == "br":
        art = ('<rect width="18" height="12" fill="#009c3b"/><path d="M9 1.6 16.2 6 9 10.4 1.8 6Z" fill="#ffdf00"/>'
               '<circle cx="9" cy="6" r="2.7" fill="#002776"/>')
    elif code == "gb":
        art = ('<rect width="18" height="12" fill="#012169"/>'
               '<path d="M0 0 18 12M18 0 0 12" stroke="#fff" stroke-width="2.6"/>'
               '<path d="M0 0 18 12M18 0 0 12" stroke="#c8102e" stroke-width="0.9"/>'
               '<path d="M9 0v12M0 6h18" stroke="#fff" stroke-width="3.6"/>'
               '<path d="M9 0v12M0 6h18" stroke="#c8102e" stroke-width="2"/>')
    else:  # jp
        art = '<rect width="18" height="12" fill="#fff"/><circle cx="9" cy="6" r="3.6" fill="#bc002d"/>'
    return (f'<g transform="translate({x} {y:.1f})"><clipPath id="{cid}"><rect width="18" height="12" rx="2.5"/></clipPath>'
            f'<g clip-path="url(#{cid})">{art}</g><rect x=".25" y=".25" width="17.5" height="11.5" rx="2.4" fill="none" stroke="#fff" stroke-opacity="0.18" stroke-width=".5"/></g>')


def cal(x, baseline, color, size=11):
    """Ícone de calendário alinhado à linha de base do texto ao lado."""
    k = size / 12
    return (f'<g transform="translate({x:.1f} {baseline - size + .5:.1f}) scale({k:.3f})" fill="none" stroke="{color}" '
            f'stroke-width="{1.15 / k:.2f}" stroke-linecap="round" stroke-linejoin="round">'
            '<rect x="1" y="2" width="10" height="9" rx="1.8"/><path d="M1 5h10M4 .8v2.4M8 .8v2.4"/></g>')


def arrow(x, y, color=MUTED):
    return (f'<g transform="translate({x} {y})" fill="none" stroke="{color}" stroke-width="1.5" stroke-linecap="round">'
            '<path d="M3 11 11 3M5 3h6v6"/></g>')


def write(name, content):
    (OUT / name).write_text(content, encoding="utf-8")
    print(f"  ok {name:<34} {len(content.encode()) // 1024:>4} KB")


# Peças com fundo transparente (títulos, legendas, rodapé) ganham uma versão
# para o tema claro do GitHub; o README escolhe com <picture> + prefers-color-scheme.
LIGHT = {TEXT: "#1f2328", BODY: "#424a53", LABEL: "#424a53", MUTED: "#6e7781",
         BORDER: "#d0d7de", CHIP_BORDER: "#d0d7de", BLUE: "#0969da"}


def write_themed(name, content, light_extra=None):
    write(name, content.replace("<!--light-only-->", ""))
    light = content
    for dark_c, light_c in LIGHT.items():
        light = light.replace(f'"{dark_c}"', f'"{light_c}"')
    if light_extra:
        light = light.replace("<!--light-only-->", light_extra)
    write(name.replace(".svg", "-light.svg"), light)


ICONS = {
    "nodes": '<circle cx="5" cy="22" r="3.2"/><circle cx="23" cy="22" r="3.2"/><circle cx="14" cy="6" r="3.2"/>'
             '<path d="M8.2 22h11.6M12.4 8.8 6.6 19.2M15.6 8.8l5.8 10.4"/>',
    "bolt": '<path d="M16 2 5 16h8l-2 10 11-14h-8l2-10Z"/>',
    "hex": '<path d="M14 2.5 24 8.3v11.4L14 25.5 4 19.7V8.3Z"/><path d="M14 9.5 18.5 12v5L14 19.5 9.5 17v-5Z" opacity="0.55"/>',
    "cloud": '<path d="M8 22h13a5 5 0 0 0 .6-9.96A7.5 7.5 0 0 0 7.1 13.6 4.2 4.2 0 0 0 8 22Z"/>'
             '<path d="M9 17.5h3l1.5-3 2 5 1.5-2h2"/>',
    "folder": '<path d="M3 7a2 2 0 0 1 2-2h4.2l2 2.2H19a2 2 0 0 1 2 2V17a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2Z"/>'
              '<path d="M3 10h18" fill="none" stroke-opacity="0.6"/>',
    "linkedin": '<rect x="5" y="5" width="18" height="18" rx="4"/><path d="M10 13v6M10 9.8v.2M14 19v-6M14 15.5c0-1.5 1-2.5 2.3-2.5s2.2 1 2.2 2.5V19"/>',
    "lock": '<rect x="7" y="12.5" width="14" height="10" rx="2.5"/><path d="M10 12.5V10a4 4 0 0 1 8 0v2.5M14 16.2v2.6"/>',
    "cap": '<path d="M2 11 14 5l12 6-12 6Z"/><path d="M7 13.5V19c0 1.7 3.1 3 7 3s7-1.3 7-3v-5.5M26 11v6"/>',
    "award": '<circle cx="14" cy="10.5" r="6.5"/><path d="m10.2 15.8-2.2 8.7 6-3 6 3-2.2-8.7"/>',
    "globe": '<circle cx="14" cy="14" r="10"/><path d="M4 14h20M14 4c2.8 3 4 6.4 4 10s-1.2 7-4 10c-2.8-3-4-6.4-4-10s1.2-7 4-10Z"/>',
    "bot": '<rect x="4" y="9" width="20" height="14" rx="4"/><path d="M14 4.6V9M10.5 15v1.2M17.5 15v1.2M11 19.5h6"/><circle cx="14" cy="3.6" r="1.2"/>',
    "neural": '<circle cx="5" cy="7" r="2.3"/><circle cx="5" cy="21" r="2.3"/><circle cx="14" cy="14" r="2.3"/><circle cx="23" cy="7" r="2.3"/><circle cx="23" cy="21" r="2.3"/>'
              '<path d="m7 8.5 5 4M7 19.5l5-4M16 12.5l5-4M16 15.5l5 4"/>',
    "building": '<path d="M4 24V10l7-4v18M11 24V5l13 5v14M2 24h24M15 13h5M15 17h5M15 21h5M7 13v1M7 17v1M7 21v1"/>',
    "inspect": '<circle cx="12" cy="12" r="7.5"/><path d="m17.5 17.5 6 6M8.8 12l2.2 2.2 4.2-4.4"/>',
    "code": '<path d="m10 8-6 6 6 6M18 8l6 6-6 6M16 5l-4 18"/>',
    "links": '<path d="M12.5 15.5a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1M15.5 12.5a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1"/>',
}


ICONS16 = {
    "cart": '<path d="M1.5 2h2l1.6 8h7.4l1.5-5.5H4.3"/><circle cx="6" cy="13" r="1.1"/><circle cx="11.5" cy="13" r="1.1"/>',
    "card": '<rect x="1.5" y="3.5" width="13" height="9" rx="1.8"/><path d="M1.5 6.5h13M4 10h3"/>',
    "box": '<path d="M8 1.5 14 4.5v7L8 14.5 2 11.5v-7Z"/><path d="M2 4.5 8 7.5l6-3M8 7.5v7"/>',
    "bot": '<rect x="2.5" y="5" width="11" height="8.5" rx="2.2"/><path d="M8 2.2V5M6 9.6v.2M10 9.6v.2"/><circle cx="8" cy="1.8" r=".7"/>',
    "neural": '<circle cx="3" cy="4" r="1.3"/><circle cx="3" cy="12" r="1.3"/><circle cx="8" cy="8" r="1.3"/><circle cx="13" cy="4" r="1.3"/><circle cx="13" cy="12" r="1.3"/>'
              '<path d="M4.1 4.8 6.9 7.2M4.1 11.2l2.8-2.4M9.1 7.2l2.8-2.4M9.1 8.8l2.8 2.4"/>',
    "bell": '<path d="M4 11V7.5a4 4 0 0 1 8 0V11l1.2 1.5H2.8Z"/><path d="M6.5 14a1.6 1.6 0 0 0 3 0"/>',
}


def bkr_glyph():
    """Símbolo bkr (sem o fundo quadrado), pronto para um <svg viewBox="0 0 96 96">."""
    src = (ROOT / "bkr-logo.svg").read_text(encoding="utf-8")
    inner = re.search(r"<svg[^>]*>(.*)</svg>", src, re.S).group(1)
    inner = re.sub(r'<g clip-path="url\(#paint0_diamond.*?</g></g>', "", inner, flags=re.S)  # fundo quadrado
    inner = re.sub(r'<rect width="96" height="96" data-figma[^>]*/>', "", inner)              # (só o símbolo)
    inner = re.sub(r'\sdata-figma-[a-z-]+="[^"]*"', "", inner)      # metadados do Figma
    return re.sub(r'(id="|url\(#)', r"\g<1>bkr-", inner)           # ids únicos


# ── Hero ───────────────────────────────────────────────────────────────────
HERO = {
    "kicker": "SOFTWARE ENGINEER",
    "name": "André Luis Becker",
    "en": "Backend, architecture & AI agents for systems that scale.",
    "pt": "Backend, arquitetura e agentes de IA para sistemas que escalam.",
    "chips": ["Java 25", "Spring Boot 4", "Kafka", "Kubernetes", "AI Agents"],
    # serviços do diagrama: (rótulo, ícone, cor)
    "top": [("orders", "cart", BLUE), ("payments", "card", BLUE), ("catalog", "box", BLUE)],
    "bottom": [("ai-agent", "bot", ROSE), ("ml-model", "neural", LIME), ("notify", "bell", CYAN)],
}


def build_hero():
    W, H = 1280, 400
    d = Doc()
    hero = HERO
    inner = bkr_glyph()
    defs = f"""
  <radialGradient id="g1" cx="0.12" cy="0" r="0.75"><stop offset="0" stop-color="{BLUE}" stop-opacity="0.10"/><stop offset="1" stop-color="{BLUE}" stop-opacity="0"/></radialGradient>
  <radialGradient id="g2" cx="0.92" cy="1" r="0.55"><stop offset="0" stop-color="{AMBER}" stop-opacity="0.05"/><stop offset="1" stop-color="{AMBER}" stop-opacity="0"/></radialGradient>
  <pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r="1" fill="#fff" fill-opacity="0.07"/></pattern>
  <linearGradient id="fadeL" x1="0" y1="0" x2="1" y2="0"><stop offset="0.35" stop-color="#fff" stop-opacity="0"/><stop offset="0.75" stop-color="#fff" stop-opacity="1"/></linearGradient>
  <mask id="dm"><rect width="{W}" height="{H}" fill="url(#fadeL)"/></mask>
  <linearGradient id="bus" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{AMBER}" stop-opacity="0"/><stop offset="0.12" stop-color="{AMBER}" stop-opacity="0.45"/><stop offset="0.88" stop-color="{AMBER}" stop-opacity="0.45"/><stop offset="1" stop-color="{AMBER}" stop-opacity="0"/></linearGradient>
  <filter id="soft" x="-200%" y="-200%" width="500%" height="500%"><feGaussianBlur stdDeviation="2.5"/></filter>
  <clipPath id="frame"><rect width="{W}" height="{H}" rx="20"/></clipPath>"""

    # Lado esquerdo: identidade
    x0 = 72
    name_w = width(hero["name"], "s", 58)
    left = [
        f'<rect x="{x0}" y="109" width="22" height="2" rx="1" fill="{AMBER}"/>',
        d.t(x0 + 34, 115, hero["kicker"], 13, LABEL, "m", ls=4),
        d.t(x0 - 2, 180, hero["name"], 58, TEXT, "s"),
        d.t(x0, 224, hero["en"], 20, BODY, "r"),
        d.t(x0, 254, hero["pt"], 15.5, MUTED, "i"),
    ]
    cx = x0
    for c in hero["chips"]:
        cw = width(c, "m", 12.5) + 28
        left.append(f'<rect x="{cx + .5}" y="290.5" width="{cw - 1:.1f}" height="31" rx="15.5" fill="#fff" fill-opacity="0.035" stroke="{CHIP_BORDER}"/>')
        left.append(d.t(cx + cw / 2, 310.5, c, 12.5, BODY, "m", anchor="middle"))
        cx += cw + 10
    assert name_w < 660, name_w
    assert cx < 720, f"chips invadem o diagrama: {cx}"

    # Lado direito: diagrama orientado a eventos (animado)
    BX1, BX2, BY = 744, 1222, 208
    box_h = 46

    # Colunas alinhadas: cada produtor (em cima) fica sobre um consumidor (embaixo),
    # com um único ponto de junção por coluna no barramento.
    bw = max(width(l, "mono", 12.5) for l, _, _ in hero["top"] + hero["bottom"]) + 60
    gap = 26
    ncol = len(hero["top"])
    x_start = (BX1 + BX2) / 2 - (ncol * bw + (ncol - 1) * gap) / 2

    def boxes(items, y):
        return [(x_start + k * (bw + gap), y, bw, l, ic, col) for k, (l, ic, col) in enumerate(items)]

    top = boxes(hero["top"], 110)
    bottom = boxes(hero["bottom"], 260)
    assert len(top) == len(bottom)
    assert top[0][0] > BX1 and bottom[0][0] > BX1, "diagrama largo demais"
    g = [f'<rect x="{BX1}" y="{BY - 1}" width="{BX2 - BX1}" height="2" fill="url(#bus)"/>',
         d.t(BX1 + 8, BY + 24, "kafka", 11, MUTED, "mono")]
    assert BX1 + 8 + width("kafka", "mono", 11) < x_start + bw / 2 - 12, "rótulo do barramento encosta no conector"
    junctions = []
    for i, (x, y, bw, l, ic, color) in enumerate(top + bottom):
        cxm = x + bw / 2
        is_top = y < BY
        y1, y2 = (y + box_h, BY) if is_top else (BY, y)
        g.append(f'<line x1="{cxm:.1f}" y1="{y1}" x2="{cxm:.1f}" y2="{y2}" stroke="{CHIP_BORDER}" stroke-width="1.5"/>')
        if is_top:
            junctions.append(cxm)
        g.append(f'<rect x="{x + .5:.1f}" y="{y + .5}" width="{bw - 1:.1f}" height="{box_h - 1}" rx="10" fill="#111a2e" stroke="{CHIP_BORDER}"/>')
        # quadradinho com o ícone do serviço, na cor do papel dele
        tx, ty, ts = x + 9, y + (box_h - 28) / 2, 28
        g.append(f'<rect x="{tx + .5:.1f}" y="{ty + .5}" width="{ts - 1}" height="{ts - 1}" rx="7" fill="{color}" fill-opacity="0.12" stroke="{color}" stroke-opacity="0.38"/>')
        g.append(f'<g transform="translate({tx + 6:.1f} {ty + 6})" fill="none" stroke="{color}" stroke-width="1.35" stroke-linecap="round" stroke-linejoin="round">{ICONS16[ic]}</g>')
        g.append(d.t(x + 46, y + box_h / 2 + 4.3, l, 12.5, BODY, "mono"))
        # pacote viajando entre serviço e barramento
        begin = f"{i * 0.9:.1f}s"
        path = f"M{cxm:.1f} {y1} V{y2}"
        g.append(f"""<g opacity="0"><circle r="5" fill="{color}" filter="url(#soft)" opacity="0.8"/><circle r="2.6" fill="{color}"/>
  <animateMotion path="{path}" dur="1.4s" begin="{begin}; m{i}.end+3.1s" id="m{i}" fill="freeze"/>
  <animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.15;0.8;1" dur="1.4s" begin="{begin}; m{i}.end+3.1s"/></g>""")
    for jx in junctions:
        g.append(f'<circle cx="{jx:.1f}" cy="{BY}" r="4" fill="{SURF_BOT}" stroke="{AMBER}" stroke-opacity="0.75" stroke-width="1.4"/>')
    # eventos percorrendo o barramento
    for k in range(3):
        g.append(f"""<g><circle r="6" fill="{AMBER}" filter="url(#soft)" opacity="0.7"/><circle r="2.8" fill="{AMBER}"/>
  <animateMotion path="M{BX1} {BY} H{BX2}" dur="4.5s" begin="{k * 1.5}s" repeatCount="indefinite"/>
  <animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.1;0.9;1" dur="4.5s" begin="{k * 1.5}s" repeatCount="indefinite"/></g>""")

    body = f"""<g clip-path="url(#frame)">
<rect width="{W}" height="{H}" fill="url(#surf)"/>
<rect width="{W}" height="{H}" fill="url(#dots)" mask="url(#dm)"/>
<rect width="{W}" height="{H}" fill="url(#g1)"/>
<rect width="{W}" height="{H}" fill="url(#g2)"/>
</g>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="20" fill="none" stroke="{BORDER}"/>
<rect x="20" y=".5" width="{W - 40}" height="1" fill="url(#hl)"/>
{"".join(left)}
{"".join(g)}
<svg x="{W - 64 - 84}" y="18" width="84" height="84" viewBox="0 0 96 96" overflow="visible">{inner}</svg>"""
    write("hero.svg", d.svg(W, H, f'{hero["name"]} · {hero["kicker"].title()} · {hero["en"]}', body, defs))


# ── Títulos de seção ───────────────────────────────────────────────────────
SECTIONS = [("about", "ABOUT", "SOBRE"), ("journey", "JOURNEY", "TRAJETÓRIA"), ("focus", "FOCUS", "FOCO"),
            ("work", "FEATURED WORK", "PROJETOS EM DESTAQUE"), ("education", "EDUCATION", "FORMAÇÃO"),
            ("toolbox", "TOOLBOX", "FERRAMENTAS"), ("connect", "CONNECT", "CONTATO")]


def build_sections():
    for n, (key, en, pt) in enumerate(SECTIONS, 1):
        d = Doc()
        w, h, ls = 960, 40, 3.2
        x_en = 34
        x_pt = x_en + width(en, "s", 12.5, ls) + 14
        end = x_pt + width(pt, "m", 12.5, ls) + 18
        body = (d.t(0, 25, f"{n:02d}", 12, BLUE, "mono")
                + f'<rect x="21" y="16" width="1" height="12" fill="{CHIP_BORDER}"/>'
                + d.t(x_en, 25, en, 12.5, TEXT, "s", ls=ls)
                + d.t(x_pt, 25, pt, 12.5, MUTED, "m", ls=ls)
                + f'<rect x="{end:.1f}" y="20" width="{w - end:.1f}" height="1" fill="url(#rule)"/>')
        write_themed(f"section-{key}.svg", d.svg(w, h, f"{en} · {pt}", body))


# ── About: saudação como um log de eventos ─────────────────────────────────
ABOUT = {
    "en": ("I design and build backend systems that scale: distributed, event-driven services in Java "
           "and Spring, shipped to Kubernetes with observability built in from day one. "
           "Lately exploring AI agents and machine learning."),
    "pt": ("Projeto e construo sistemas backend que escalam: serviços distribuídos e orientados a eventos "
           "em Java e Spring, entregues no Kubernetes com observabilidade desde o primeiro dia. "
           "Recentemente explorando agentes de IA e machine learning."),
    # selo: país + modalidades (preferência em destaque, presencial discreto)
    "place": [("Brazil", "m", "text"), ("Remote", "s", "pref"), ("Hybrid", "s", "pref"), ("On-site", "r", "alt")],
    "events": [  # (cor, evento, payload)
        (BLUE, "VisitorArrived", '{ from: "github" }'),
        (AMBER, "GreetingEmitted", '{ en: "Hello", pt: "Olá" }'),
        (GREEN, "IntroductionReady", '{ next: "scroll ↓" }'),
    ],
}


def build_about():
    d = Doc()
    a = ABOUT
    w = 960
    RX, RW = 486, 440
    en = wrap(a["en"], "r", 14.5, RW)
    pt = wrap(a["pt"], "i", 13, RW)
    y_en = 58
    y_pt = y_en + len(en) * 23 + 12
    y_place = y_pt + len(pt) * 20 + 28
    h = max(262, int(y_place + 34))

    # Log de eventos: as linhas entram em sequência e o ciclo recomeça
    CYCLE = 11
    log = [d.t(32, 54, "$", 12.5, GREEN, "mono"),
           d.t(48, 54, "tail -f profile.events", 12.5, MUTED, "mono")]
    for i, (color, ev, payload) in enumerate(a["events"]):
        y = 96 + i * 42
        t0 = (0.8 + i * 1.1) / CYCLE
        t1 = t0 + 0.035
        kt = f"0;{t0:.3f};{t1:.3f};0.93;1"
        anim = (f'<animate attributeName="opacity" values="0;0;1;1;0" keyTimes="{kt}" dur="{CYCLE}s" repeatCount="indefinite"/>'
                f'<animateTransform attributeName="transform" type="translate" values="8 0;8 0;0 0;0 0;0 0" keyTimes="{kt}" dur="{CYCLE}s" repeatCount="indefinite"/>')
        log.append(f'<g opacity="0">{anim}'
                   f'<circle cx="37" cy="{y - 4}" r="3.2" fill="{color}"/>'
                   + d.t(50, y, ev, 12.5, TEXT, "mono")
                   + d.t(50, y + 17, payload, 11.5, MUTED, "mono")
                   + '</g>')
    cy = 96 + len(a["events"]) * 42 + 4
    log.append(f'<rect x="32" y="{cy - 12}" width="8" height="15" rx="1" fill="{GREEN}">'
               '<animate attributeName="opacity" values="1;0" dur="1.05s" calcMode="discrete" repeatCount="indefinite"/></rect>')

    right = [d.t(RX, y_en + i * 23, ln, 14.5, BODY, "r") for i, ln in enumerate(en)]
    right += [d.t(RX, y_pt + i * 20, ln, 13, MUTED, "i") for i, ln in enumerate(pt)]
    # selo de localização e modalidades, em pílula com tom azul
    top = y_place - 20
    colors = {"text": TEXT, "pref": BLUE, "alt": MUTED}
    x = RX + 34
    pill_parts = []
    for i, (label, face, kind) in enumerate(a["place"]):
        if i:
            pill_parts.append(d.t(x + 7, top + 19.5, "·", 12.5, MUTED, "r"))
            x += width("·", "r", 12.5) + 14
        pill_parts.append(d.t(x, top + 19.5, label, 12.5, colors[kind], face))
        x += width(label, face, 12.5)
    pill_w = x + 16 - RX
    assert RX + pill_w < w - 24, "selo de localização estoura o painel"
    right.append(f'<rect x="{RX + .5}" y="{top + .5}" width="{pill_w - 1:.1f}" height="29" rx="14.5" '
                 f'fill="{BLUE}" fill-opacity="0.10" stroke="{BLUE}" stroke-opacity="0.38"/>')
    right.append(f'<g transform="translate({RX + 13} {top + 7.5})" fill="none" stroke="{BLUE}" stroke-width="1.5">'
                 '<path d="M6 1.5a4.5 4.5 0 0 1 4.5 4.5c0 3.4-4.5 8-4.5 8S1.5 9.4 1.5 6A4.5 4.5 0 0 1 6 1.5Z"/><circle cx="6" cy="6" r="1.6"/></g>')
    right += pill_parts

    body = f"""{panel(w, h)}
<rect x="452" y="32" width="1" height="{h - 64}" fill="{BORDER}"/>
{"".join(log)}
{"".join(right)}"""
    write("about.svg", d.svg(w, h, a["en"], body))


# ── Now ────────────────────────────────────────────────────────────────────
NOW = {
    "en": "Event-driven microservices",
    "pt": "Microsserviços orientados a eventos",
    "stack": "Java 25 · Spring Boot 4 · Kafka · Kubernetes",
}


def build_now():
    d = Doc()
    w, h = 960, 78
    label = "NOW · AGORA"
    lx = 58
    div = lx + width(label, "s", 11, 3) + 18
    body = f"""{panel(w, h, 14, tint=GREEN, horizontal=True, strength=0.13)}
<circle cx="34" cy="39" r="4" fill="none" stroke="{GREEN}" stroke-width="1.5">
  <animate attributeName="r" values="4;15" dur="2s" repeatCount="indefinite"/>
  <animate attributeName="stroke-opacity" values="0.7;0" dur="2s" repeatCount="indefinite"/>
</circle>
<circle cx="34" cy="39" r="9" fill="{GREEN}" fill-opacity="0.18"/>
<circle cx="34" cy="39" r="4.5" fill="{GREEN}">
  <animate attributeName="fill-opacity" values="1;0.55;1" dur="2s" repeatCount="indefinite"/>
</circle>
{d.t(lx, 43, label, 11, GREEN, "s", ls=3)}
<rect x="{div:.1f}" y="22" width="1" height="34" fill="{BORDER}"/>
{d.t(div + 22, 36, NOW["en"], 15, TEXT, "m")}
{d.t(div + 22 + width(NOW["en"], "m", 15) + 14, 36, NOW["pt"], 12.5, MUTED, "i")}
{d.t(div + 22, 57, NOW["stack"], 11.5, BODY, "mono")}"""
    write("now.svg", d.svg(w, h, f'{NOW["en"]} · {NOW["stack"]}', body))


# ── Pilares ────────────────────────────────────────────────────────────────
PILLARS = [
    ("nodes", BLUE, "Distributed Systems", "Sistemas distribuídos", ["Microservices · API Gateway", "Service discovery · Resilience"]),
    ("bolt", AMBER, "Event-Driven", "Orientação a eventos", ["Kafka · RabbitMQ", "Outbox · Saga · Idempotency"]),
    ("hex", VIOLET, "Domain-Driven Design", "Design orientado a domínio", ["Bounded contexts · Aggregates", "Hexagonal architecture"]),
    ("cloud", CYAN, "Cloud-Native", "Nativo em nuvem", ["Kubernetes · Docker · CI/CD", "OpenTelemetry · Prometheus"]),
    ("bot", ROSE, "AI Agents", "Agentes de IA", ["LLM agents · Generative AI", "Automation · n8n · Ollama"]),
    ("neural", LIME, "Machine Learning", "Aprendizado de máquina", ["scikit-learn · XGBoost · SHAP", "NLP · Feature engineering"]),
]


def build_pillars():
    """Grade 3 × 2: ícone e título lado a lado, palavras-chave embaixo."""
    d = Doc()
    w, gap, ch, cols = 960, 16, 156, 3
    cw = (w - gap * (cols - 1)) / cols
    rows = (len(PILLARS) + cols - 1) // cols
    h = rows * ch + (rows - 1) * gap
    parts = []
    for i, (icon, color, en, pt, kws) in enumerate(PILLARS):
        x, y = (i % cols) * (cw + gap), (i // cols) * (ch + gap)
        kw = "".join(d.t(20, 112 + j * 18, k, 11, BODY, "mono") for j, k in enumerate(kws))
        parts.append(f"""<g transform="translate({x:.1f} {y})">
  {panel(cw, ch, 14, tint=color, strength=0.09)}
  {tile(20, 20, 42, color, ICONS[icon])}
  {d.t(76, 39, en, 15.5, TEXT, "s")}
  {d.t(76, 58, pt, 12.5, MUTED, "i")}
  <rect x="20" y="84" width="22" height="2" rx="1" fill="{color}"/>
  {kw}
</g>""")
    write("focus.svg", d.svg(w, h, " · ".join(p[2] for p in PILLARS), "\n".join(parts)))


# ── Projetos ───────────────────────────────────────────────────────────────
PROJECTS = [
    dict(slug="cinepass", color=AMBER, tag="EVENT-DRIVEN · OBSERVABILITY", title="CinePass",
         en="Kafka in KRaft mode with transactional outbox, idempotent consumers, per-booking ordering and DLT replay. Logs in ELK, traces in Zipkin.",
         pt="Kafka com outbox transacional, consumidores idempotentes, DLT com reprocessamento, ELK e Zipkin.",
         chips=["Java 25", "Spring Boot 4", "Kafka"]),
    dict(slug="infnet-hub-prod", color=CYAN, tag="PLATFORM · KUBERNETES", title="Infnet Hub · Production",
         en="Spring Boot microservices running on Kubernetes with full observability (Prometheus, Grafana, Loki, Tempo) and CI/CD.",
         pt="Microsserviços em Kubernetes com observabilidade completa e CI/CD com GitHub Actions.",
         chips=["Kubernetes", "OpenTelemetry", "GitHub Actions"]),
    dict(slug="infnet-hub-events", color=AMBER, tag="EVENT-DRIVEN · SAGA", title="Infnet Hub · Events",
         en="Refactored to event-driven with RabbitMQ: outbox, quorum queues, DLQ, saga and request/reply, secured by a Keycloak BFF.",
         pt="Refatoração para eventos com RabbitMQ: outbox, filas quorum, DLQ, saga e BFF com Keycloak.",
         chips=["RabbitMQ", "Keycloak", "Next.js"]),
    dict(slug="async-messaging", color=AMBER, tag="ASYNC MESSAGING · DDD", title="E-commerce · Async Messaging",
         en="Commands over RabbitMQ, events over Kafka, mirrored to SNS/SQS FIFO. Transactional outbox and inbox with an orchestrated saga.",
         pt="Comandos via RabbitMQ, eventos via Kafka e SNS/SQS FIFO, com outbox, inbox e saga orquestrada.",
         chips=["Kafka", "RabbitMQ", "AWS SQS"]),
    dict(slug="jwt-auth", color=BLUE, tag="SECURITY · REACTIVE", title="Sales API · JWT Auth",
         en="Auth service with login and rotating refresh tokens, protected routes at the gateway and services. Reactive stack with WebFlux and R2DBC.",
         pt="Autenticação JWT com refresh token rotativo e rotas protegidas no gateway, em stack reativa.",
         chips=["Spring Cloud", "WebFlux", "PostgreSQL"]),
    dict(slug="monolith-to-ms", color=VIOLET, tag="REFACTORING · HEXAGONAL", title="From Monolith to Microservices",
         en="Extracting the Payments bounded context from a live e-commerce monolith using DDD and Branch by Abstraction.",
         pt="Extração do contexto de Pagamento de um monólito com DDD e Branch by Abstraction, sem downtime.",
         chips=["DDD", "Ports & Adapters", "Strangler Fig"]),
    dict(slug="ml-portfolio", color=LIME, tag="MACHINE LEARNING · NLP", title="Machine Learning Portfolio",
         en="Notebooks covering classification, clustering, feature engineering and NLP, with model interpretability through SHAP.",
         pt="Notebooks de classificação, clustering, engenharia de features e NLP, com interpretabilidade via SHAP.",
         chips=["scikit-learn", "XGBoost", "SHAP"]),
]


def build_projects():
    w, h = 480, 254
    for p in PROJECTS:
        d = Doc()
        en = wrap(p["en"], "r", 13, w - 56)
        pt = wrap(p["pt"], "i", 11.5, w - 56)
        y = 104
        body = [panel(w, h),
                f'<circle cx="31" cy="36" r="3.5" fill="{p["color"]}"/>',
                d.t(44, 40, p["tag"], 10.5, LABEL, "s", ls=2),
                arrow(w - 44, 27),
                f'<g transform="translate(23 53) scale(1.1)" fill="{p["color"]}" fill-opacity="0.14" stroke="{p["color"]}" '
                f'stroke-width="1.45" stroke-linejoin="round">{ICONS["folder"]}</g>',
                d.t(57, 76, p["title"], 21, TEXT, "s")]
        for ln in en:
            body.append(d.t(26, y, ln, 13, BODY, "r"))
            y += 19.5
        y += 5
        for ln in pt:
            body.append(d.t(26, y, ln, 11.5, MUTED, "i"))
            y += 17
        assert y - 17 < h - 56, (p["slug"], y - 17)  # última linha acima dos chips
        cx = 26
        for c in p["chips"]:
            cw = width(c, "m", 11) + 24
            body.append(f'<rect x="{cx + .5}" y="{h - 46.5}" width="{cw - 1:.1f}" height="25" rx="12.5" fill="#fff" fill-opacity="0.035" stroke="{CHIP_BORDER}"/>')
            body.append(d.t(cx + cw / 2, h - 30, c, 11, BODY, "m", anchor="middle"))
            cx += cw + 8
        write(f"project-{p['slug']}.svg", d.svg(w, h, f'{p["title"]}: {p["en"]}', "\n".join(body)))


# ── Contato ────────────────────────────────────────────────────────────────
LINKS = [
    ("linkedin", BLUE, "LinkedIn", "in/becker84"),
    ("lock", AMBER, "Contact · Contato", "password · com senha"),
    ("links", CYAN, "Links", "andrebecker84.github.io"),
]


def build_links():
    w, h = 300, 68
    for icon, color, label, sub in LINKS:
        d = Doc()
        body = (panel(w, h, 14) + tile(16, 16, 36, color, ICONS[icon], r=9)
                + d.t(66, 31, label, 14.5, TEXT, "s")
                + d.t(66, 49, sub, 11, MUTED, "mono")
                + arrow(w - 36, 27))
        write(f"link-{icon}.svg", d.svg(w, h, f"{label}: {sub}", body))


# ── Toolbox: linha de mensageria (ícones skill-icons, MIT) ─────────────────
# O Kafka do skill-icons só existe em tile claro; aqui ele ganha o tile escuro padrão.
STACK_ROWS = {"messaging": ["kafka", "rabbitmq", "postgres", "mongodb", "redis", "elasticsearch"]}


def icon_inner(name):
    s = (ROOT / "icons" / f"{name}.svg").read_text(encoding="utf-8")
    inner = re.search(r'translate\(0, 0\)">\s*<svg[^>]*>(.*)</svg>\s*</g>', s, re.S).group(1)
    if name == "kafka":
        inner = inner.replace('fill="#A9CBD4"', 'fill="#242938"').replace('fill="black"', 'fill="#fff"')
    return re.sub(r'(id="|url\(#)', rf"\g<1>{name}-", inner)  # ids únicos por ícone


# ── Trajetória ─────────────────────────────────────────────────────────────
JOURNEY = {
    "en": "From designing buildings to designing systems.",
    "pt": "De projetar edifícios a projetar sistemas.",
    "steps": [  # (cor, ícone, período, papel EN, papel PT, onde)
        (VIOLET, "building", "2007 — 2017", "Architecture & Urbanism", "Arquitetura e Urbanismo", "Brazil · 10 years of practice"),
        (ROSE, "inspect", "2017 — 2022", "Quality Control", "Controle de Qualidade", "Japan · Toyota Boshoku, Lexus, Suzuki"),
        (GREEN, "code", "2023 — now", "Software Engineering", "Engenharia de Software", "Brazil · Instituto Infnet"),
    ],
}


def build_journey():
    d = Doc()
    w, h = 960, 270
    LY, T = 130, 42                      # linha do tempo e tamanho do ícone
    col = (w - 64) / 3
    parts = [panel(w, h),
             d.t(32, 52, JOURNEY["en"], 18, TEXT, "s"),
             d.t(32, 76, JOURNEY["pt"], 13, MUTED, "i"),
             f'<defs><linearGradient id="tl" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{VIOLET}" stop-opacity="0.5"/>'
             f'<stop offset="0.5" stop-color="{ROSE}" stop-opacity="0.5"/><stop offset="1" stop-color="{GREEN}" stop-opacity="0.6"/></linearGradient></defs>',
             f'<rect x="40" y="{LY - .75}" width="{w - 80}" height="1.5" fill="url(#tl)"/>']
    for i, (color, icon, period, en, pt, where) in enumerate(JOURNEY["steps"]):
        x = 32 + i * col
        ty = LY - T / 2
        if i == len(JOURNEY["steps"]) - 1:  # etapa atual: aro pulsando em volta do ícone
            cxp = x + T / 2
            parts.append(f'<g transform="translate({cxp:.1f} {LY})"><rect x="{-T / 2}" y="{-T / 2}" width="{T}" height="{T}" rx="11" fill="none" stroke="{color}" stroke-width="1.5">'
                         '<animate attributeName="stroke-opacity" values="0.8;0" dur="2s" repeatCount="indefinite"/>'
                         '<animateTransform attributeName="transform" type="scale" values="1;1.35" dur="2s" repeatCount="indefinite"/></rect></g>')
        parts.append(f'<rect x="{x - 3}" y="{ty - 3}" width="{T + 6}" height="{T + 6}" rx="13" fill="{SURF_TOP}"/>')
        parts.append(tile(x, ty, T, color, ICONS[icon], r=11))
        parts += [cal(x, LY + 50, color, 11.5),
                  d.t(x + 17, LY + 50, period, 11.5, color, "mono"),
                  d.t(x, LY + 75, en, 15.5, TEXT, "s"),
                  d.t(x, LY + 95, pt, 12.5, MUTED, "i"),
                  d.t(x, LY + 119, where, 12.5, BODY, "r")]
    write("journey.svg", d.svg(w, h, JOURNEY["en"] + " " + " → ".join(s[3] for s in JOURNEY["steps"]), "\n".join(parts)))


# ── Formação, certificações e idiomas ──────────────────────────────────────
EDUCATION = [
    ("cap", BLUE, "Education", "Formação", [
        # (curso, instituição, período, badge de status)
        ("Software Engineering", "Instituto Infnet", "2023 — 2027", "in progress"),
        ("Architecture & Urbanism", "UniSociesc", "2007 — 2012", ""),
    ]),
    ("award", AMBER, "Certifications", "Certificações", [
        ("Pentest & Ethical Hacking", "2026"),
        ("AWS Cloud Practitioner Essentials", "2024"),
        ("Cloud Computing Applications", "2024"),
        ("Generative AI Fundamentals", "2024"),
    ]),
    ("globe", CYAN, "Languages", "Idiomas", [
        # (bandeira, idioma, nível no badge, cor, observação)
        ("br", "Portuguese", "Native · Nativo", GREEN, ""),
        ("gb", "English", "B2", BLUE, "→ C1"),
        ("jp", "Japanese", "JLPT N3", ROSE, ""),
    ]),
]


def build_education():
    d = Doc()
    w, h, gap = 960, 214, 16
    cw = (w - gap * 2) / 3
    parts = []
    for i, (icon, color, en, pt, items) in enumerate(EDUCATION):
        x = i * (cw + gap)
        g = [panel(cw, h, 14, tint=color, strength=0.07), tile(20, 20, 40, color, ICONS[icon]),
             d.t(74, 38, en, 15.5, TEXT, "s"), d.t(74, 57, pt, 12.5, MUTED, "i")]
        y = 96
        if icon == "cap":  # título + linha de apoio
            for title, inst, period, status in items:
                tx = 20
                if inst in INST_LOGOS:  # logo da instituição na frente do item
                    g.append(seal(20, y - 13, 30, inst))
                    tx = 62
                px = tx + width(inst, "r", 11.5) + 10
                g += [d.t(tx, y, title, 13.5, TEXT, "m"),
                      d.t(tx, y + 18, inst, 11.5, MUTED, "r"),
                      cal(px, y + 18, MUTED, 10.5),
                      d.t(px + 15, y + 18, period, 11.5, MUTED, "r")]
                assert px + 15 + width(period, "r", 11.5) < cw - 16, f"período estoura o cartão: {title}"
                if status:  # badge verde ao lado do título
                    sx = tx + width(title, "m", 13.5) + 8
                    sw = width(status, "m", 9.5) + 14
                    assert sx + sw < cw - 16, "badge de status estoura o cartão"
                    g += [f'<rect x="{sx + .5:.1f}" y="{y - 12.5}" width="{sw - 1:.1f}" height="17" rx="8.5" fill="{GREEN}" fill-opacity="0.12" stroke="{GREEN}" stroke-opacity="0.42"/>',
                          d.t(sx + sw / 2, y - 0.8, status, 9.5, GREEN, "m", anchor="middle")]
                y += 50
        elif icon == "globe":  # idiomas: nível em badge
            for code, name, level, lc, note in items:
                bw = width(level, "m", 10.5) + 18
                bx = cw - 20 - bw
                g += [flag(20, y, code), d.t(46, y, name, 12.5, BODY, "r"),
                      f'<rect x="{bx + .5:.1f}" y="{y - 14.5}" width="{bw - 1:.1f}" height="20" rx="10" fill="{lc}" fill-opacity="0.12" stroke="{lc}" stroke-opacity="0.42"/>',
                      d.t(bx + bw / 2, y - .5, level, 10.5, lc, "m", anchor="middle")]
                if note:
                    g.append(d.t(bx - 8, y - .5, note, 10.5, MUTED, "mono", anchor="end"))
                y += 30
        else:  # lista com valor à direita
            for title, val in items:
                g += [d.t(20, y, title, 12.5, BODY, "r"),
                      d.t(cw - 20, y, val, 11, MUTED, "mono", anchor="end")]
                if val.isdigit():  # é um ano
                    ix = cw - 20 - width(val, "mono", 11) - 16
                    g.append(cal(ix, y, MUTED, 10.5))
                    assert 20 + width(title, "r", 12.5) < ix - 8, f"título encosta no calendário: {title}"
                y += 26
        parts.append(f'<g transform="translate({x:.1f} 0)">{"".join(g)}</g>')
    write("education.svg", d.svg(w, h, "Education, certifications and languages", "\n".join(parts)))


# ── Detalhes: botão "todos os repositórios", legendas da toolbox e rodapé ──
CAPTIONS = {
    "languages": ("LANGUAGES & FRAMEWORKS", "LINGUAGENS E FRAMEWORKS"),
    "messaging": ("MESSAGING & DATA", "MENSAGERIA E DADOS"),
    "platform": ("PLATFORM & OBSERVABILITY", "PLATAFORMA E OBSERVABILIDADE"),
}


def bilingual_line(d, cx, y, en, pt, size=10.5, ls=2.6):
    """EN em destaque + PT esmaecido, centralizados em cx."""
    w_en = width(en, "s", size, ls)
    w_sep = width("  ·  ", "r", size)
    total = w_en + w_sep + width(pt, "m", size, ls)
    x = cx - total / 2
    return (d.t(x, y, en, size, LABEL, "s", ls=ls)
            + d.t(x + w_en, y, "  ·  ", size, MUTED, "r")
            + d.t(x + w_en + w_sep, y, pt, size, MUTED, "m", ls=ls)), total


def build_details():
    # botão para todos os repositórios
    d = Doc()
    en, pt = "VIEW ALL REPOSITORIES", "VER TODOS"
    h = 44
    _, tw = bilingual_line(Doc(), 0, 0, en, pt, 11, 2.4)
    w = int(tw + 84)
    line, _ = bilingual_line(d, w / 2 - 8, 27, en, pt, 11, 2.4)
    body = (f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="{h / 2}" fill="url(#surf)" stroke="{CHIP_BORDER}"/>'
            f'<rect x="{h / 2}" y=".5" width="{w - h}" height="1" fill="url(#hl)"/>'
            + line + arrow(w - 36, 15, BLUE))
    write("all-repos.svg", d.svg(w, h, "View all repositories · Ver todos os repositórios", body))

    # legendas da toolbox
    for key, (en, pt) in CAPTIONS.items():
        d = Doc()
        w, h = 620, 22
        line, tw = bilingual_line(d, w / 2, 15, en, pt)
        assert tw < w, key
        write_themed(f"caption-{key}.svg", d.svg(w, h, f"{en} · {pt}", line))

    # rodapé
    d = Doc()
    w, h = 960, 132
    body = (f'<defs><linearGradient id="fl" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{BORDER}" stop-opacity="0"/>'
            f'<stop offset="0.5" stop-color="{CHIP_BORDER}"/><stop offset="1" stop-color="{BORDER}" stop-opacity="0"/></linearGradient></defs>'
            f'<rect x="0" y="12" width="{w}" height="1" fill="url(#fl)"/>'
            '<!--light-only-->'
            f'<svg x="{w / 2 - 34}" y="22" width="68" height="68" viewBox="0 0 96 96" overflow="visible">{bkr_glyph()}</svg>'
            + d.t(w / 2, 100, "Thanks for stopping by", 13, BODY, "r", anchor="middle")
            + d.t(w / 2, 120, "Obrigado pela visita", 11.5, MUTED, "i", anchor="middle"))
    # no tema claro o símbolo (prateado) ganha um ladrilho escuro para ter contraste
    tile_light = f'<rect x="{w / 2 - 38}" y="28" width="76" height="56" rx="16" fill="{SURF_TOP}"/>'
    write_themed("footer.svg", d.svg(w, h, "Thanks for stopping by · Obrigado pela visita", body), tile_light)


def build_stack():
    for row, names in STACK_ROWS.items():
        w = len(names) * 300 - 44  # mesma geometria do skillicons.dev
        icons = "".join(f'<svg x="{i * 300}" width="256" height="256" viewBox="0 0 256 256">{icon_inner(n)}</svg>'
                        for i, n in enumerate(names))
        write(f"stack-{row}.svg", f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="256" viewBox="0 0 {w} 256" '
                                  f'role="img" aria-label="{", ".join(names)}">{icons}</svg>\n')


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    build_hero()
    build_sections()
    build_about()
    build_now()
    build_pillars()
    build_projects()
    build_links()
    build_journey()
    build_education()
    build_stack()
    build_details()
