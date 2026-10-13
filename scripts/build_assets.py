"""Gera o README do perfil em dois idiomas: README.md (inglês) e README.pt-BR.md
(português), com as imagens em assets/en/ e assets/pt/.

Uso:  pip install fonttools pillow
      python scripts/build_assets.py

Os textos ficam nos blocos de dados (HERO, ABOUT, NOW, PILLARS, PROJECTS, ...).
Valores com dois idiomas são dicionários {"en": ..., "pt": ...}; T() escolhe o
idioma da rodada. As fontes (Poppins e JetBrains Mono, licença OFL) vão embutidas
em cada SVG, recortadas só com os caracteres usados.
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
REPO = ROOT.parent
ASSETS = REPO / "assets"
FONTS = ROOT / "fonts"
PROFILE = "https://github.com/andrebecker84"
PT_README = "https://github.com/andrebecker84/andrebecker84/blob/main/README.pt-BR.md"

LANG = "en"              # idioma da rodada (en | pt)
OUT = ASSETS / LANG


def T(v):
    """Texto no idioma da rodada (ou o próprio valor, se não for bilíngue)."""
    return v[LANG] if isinstance(v, dict) else v


# ── Paleta ─────────────────────────────────────────────────────────────────
SURF_TOP, SURF_BOT = "#0f1729", "#0a101d"
BORDER = "#1c2740"
CHIP_BORDER = "#26324c"
TEXT = "#f1f4f9"
BODY = "#aab6cb"
MUTED = "#6b7896"
LABEL = "#8a97b2"
DESC = "#9ca9bf"   # descrição dos projetos: abaixo do BODY, ainda AAA (7.1:1) sobre o cartão

BLUE = "#60a5fa"
AMBER = "#f5b14c"
VIOLET = "#c084fc"
CYAN = "#22d3ee"
GREEN = "#34d399"
ROSE = "#f472b6"
LIME = "#a3e635"

def mix(c, t="#e6ebf5", k=0.45):
    """Aproxima a cor de um branco frio: mantém o matiz, tira a saturação gritante."""
    a = [int(c[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(t[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x * (1 - k) + y * k):02x}" for x, y in zip(a, b))


# ── Tipografia ─────────────────────────────────────────────────────────────
FACES = {  # chave: (família, peso, itálico, arquivo)
    "l": ("P", 300, False, "Poppins-Light.ttf"),
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


def panel(w, h, r=16, x=0, y=0, tint=None, horizontal=False, strength=0.10, edge=0.26):
    """Superfície plana, borda fina e um brilho sutil na aresta superior.
    Com `tint`, ganha um véu suave da cor (de cima para baixo, ou da esquerda) e a borda levemente tingida."""
    stroke = f'stroke="{tint}" stroke-opacity="{edge}"' if tint and edge else f'stroke="{BORDER}"'
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


# bandeiras em vetor: retangular (18 × 12) nas listas, redonda no seletor de idioma
FLAG_ART = {
    "br": ('<rect width="18" height="12" fill="#009c3b"/><path d="M9 1.6 16.2 6 9 10.4 1.8 6Z" fill="#ffdf00"/>'
           '<circle cx="9" cy="6" r="2.7" fill="#002776"/>'),
    "gb": ('<rect width="18" height="12" fill="#012169"/>'
           '<path d="M0 0 18 12M18 0 0 12" stroke="#fff" stroke-width="2.6"/>'
           '<path d="M0 0 18 12M18 0 0 12" stroke="#c8102e" stroke-width="0.9"/>'
           '<path d="M9 0v12M0 6h18" stroke="#fff" stroke-width="3.6"/>'
           '<path d="M9 0v12M0 6h18" stroke="#c8102e" stroke-width="2"/>'),
    "jp": '<rect width="18" height="12" fill="#fff"/><circle cx="9" cy="6" r="3.6" fill="#bc002d"/>',
}
ROUND_FLAG = {
    "br": ('<rect width="16" height="16" fill="#009c3b"/><path d="M8 2.6 14.6 8 8 13.4 1.4 8Z" fill="#ffdf00"/>'
           '<circle cx="8" cy="8" r="3.1" fill="#002776"/><path d="M5.1 7.2c1.9-.4 4-.1 5.8.9" stroke="#fff" stroke-width=".55" fill="none"/>'),
    "gb": ('<rect width="16" height="16" fill="#012169"/><path d="M0 0 16 16M16 0 0 16" stroke="#fff" stroke-width="3"/>'
           '<path d="M0 0 16 16M16 0 0 16" stroke="#c8102e" stroke-width="1"/><path d="M8 0v16M0 8h16" stroke="#fff" stroke-width="4.4"/>'
           '<path d="M8 0v16M0 8h16" stroke="#c8102e" stroke-width="2.4"/>'),
}


def flag(x, baseline, code):
    y = baseline - 10.5
    cid = f"fl{code}"
    return (f'<g transform="translate({x} {y:.1f})"><clipPath id="{cid}"><rect width="18" height="12" rx="2.5"/></clipPath>'
            f'<g clip-path="url(#{cid})">{FLAG_ART[code]}</g><rect x=".25" y=".25" width="17.5" height="11.5" rx="2.4" fill="none" stroke="#fff" stroke-opacity="0.18" stroke-width=".5"/></g>')


def cal(x, baseline, color, size=11):
    """Ícone de calendário alinhado à linha de base do texto ao lado."""
    k = size / 12
    return (f'<g transform="translate({x:.1f} {baseline - size + .5:.1f}) scale({k:.3f})" fill="none" stroke="{color}" '
            f'stroke-width="{1.15 / k:.2f}" stroke-linecap="round" stroke-linejoin="round">'
            '<rect x="1" y="2" width="10" height="9" rx="1.8"/><path d="M1 5h10M4 .8v2.4M8 .8v2.4"/></g>')


def arrow(x, y, color=MUTED):
    return (f'<g transform="translate({x} {y})" fill="none" stroke="{color}" stroke-width="1.5" stroke-linecap="round">'
            '<path d="M3 11 11 3M5 3h6v6"/></g>')


def write(name, content, shared=False):
    folder = ASSETS if shared else OUT
    folder.mkdir(parents=True, exist_ok=True)
    (folder / name).write_text(content, encoding="utf-8")
    label = name if shared else f"{LANG}/{name}"
    print(f"  ok {label:<37} {len(content.encode()) // 1024:>4} KB")


# Peças com fundo transparente (títulos, legendas, rodapé) ganham uma versão
# para o tema claro do GitHub; o README escolhe com <picture> + prefers-color-scheme.
LIGHT = {TEXT: "#1f2328", BODY: "#424a53", LABEL: "#424a53", MUTED: "#6e7781",
         BORDER: "#d0d7de", CHIP_BORDER: "#d0d7de", BLUE: "#0969da"}


def write_themed(name, content, light_extra=None, light_map=None):
    write(name, content.replace("<!--light-only-->", ""))
    light = content
    for dark_c, light_c in {**LIGHT, **(light_map or {})}.items():
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
    "contact": '<rect x="4" y="6" width="20" height="16" rx="3"/><circle cx="10.5" cy="12" r="2.5"/>'
               '<path d="M7 18.6c.6-2 1.9-3 3.5-3s2.9 1 3.5 3M16.5 11.7h4M16.5 15.7h3"/>',
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


# ── Seletor de idioma ──────────────────────────────────────────────────────
def build_lang_toggle():
    """Pílula com as duas bandeiras; a do idioma atual fica acesa."""
    d = Doc()
    w, h = TOPBAR[1] - TOPGAP, 38          # mesma largura do bloco do my-links
    half = (w - 8) / 2
    items = [("gb", "EN", "en"), ("br", "PT", "pt")]
    parts = [f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="{h / 2}" fill="url(#surf)" stroke="{CHIP_BORDER}"/>']
    for i, (code, label, lang) in enumerate(items):
        x = 4 + i * half
        on = lang == LANG
        if on:
            parts.append(f'<rect x="{x}" y="4" width="{half}" height="30" rx="15" fill="#fff" fill-opacity="0.08"/>')
        parts.append(f'<g transform="translate({x + 12} 11)" opacity="{1 if on else 0.4}"><clipPath id="r{code}"><circle cx="8" cy="8" r="8"/></clipPath>'
                     f'<g clip-path="url(#r{code})">{ROUND_FLAG[code]}</g><circle cx="8" cy="8" r="7.75" fill="none" stroke="#fff" stroke-opacity=".25" stroke-width=".5"/></g>')
        parts.append(d.t(x + 34, 24.5, label, 12.5, TEXT if on else MUTED, "s", ls=1))
    write("lang.svg", d.svg(w, h, "English · Português", "".join(parts)))


def build_mylinks_pill():
    """Bloco à direita da faixa do Agora, embaixo do idioma (mesma altura): atalho para o my-links."""
    d = Doc()
    _, w, h = TOPBAR
    gap = TOPGAP                               # respiro entre a faixa e o bloco (à esquerda)
    label = "my-links"
    tw = 22 + 8 + width(label, "s", 14.5, 0.4)
    x0 = gap + (w - gap - tw) / 2
    body = (f'<rect x="{gap + .5}" y=".5" width="{w - gap - 1}" height="{h - 1}" rx="14" fill="url(#surf)" stroke="{CYAN}" stroke-opacity="0.35"/>'
            f'<rect x="{gap + 1}" y="1" width="{w - gap - 2}" height="{h - 2}" rx="13.5" fill="{CYAN}" fill-opacity="0.07"/>'
            f'<g transform="translate({x0 - 2:.1f} {h / 2 - 11}) scale(.8)" fill="none" stroke="{CYAN}" stroke-width="2" stroke-linecap="round">{ICONS["links"]}</g>'
            + d.t(x0 + 30, h / 2 + 5, label, 14.5, TEXT, "s", ls=0.4))
    write("my-links.svg", d.svg(w, h, "my-links", body))


# ── Hero ───────────────────────────────────────────────────────────────────
HERO = {
    "kicker": {"en": "SOFTWARE ENGINEER", "pt": "ENGENHEIRO DE SOFTWARE"},
    "name": "André Luis Becker",
    "tagline": {"en": "Backend, architecture & AI agents for systems that scale.",
                "pt": "Backend, arquitetura e agentes de IA para sistemas que escalam."},
    "chips": ["Java 25", "Spring Boot 4", "Kafka", "Kubernetes", {"en": "AI Agents", "pt": "Agentes de IA"}],
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

    # Lado esquerdo: identidade (um idioma só, centralizado com o diagrama)
    x0 = 72
    name_w = width(hero["name"], "s", 58)
    tagline = T(hero["tagline"])
    # a frase quebra em duas linhas se não couber antes do diagrama; o bloco sobe para seguir centralizado
    tag_lines = wrap(tagline, "r", 23, 640)
    up = 15 * (len(tag_lines) - 1)
    left = [
        f'<rect x="{x0}" y="{123 - up}" width="22" height="2" rx="1" fill="{AMBER}"/>',
        d.t(x0 + 34, 130 - up, T(hero["kicker"]), 16, LABEL, "m", ls=4),
        d.t(x0 - 2, 194 - up, hero["name"], 58, TEXT, "s"),
    ]
    left += [d.t(x0, 240 - up + i * 31, ln, 23, BODY, "r") for i, ln in enumerate(tag_lines)]
    chips_y = 272 - up + (len(tag_lines) - 1) * 31
    cx = x0
    for c in hero["chips"]:
        c = T(c)
        cw = width(c, "m", 16) + 30
        left.append(f'<rect x="{cx + .5}" y="{chips_y + .5}" width="{cw - 1:.1f}" height="37" rx="18.5" fill="#fff" fill-opacity="0.035" stroke="{CHIP_BORDER}"/>')
        left.append(d.t(cx + cw / 2, chips_y + 24.2, c, 16, BODY, "m", anchor="middle"))
        cx += cw + 10
    assert name_w < 660, name_w
    assert cx - 10 < 724, f"chips invadem o diagrama: {cx}"

    # Lado direito: diagrama orientado a eventos (animado)
    BX1, BX2, BY = 744, 1222, 208
    box_h = 54

    # Colunas alinhadas: cada produtor (em cima) fica sobre um consumidor (embaixo),
    # com um único ponto de junção por coluna no barramento.
    bw = max(width(l, "mono", 16) for l, _, _ in hero["top"] + hero["bottom"]) + 66
    gap = 18
    ncol = len(hero["top"])
    x_start = (BX1 + BX2) / 2 - (ncol * bw + (ncol - 1) * gap) / 2

    def boxes(items, y):
        return [(x_start + k * (bw + gap), y, bw, l, ic, col) for k, (l, ic, col) in enumerate(items)]

    top = boxes(hero["top"], 108)
    bottom = boxes(hero["bottom"], 256)
    assert len(top) == len(bottom)
    assert top[0][0] > BX1 and bottom[0][0] > BX1, "diagrama largo demais"
    g = [f'<rect x="{BX1}" y="{BY - 1}" width="{BX2 - BX1}" height="2" fill="url(#bus)"/>',
         # ícone do Kafka (nós do cluster) + rótulo, embaixo do barramento
         f'<g transform="translate({BX1 - 3} {BY + 13}) scale(1.05)" fill="none" stroke="{AMBER}" stroke-opacity="0.9" stroke-width="1.3" stroke-linecap="round">'
         '<circle cx="7" cy="8" r="1.8"/><circle cx="7" cy="2.8" r="1.3"/><circle cx="7" cy="13.2" r="1.3"/>'
         '<circle cx="12.3" cy="5.4" r="1.3"/><circle cx="12.3" cy="10.6" r="1.3"/>'
         '<path d="M7 4.1v2.1M7 9.8v2.1M8.6 7.2l2.6-1.3M8.6 8.8l2.6 1.3"/></g>',
         d.t(BX1 + 17, BY + 26, "kafka", 14.5, MUTED, "mono")]
    assert BX1 + 17 + width("kafka", "mono", 14.5) < x_start + bw / 2 - 8, "rótulo do barramento encosta no conector"
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
        tx, ty, ts = x + 10, y + (box_h - 32) / 2, 32
        g.append(f'<rect x="{tx + .5:.1f}" y="{ty + .5}" width="{ts - 1}" height="{ts - 1}" rx="8" fill="{color}" fill-opacity="0.12" stroke="{color}" stroke-opacity="0.38"/>')
        g.append(f'<g transform="translate({tx + 6.4:.1f} {ty + 6.4}) scale(1.2)" fill="none" stroke="{color}" stroke-width="1.25" stroke-linecap="round" stroke-linejoin="round">{ICONS16[ic]}</g>')
        g.append(d.t(x + 52, y + box_h / 2 + 5.5, l, 16, BODY, "mono"))
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
    write("hero.svg", d.svg(W, H, f'{hero["name"]} · {T(hero["kicker"]).title()} · {tagline}', body, defs))


# ── Títulos de seção ───────────────────────────────────────────────────────
SECTIONS = [
    ("about", {"en": "ABOUT", "pt": "SOBRE"}),
    ("journey", {"en": "JOURNEY", "pt": "TRAJETÓRIA"}),
    ("focus", {"en": "FOCUS", "pt": "FOCO"}),
    ("work", {"en": "FEATURED WORK", "pt": "PROJETOS EM DESTAQUE"}),
    ("education", {"en": "EDUCATION", "pt": "FORMAÇÃO"}),
    ("toolbox", {"en": "TOOLBOX", "pt": "FERRAMENTAS"}),
    ("connect", {"en": "CONNECT", "pt": "CONTATO"}),
]


def build_sections():
    for n, (key, label) in enumerate(SECTIONS, 1):
        d = Doc()
        w, h, ls = 960, 40, 3.2
        label = T(label)
        end = 40 + width(label, "s", 14.5, ls) + 18
        body = (d.t(0, 26, f"{n:02d}", 14, BLUE, "mono")
                + f'<rect x="25" y="15" width="1" height="14" fill="{CHIP_BORDER}"/>'
                + d.t(40, 26, label, 14.5, TEXT, "s", ls=ls)
                + f'<rect x="{end:.1f}" y="20" width="{w - end:.1f}" height="1" fill="url(#rule)"/>')
        write_themed(f"section-{key}.svg", d.svg(w, h, label.title(), body))


# ── About: saudação como um log de eventos ─────────────────────────────────
ABOUT = {
    "text": {
        "en": ("I design and build backend systems that scale: distributed, event-driven services in Java "
               "and Spring, shipped to Kubernetes with observability built in from day one. "
               "Lately exploring AI agents and machine learning."),
        "pt": ("Projeto e construo sistemas backend que escalam: serviços distribuídos e orientados a eventos "
               "em Java e Spring, entregues no Kubernetes com observabilidade desde o primeiro dia. "
               "Recentemente explorando agentes de IA e machine learning."),
    },
    # selo: país + modalidades (preferência em destaque, presencial discreto)
    "place": [({"en": "Brazil", "pt": "Brasil"}, "m", "text"), ({"en": "Remote", "pt": "Remoto"}, "s", "pref"),
              ({"en": "Hybrid", "pt": "Híbrido"}, "s", "pref"), ({"en": "On-site", "pt": "Presencial"}, "r", "alt")],
    "events": [  # (cor, evento, payload)
        (BLUE, "VisitorArrived", '{ from: "github" }'),
        (AMBER, "GreetingEmitted", {"en": '{ text: "Hello!" }', "pt": '{ texto: "Olá!" }'}),
        (GREEN, "IntroductionReady", {"en": '{ next: "scroll ↓" }', "pt": '{ próximo: "role ↓" }'}),
    ],
}


def build_about():
    d = Doc()
    a = ABOUT
    w, h = 960, 250
    # janela de terminal à esquerda, do tamanho da linha mais longa do log; o texto ocupa o resto
    log_w = max([width("tail -f profile.events", "mono", 14)]
                + [width(ev, "mono", 14) for _, ev, _ in a["events"]]
                + [width(T(pl), "mono", 13) for _, _, pl in a["events"]])
    TX, TY, BAR = 18, 18, 30
    TW, TH = round(54 + log_w + 62 - TX), h - 2 * TY
    RX = TX + TW + 36
    RW = w - RX - 36
    lines = wrap(T(a["text"]), "l", 16.5, RW)
    block = len(lines) * 26 + 22 + 33          # texto + respiro + selo
    y0 = (h - block) / 2 + 14                  # coluna da direita centralizada

    term = [f'<defs><clipPath id="tc"><rect x="{TX}" y="{TY}" width="{TW}" height="{TH}" rx="12"/></clipPath>'
            '<pattern id="scan" width="4" height="3" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#fff" fill-opacity="0.025"/></pattern>'
            f'<radialGradient id="glow" cx="0.2" cy="0.25" r="0.9"><stop offset="0" stop-color="{GREEN}" stop-opacity="0.07"/>'
            f'<stop offset="1" stop-color="{GREEN}" stop-opacity="0"/></radialGradient>'
            '<filter id="tsh" x="-20%" y="-20%" width="140%" height="150%"><feGaussianBlur stdDeviation="9"/></filter></defs>',
            # sombra: cópia escura e desfocada, um pouco abaixo da janela
            f'<rect x="{TX + 4}" y="{TY + 12}" width="{TW - 8}" height="{TH - 6}" rx="14" fill="#000" fill-opacity="0.75" filter="url(#tsh)"/>',
            f'<rect x="{TX + .5}" y="{TY + .5}" width="{TW - 1}" height="{TH - 1}" rx="12" fill="#070b14"/>',
            f'<g clip-path="url(#tc)"><rect x="{TX}" y="{TY}" width="{TW}" height="{BAR}" fill="#fff" fill-opacity="0.035"/>'
            f'<rect x="{TX}" y="{TY + BAR}" width="{TW}" height="{TH - BAR}" fill="url(#glow)"/>'
            f'<rect x="{TX}" y="{TY + BAR}" width="{TW}" height="{TH - BAR}" fill="url(#scan)"/></g>',
            f'<rect x="{TX}" y="{TY + BAR}" width="{TW}" height="1" fill="{BORDER}"/>',
            f'<rect x="{TX + .5}" y="{TY + .5}" width="{TW - 1}" height="{TH - 1}" rx="12" fill="none" stroke="{CHIP_BORDER}"/>']
    for k, c in enumerate(("#ff5f57", "#febc2e", "#28c840")):   # botões da janela, discretos
        term.append(f'<circle cx="{TX + 17 + k * 15}" cy="{TY + BAR / 2}" r="4.2" fill="{c}" fill-opacity="0.75"/>')
    term.append(d.t(TX + TW / 2 + 22, TY + BAR / 2 + 4, "andre@bkr: ~", 11.5, MUTED, "mono", anchor="middle"))

    # Log de eventos: as linhas entram em sequência e o ciclo recomeça
    CYCLE = 11
    cmd_y = TY + BAR + 28
    log = [d.t(36, cmd_y, "$", 14, GREEN, "mono"),
           d.t(54, cmd_y, "tail -f profile.events", 14, MUTED, "mono")]
    for i, (color, ev, payload) in enumerate(a["events"]):
        y = cmd_y + 36 + i * 36
        t0 = (0.8 + i * 1.1) / CYCLE
        t1 = t0 + 0.035
        kt = f"0;{t0:.3f};{t1:.3f};0.93;1"
        anim = (f'<animate attributeName="opacity" values="0;0;1;1;0" keyTimes="{kt}" dur="{CYCLE}s" repeatCount="indefinite"/>'
                f'<animateTransform attributeName="transform" type="translate" values="8 0;8 0;0 0;0 0;0 0" keyTimes="{kt}" dur="{CYCLE}s" repeatCount="indefinite"/>')
        log.append(f'<g opacity="0">{anim}'
                   f'<circle cx="41" cy="{y - 4}" r="3.2" fill="{color}"/>'
                   + d.t(54, y, ev, 14, TEXT, "mono")
                   + d.t(54, y + 17, T(payload), 13, MUTED, "mono")
                   + '</g>')
    cy = cmd_y + 36 + len(a["events"]) * 36
    log.append(f'<rect x="36" y="{cy - 13}" width="8" height="16" rx="1" fill="{GREEN}">'
               '<animate attributeName="opacity" values="1;0" dur="1.05s" calcMode="discrete" repeatCount="indefinite"/></rect>')
    log = term + log

    right = [d.t(RX, y0 + i * 26, ln, 16.5, BODY, "l") for i, ln in enumerate(lines)]
    # selo de localização e modalidades, em pílula com tom azul
    top = y0 + (len(lines) - 1) * 26 + 22
    colors = {"text": TEXT, "pref": BLUE, "alt": MUTED}
    x = RX + 34
    pill_parts = []
    for i, (label, face, kind) in enumerate(a["place"]):
        label = T(label)
        if i:
            pill_parts.append(d.t(x + 7, top + 21.5, "·", 14, MUTED, "r"))
            x += width("·", "r", 14) + 14
        pill_parts.append(d.t(x, top + 21.5, label, 14, colors[kind], face))
        x += width(label, face, 14)
    pill_w = x + 16 - RX
    assert RX + pill_w < w - 24, "selo de localização estoura o painel"
    assert top + 33 < h - 16, "texto do About não cabe no painel"
    assert cy + 3 < TY + TH - 8, "log do About não cabe no terminal"
    right.append(f'<rect x="{RX + .5}" y="{top + .5}" width="{pill_w - 1:.1f}" height="33" rx="16.5" '
                 f'fill="{BLUE}" fill-opacity="0.10" stroke="{BLUE}" stroke-opacity="0.38"/>')
    right.append(f'<g transform="translate({RX + 13} {top + 9.5})" fill="none" stroke="{BLUE}" stroke-width="1.5">'
                 '<path d="M6 1.5a4.5 4.5 0 0 1 4.5 4.5c0 3.4-4.5 8-4.5 8S1.5 9.4 1.5 6A4.5 4.5 0 0 1 6 1.5Z"/><circle cx="6" cy="6" r="1.6"/></g>')
    right += pill_parts

    body = f"""{panel(w, h)}
{"".join(log)}
{"".join(right)}"""
    write("about.svg", d.svg(w, h, T(a["text"]), body))


# ── Now ────────────────────────────────────────────────────────────────────
NOW = {
    "label": {"en": "NOW", "pt": "AGORA"},
    "headline": {"en": "Event-driven microservices", "pt": "Microsserviços orientados a eventos"},
    "stack": "Java 25 · Spring Boot 4 · Kafka · Kubernetes",
}


TOPBAR = (810, 150, 58)   # linha do topo: Agora + my-links somam 960 de largura, mesma altura
TOPGAP = 10               # respiro entre a faixa do Agora e o bloco do my-links


def build_now():
    """Faixa de fora a fora (com o my-links à direita): ponto pulsando, rótulo, manchete e stack em duas linhas."""
    d = Doc()
    w, _, h = TOPBAR
    label, head, stack = T(NOW["label"]), T(NOW["headline"]), NOW["stack"]
    lx = 40
    div = lx + width(label, "s", 13, 2.6) + 18
    assert div + 18 + max(width(head, "m", 16.5), width(stack, "mono", 14.5)) < w - 20, "Agora não cabe na faixa"
    body = f"""<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="14" fill="url(#surf)" stroke="{GREEN}" stroke-opacity="0.32"/>
<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="13.5" fill="url(#nowg)"/>
<circle cx="22" cy="{h / 2}" r="4.5" fill="none" stroke="{GREEN}" stroke-width="1.4">
  <animate attributeName="r" values="4.5;12" dur="2s" repeatCount="indefinite"/>
  <animate attributeName="stroke-opacity" values="0.7;0" dur="2s" repeatCount="indefinite"/>
</circle>
<circle cx="22" cy="{h / 2}" r="4.6" fill="{GREEN}">
  <animate attributeName="fill-opacity" values="1;0.55;1" dur="2s" repeatCount="indefinite"/>
</circle>
{d.t(lx, h / 2 + 4.6, label, 13, GREEN, "s", ls=2.6)}
<rect x="{div:.1f}" y="13" width="1" height="{h - 26}" fill="{GREEN}" fill-opacity="0.28"/>
{d.t(div + 18, 25.5, head, 16.5, TEXT, "m")}
{d.t(div + 18, 46, stack, 14.5, BODY, "mono")}"""
    defs = (f'<linearGradient id="nowg" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{GREEN}" stop-opacity="0.12"/>'
            f'<stop offset="0.6" stop-color="{GREEN}" stop-opacity="0.02"/><stop offset="1" stop-color="{GREEN}" stop-opacity="0"/></linearGradient>')
    write("now.svg", d.svg(w, h, f'{label}: {head} · {stack}', body, defs))


# ── Pilares ────────────────────────────────────────────────────────────────
PILLARS = [
    ("nodes", BLUE, {"en": "Distributed Systems", "pt": "Sistemas Distribuídos"},
     ["Microservices · API Gateway", "Service discovery · Resilience"]),
    ("bolt", AMBER, {"en": "Event-Driven", "pt": "Orientação a Eventos"},
     ["Kafka · RabbitMQ", "Outbox · Saga · Idempotency"]),
    ("hex", VIOLET, {"en": "Domain-Driven Design", "pt": "Domain-Driven Design"},
     [{"en": "Bounded contexts · Aggregates", "pt": "Bounded contexts · Agregados"},
      {"en": "Hexagonal architecture", "pt": "Arquitetura hexagonal"}]),
    ("cloud", CYAN, {"en": "Cloud-Native", "pt": "Cloud-Native"},
     ["Kubernetes · Docker · CI/CD", "OpenTelemetry · Prometheus"]),
    ("bot", ROSE, {"en": "AI Agents", "pt": "Agentes de IA"},
     [{"en": "LLM agents · Generative AI", "pt": "Agentes LLM · IA generativa"},
      {"en": "Automation · n8n · Ollama", "pt": "Automação · n8n · Ollama"}]),
    ("neural", LIME, {"en": "Machine Learning", "pt": "Machine Learning"},
     ["scikit-learn · XGBoost · SHAP", {"en": "NLP · Feature engineering", "pt": "NLP · Engenharia de features"}]),
]


def build_pillars():
    """Grade 2 × 3: ícone e título lado a lado, palavras-chave embaixo."""
    d = Doc()
    w, gap, ch, cols = 960, 16, 150, 2
    cw = (w - gap * (cols - 1)) / cols
    rows = (len(PILLARS) + cols - 1) // cols
    h = rows * ch + (rows - 1) * gap
    parts = []
    for i, (icon, color, title, kws) in enumerate(PILLARS):
        x, y = (i % cols) * (cw + gap), (i // cols) * (ch + gap)
        kw = "".join(d.t(20, 102 + j * 21, T(k), 12.5, BODY, "mono") for j, k in enumerate(kws))
        parts.append(f"""<g transform="translate({x:.1f} {y})">
  {panel(cw, ch, 14, tint=color, strength=0.035, edge=0)}
  {tile(20, 20, 42, color, ICONS[icon])}
  {d.t(76, 47.5, T(title), 17, TEXT, "s")}
  <rect x="20" y="77" width="22" height="2" rx="1" fill="{color}"/>
  {kw}
</g>""")
    write("focus.svg", d.svg(w, h, " · ".join(T(p[2]) for p in PILLARS), "\n".join(parts)))


# ── Projetos ───────────────────────────────────────────────────────────────
PROJECTS = [
    dict(slug="cinepass", url="https://github.com/andrebecker84/cinepass-ddd-event-driven-AT", color=AMBER,
         tag={"en": "EVENT-DRIVEN · OBSERVABILITY", "pt": "EVENTOS · OBSERVABILIDADE"}, title="CinePass",
         desc={"en": "Kafka in KRaft mode with transactional outbox, idempotent consumers, per-booking ordering and DLT replay. Logs in ELK, traces in Zipkin.",
               "pt": "Kafka em modo KRaft com outbox transacional, consumidores idempotentes, ordem por reserva e reprocessamento via DLT. Logs no ELK e traces no Zipkin."},
         chips=["Java 25", "Spring Boot 4", "Kafka"]),
    dict(slug="infnet-hub-prod", url="https://github.com/andrebecker84/TP5-PB_producao", color=CYAN,
         tag={"en": "PLATFORM · KUBERNETES", "pt": "PLATAFORMA · KUBERNETES"},
         title={"en": "Infnet Hub · Production", "pt": "Infnet Hub · Produção"},
         desc={"en": "Spring Boot microservices running on Kubernetes with full observability (Prometheus, Grafana, Loki, Tempo) and CI/CD.",
               "pt": "Microsserviços Spring Boot no Kubernetes com observabilidade completa (Prometheus, Grafana, Loki, Tempo) e CI/CD."},
         chips=["Kubernetes", "OpenTelemetry", "GitHub Actions"]),
    dict(slug="infnet-hub-events", url="https://github.com/andrebecker84/TP4-PB_eventos", color=AMBER,
         tag={"en": "EVENT-DRIVEN · SAGA", "pt": "EVENTOS · SAGA"},
         title={"en": "Infnet Hub · Events", "pt": "Infnet Hub · Eventos"},
         desc={"en": "Refactored to event-driven with RabbitMQ: outbox, quorum queues, DLQ, saga and request/reply, secured by a Keycloak BFF.",
               "pt": "Refatoração para eventos com RabbitMQ: outbox, filas quorum, DLQ, saga e request/reply, com segurança via BFF no Keycloak."},
         chips=["RabbitMQ", "Keycloak", "Next.js"]),
    dict(slug="async-messaging", url="https://github.com/andrebecker84/ecommerce-ddd-async-messaging-TP3", color=AMBER,
         tag={"en": "ASYNC MESSAGING · DDD", "pt": "MENSAGERIA ASSÍNCRONA · DDD"},
         title={"en": "E-commerce · Async Messaging", "pt": "E-commerce · Mensageria"},
         desc={"en": "Commands over RabbitMQ, events over Kafka, mirrored to SNS/SQS FIFO. Transactional outbox and inbox with an orchestrated saga.",
               "pt": "Comandos via RabbitMQ, eventos via Kafka e espelho em SNS/SQS FIFO. Outbox e inbox transacionais com saga orquestrada."},
         chips=["Kafka", "RabbitMQ", "AWS SQS"]),
    dict(slug="jwt-auth", url="https://github.com/andrebecker84/microservices-devops-api-vendas-TP3", color=BLUE,
         tag={"en": "SECURITY · REACTIVE", "pt": "SEGURANÇA · REATIVO"},
         title={"en": "Sales API · JWT Auth", "pt": "API de Vendas · JWT"},
         desc={"en": "Auth service with login and rotating refresh tokens, protected routes at the gateway and services. Reactive stack with WebFlux and R2DBC.",
               "pt": "Serviço de autenticação com login e refresh token rotativo, rotas protegidas no gateway e nos serviços. Stack reativa com WebFlux e R2DBC."},
         chips=["Spring Cloud", "WebFlux", "PostgreSQL"]),
    dict(slug="monolith-to-ms", url="https://github.com/andrebecker84/ecommerce-ddd-refactoring-TP1", color=VIOLET,
         tag={"en": "REFACTORING · HEXAGONAL", "pt": "REFATORAÇÃO · HEXAGONAL"},
         title={"en": "From Monolith to Microservices", "pt": "Do Monólito aos Microsserviços"},
         desc={"en": "Extracting the Payments bounded context from a live e-commerce monolith using DDD and Branch by Abstraction.",
               "pt": "Extração do contexto de Pagamento de um monólito de e-commerce em produção, com DDD e Branch by Abstraction."},
         chips=["DDD", "Ports & Adapters", "Strangler Fig"]),
    dict(slug="ml-portfolio", url="https://github.com/andrebecker84/ml-portfolio", color=LIME,
         tag={"en": "MACHINE LEARNING · NLP", "pt": "MACHINE LEARNING · NLP"},
         title={"en": "Machine Learning Portfolio", "pt": "Portfólio de Machine Learning"},
         desc={"en": "Notebooks covering classification, clustering, feature engineering and NLP, with model interpretability through SHAP.",
               "pt": "Notebooks de classificação, clustering, engenharia de features e NLP, com interpretabilidade de modelos via SHAP."},
         chips=["scikit-learn", "XGBoost", "SHAP"]),
]


SHOTS = ROOT / "shots"   # miniaturas dos projetos (560 × 336, JPEG), uma por slug, quando houver


def build_projects():
    """Um cartão por linha: categoria, título, descrição e chips; screenshot à direita quando o projeto tiver."""
    w = 960
    TW, TH = 280, 168                     # miniatura
    shot_x = w - 18 - TW
    text_r = {True: shot_x - 30, False: w - 30}   # limite direito do texto, com e sem miniatura

    def has_shot(p):
        return (SHOTS / f"{p['slug']}.jpg").exists()

    def desc_lines(p):
        return wrap(T(p["desc"]), "r", 14.5, text_r[has_shot(p)] - 30)

    nmax = max(len(desc_lines(p)) for p in PROJECTS)
    h = max(TH + 36, round(102 + (nmax - 1) * 22 + 18 + 28 + 22))
    for p in PROJECTS:
        d = Doc()
        shot = has_shot(p)
        right = text_r[shot]
        title = T(p["title"])
        body = [panel(w, h),
                f'<circle cx="35" cy="35" r="3.5" fill="{p["color"]}"/>',
                d.t(48, 39.5, T(p["tag"]), 12, LABEL, "s", ls=1.8),
                arrow(right - 16, 24),
                f'<g transform="translate(28 53) scale(.92)" fill="{p["color"]}" fill-opacity="0.14" stroke="{p["color"]}" '
                f'stroke-width="1.45" stroke-linejoin="round">{ICONS["folder"]}</g>',
                d.t(58, 72.5, title, 18, TEXT, "s")]
        assert 58 + width(title, "s", 18) < right, f"título longo demais: {title}"
        y = 102
        for ln in desc_lines(p):
            body.append(d.t(30, y, ln, 14.5, DESC, "r"))
            y += 22
        # chips embaixo da descrição
        cy, cx = y - 22 + 18, 30
        for c in p["chips"]:
            cw = width(c, "m", 12.5) + 26
            body.append(f'<rect x="{cx + .5:.1f}" y="{cy + .5}" width="{cw - 1:.1f}" height="28" rx="14" fill="#fff" fill-opacity="0.035" stroke="{CHIP_BORDER}"/>')
            body.append(d.t(cx + cw / 2, cy + 18.5, c, 12.5, LABEL, "m", anchor="middle"))
            cx += cw + 8
        assert cx - 8 < right and cy + 28 < h - 14, (p["slug"], LANG, cx, cy)
        if shot:  # miniatura com cantos arredondados e borda na cor do projeto
            b64 = base64.b64encode((SHOTS / f"{p['slug']}.jpg").read_bytes()).decode()
            ty = (h - TH) / 2
            body += [f'<clipPath id="th"><rect x="{shot_x}" y="{ty}" width="{TW}" height="{TH}" rx="10"/></clipPath>',
                     f'<image x="{shot_x}" y="{ty}" width="{TW}" height="{TH}" preserveAspectRatio="xMidYMid slice" clip-path="url(#th)" '
                     f'href="data:image/jpeg;base64,{b64}"/>',
                     f'<rect x="{shot_x + .5}" y="{ty + .5}" width="{TW - 1}" height="{TH - 1}" rx="10" fill="none" stroke="{p["color"]}" stroke-opacity="0.35"/>']
        write(f"project-{p['slug']}.svg", d.svg(w, h, f'{title}: {T(p["desc"])}', "\n".join(body)))


# ── Contato ────────────────────────────────────────────────────────────────
LINKS = [
    ("linkedin", BLUE, "LinkedIn", "in/becker84", "https://www.linkedin.com/in/becker84"),
    ("contact", AMBER, {"en": "Contact", "pt": "Contato"}, {"en": "phone · e-mail · résumé", "pt": "telefone · e-mail · CV"},
     "https://andrebecker84.github.io/my-links/#contato"),
    ("links", CYAN, "Links", "andrebecker84.github.io", "https://andrebecker84.github.io/my-links/"),
]


def build_links():
    w, h = 300, 68
    for icon, color, label, sub, _ in LINKS:
        d = Doc()
        locked = icon == "contact"   # seção fechada: cadeado no canto do ícone e chave no lugar da seta
        body = (panel(w, h, 14) + tile(16, 16, 36, color, ICONS[icon], r=9)
                + d.t(66, 31, T(label), 16, TEXT, "s")
                + d.t(66, 50, T(sub), 12.5, MUTED, "mono"))
        if locked:
            body += (f'<circle cx="50" cy="50" r="8.5" fill="{SURF_BOT}" stroke="{color}" stroke-opacity="0.5"/>'
                     f'<g transform="translate(44.5 44.5) scale(.92)" fill="none" stroke="{color}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
                     '<rect x="2.4" y="5.4" width="7.2" height="5" rx="1.3"/><path d="M4.1 5.4V4a1.9 1.9 0 0 1 3.8 0v1.4"/></g>'
                     f'<g transform="translate({w - 41} 25) scale(1.15)" fill="none" stroke="{color}" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round">'
                     '<circle cx="4.8" cy="8" r="2.9"/><path d="M7.7 8h6.6M12.1 8v2.4M14.3 8v1.7"/></g>')
            assert 66 + width(T(sub), "mono", 12.5) < w - 46, f"subtítulo do contato encosta na chave ({LANG})"
        else:
            body += arrow(w - 36, 27)
        write(f"link-{icon}.svg", d.svg(w, h, f"{T(label)}: {T(sub)}", body))


# ── Trajetória ─────────────────────────────────────────────────────────────
JOURNEY = {
    "hook": {"en": "From designing buildings to designing systems.", "pt": "De projetar edifícios a projetar sistemas."},
    "steps": [  # (cor, ícone, período, papel, onde)
        (VIOLET, "building", "2007 — 2017", {"en": "Architecture & Urbanism", "pt": "Arquitetura e Urbanismo"},
         {"en": "Brazil · 10 years of practice", "pt": "Brasil · 10 anos de atuação"}),
        (ROSE, "inspect", "2017 — 2022", {"en": "Quality Control", "pt": "Controle de Qualidade"},
         {"en": "Japan · Toyota Boshoku, Lexus, Suzuki", "pt": "Japão · Toyota Boshoku, Lexus, Suzuki"}),
        (GREEN, "code", {"en": "2023 — now", "pt": "2023 — hoje"}, {"en": "Software Engineering", "pt": "Engenharia de Software"},
         {"en": "Brazil · Instituto Infnet", "pt": "Brasil · Instituto Infnet"}),
    ],
}


def bubble(x, y, w, h, r, tx, tw=18, th=11):
    """Retângulo arredondado com uma ponta no topo apontando para (tx, y - th)."""
    return (f"M{x + r:.1f} {y} H{tx - tw / 2:.1f} L{tx:.1f} {y - th} L{tx + tw / 2:.1f} {y} H{x + w - r:.1f} "
            f"A{r} {r} 0 0 1 {x + w:.1f} {y + r} V{y + h - r} A{r} {r} 0 0 1 {x + w - r:.1f} {y + h} "
            f"H{x + r:.1f} A{r} {r} 0 0 1 {x:.1f} {y + h - r} V{y + r} A{r} {r} 0 0 1 {x + r:.1f} {y} Z")


PAGE = "#0d1117"   # fundo do GitHub (escuro); recorta a linha tracejada atrás dos ícones


def build_journey():
    """Sem cartão: frase, linha do tempo tracejada e um balão saindo de cada ícone."""
    d = Doc()
    w, gap, T_ = 960, 16, 44
    LY = 80                                   # altura da linha do tempo
    bw = (w - gap * 2) / 3
    top = LY + T_ / 2 + 14                    # topo dos balões (a ponta sobe até o ícone)
    bh = 104
    h = int(top + bh + 2)
    steps = JOURNEY["steps"]
    defs = (f'<linearGradient id="tl" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="{w}" y2="0"><stop offset="0" stop-color="{VIOLET}" stop-opacity="0.38"/>'
            f'<stop offset="0.5" stop-color="{ROSE}" stop-opacity="0.38"/><stop offset="1" stop-color="{GREEN}" stop-opacity="0.5"/></linearGradient>'
            + "".join(f'<linearGradient id="b{i}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{c}" stop-opacity="0.05"/>'
                      f'<stop offset="1" stop-color="{c}" stop-opacity="0.02"/></linearGradient>' for i, (c, *_) in enumerate(steps)))
    hook = T(JOURNEY["hook"])
    hw = width(hook, "i", 19)
    parts = [  # frase como pensamento: itálico entre aspas grandes nas cores da linha do tempo
             d.t(0, 44, "“", 48, VIOLET, "s", extra='fill-opacity="0.5"'),
             f'<defs><linearGradient id="hk" gradientUnits="userSpaceOnUse" x1="30" y1="0" x2="{30 + hw:.0f}" y2="0">'
             f'<stop offset="0" stop-color="{mix(VIOLET)}"/><stop offset="0.5" stop-color="{mix(ROSE)}"/><stop offset="1" stop-color="{mix(GREEN)}"/></linearGradient></defs>',
             d.t(30, 30, hook, 19, "url(#hk)", "i"),
             d.t(30 + hw + 6, 44, "”", 48, GREEN, "s", extra='fill-opacity="0.5"'),
             f'<line x1="0" y1="{LY}" x2="{w}" y2="{LY}" stroke="url(#tl)" stroke-width="1.6" stroke-dasharray="7 6" stroke-linecap="round"/>']
    for i, (color, icon, period, role, where) in enumerate(steps):
        x = i * (bw + gap)
        ix = x + 22                           # ícone alinhado à esquerda do balão
        icx = ix + T_ / 2
        ty = LY - T_ / 2
        parts.append(f'<rect x="{ix - 6:.1f}" y="{ty - 6}" width="{T_ + 12}" height="{T_ + 12}" rx="15" fill="{PAGE}"/>')
        if i == len(steps) - 1:  # etapa atual: aro pulsando em volta do ícone
            parts.append(f'<g transform="translate({icx:.1f} {LY})"><rect x="{-T_ / 2}" y="{-T_ / 2}" width="{T_}" height="{T_}" rx="12" fill="none" stroke="{color}" stroke-width="1.5">'
                         '<animate attributeName="stroke-opacity" values="0.8;0" dur="2s" repeatCount="indefinite"/>'
                         '<animateTransform attributeName="transform" type="scale" values="1;1.35" dur="2s" repeatCount="indefinite"/></rect></g>')
        parts.append(tile(ix, ty, T_, color, ICONS[icon], r=12))
        path = bubble(x + .5, top, bw - 1, bh - 1, 14, icx)
        parts += [f'<path d="{path}" fill="url(#surf)"/>',
                  f'<path d="{path}" fill="url(#b{i})" stroke="{CHIP_BORDER}"/>',
                  cal(x + 22, top + 30, color, 13),
                  d.t(x + 41, top + 30, T(period), 13, color, "mono"),
                  d.t(x + 22, top + 58, T(role), 17.5, TEXT, "s"),
                  d.t(x + 22, top + 83, T(where), 14, BODY, "r")]
        assert x + 22 + width(T(where), "r", 14) < x + bw - 14, f"texto estoura o balão: {T(where)}"
        assert x + 22 + width(T(role), "s", 17.5) < x + bw - 14, f"texto estoura o balão: {T(role)}"
    # no tema claro: balões claros, recorte branco atrás dos ícones
    write_themed("journey.svg",
                 d.svg(w, h, T(JOURNEY["hook"]) + " " + " → ".join(T(s[3]) for s in steps), "\n".join(parts), defs),
                 light_map={PAGE: "#ffffff", SURF_TOP: "#f6f8fa", SURF_BOT: "#ffffff",
                            VIOLET: "#8250df", ROSE: "#bf3989", GREEN: "#1a7f37",
                            mix(VIOLET): "#8250df", mix(ROSE): "#bf3989", mix(GREEN): "#1a7f37"})   # tons do Primer, legíveis no branco


# ── Formação, certificações e idiomas ──────────────────────────────────────
EDUCATION = [
    ("cap", BLUE, {"en": "Education", "pt": "Formação"}, [
        # (curso, instituição, período, badge de status)
        ({"en": "Software Engineering", "pt": "Engenharia de Software"}, "Instituto Infnet", "2023 — 2027",
         {"en": "in progress", "pt": "cursando"}),
        ({"en": "Architecture & Urbanism", "pt": "Arquitetura e Urbanismo"}, "UniSociesc", "2007 — 2012", ""),
    ]),
    ("award", AMBER, {"en": "Certifications", "pt": "Certificações"}, [
        ({"en": "Pentest & Ethical Hacking", "pt": "Pentest e Hacking Ético"}, "2026"),
        ("AWS Cloud Practitioner Essentials", "2024"),
        ({"en": "Cloud Computing Applications", "pt": "Aplicações de Cloud Computing"}, "2024"),
        ({"en": "Generative AI Fundamentals", "pt": "Introdução à IA Generativa"}, "2024"),
    ]),
    ("globe", CYAN, {"en": "Languages", "pt": "Idiomas"}, [
        # (bandeira, idioma, nível no badge, cor, observação)
        ("br", {"en": "Portuguese", "pt": "Português"}, {"en": "Native", "pt": "Nativo"}, GREEN, ""),
        ("gb", {"en": "English", "pt": "Inglês"}, "B2", BLUE, "C1"),
        ("jp", {"en": "Japanese", "pt": "Japonês"}, "JLPT N3", ROSE, ""),
    ]),
]


def build_education():
    d = Doc()
    w, h, gap = 960, 232, 16
    cw = (w - gap * 2) / 3
    parts = []
    for i, (icon, color, title, items) in enumerate(EDUCATION):
        x = i * (cw + gap)
        g = [panel(cw, h, 14, tint=color, strength=0.03, edge=0), tile(20, 20, 40, color, ICONS[icon]),
             d.t(74, 46.5, T(title), 17, TEXT, "s")]
        y = 98
        if icon == "cap":  # título + linha de apoio
            for course, inst, period, status in items:
                course = T(course)
                tx = 20
                if inst in INST_LOGOS:  # logo da instituição na frente do item
                    g.append(seal(20, y - 13, 30, inst))
                    tx = 62
                px = tx + width(inst, "r", 12.5) + 10
                g += [d.t(tx, y, course, 14.5, TEXT, "m"),
                      d.t(tx, y + 20, inst, 12.5, MUTED, "r"),
                      cal(px, y + 20, MUTED, 12),
                      d.t(px + 17, y + 20, period, 12.5, MUTED, "r")]
                assert px + 17 + width(period, "r", 12.5) < cw - 16, f"período estoura o cartão: {course}"
                extra = 0
                if status:  # badge verde ao lado do título; se não couber, numa linha própria
                    status = T(status)
                    sw = width(status, "m", 12) + 18
                    sx, sy = tx + width(course, "m", 14.5) + 8, y - 15
                    if sx + sw > cw - 16:
                        sx, sy, extra = tx, y + 29, 28
                    g += [f'<rect x="{sx + .5:.1f}" y="{sy}" width="{sw - 1:.1f}" height="21" rx="10.5" fill="{GREEN}" fill-opacity="0.12" stroke="{GREEN}" stroke-opacity="0.42"/>',
                          d.t(sx + sw / 2, sy + 14.6, status, 12, GREEN, "m", anchor="middle")]
                y += 54 + extra
                assert y - 32 < h - 16, f"formação não cabe no cartão ({LANG})"
        elif icon == "globe":  # idiomas: nível em badge
            for code, name, level, lc, note in items:
                level = T(level)
                bw = width(level, "m", 12) + 20
                bx = cw - 20 - bw
                g += [flag(20, y, code), d.t(46, y, T(name), 14, BODY, "r")]
                if note:  # meta: B2 → C1, o C1 em selo tracejado
                    note = T(note)
                    nw = width(note, "m", 12) + 20
                    nx = cw - 20 - nw
                    ax = nx - 8 - 12
                    g += [f'<rect x="{nx + .5:.1f}" y="{y - 16}" width="{nw - 1:.1f}" height="22" rx="11" fill="none" stroke="{lc}" stroke-opacity="0.6" stroke-dasharray="3 2.5"/>',
                          d.t(nx + nw / 2, y - .2, note, 12, lc, "m", anchor="middle"),
                          f'<path d="M{ax:.1f} {y - 4.5}h12m-3.6-3.6 3.6 3.6-3.6 3.6" fill="none" stroke="{BODY}" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>']
                    bx = ax - 8 - bw
                g += [f'<rect x="{bx + .5:.1f}" y="{y - 16}" width="{bw - 1:.1f}" height="22" rx="11" fill="{lc}" fill-opacity="0.12" stroke="{lc}" stroke-opacity="0.42"/>',
                      d.t(bx + bw / 2, y - .2, level, 12, lc, "m", anchor="middle")]
                assert 46 + width(T(name), "r", 14) + 12 < bx, "nível do idioma encosta no nome"
                y += 34
        else:  # lista com o ano à direita
            for name, year in items:
                name = T(name)
                g += [d.t(20, y, name, 13.5, BODY, "r"),
                      d.t(cw - 20, y, year, 12.5, MUTED, "mono", anchor="end")]
                assert 20 + width(name, "r", 13.5) < cw - 20 - width(year, "mono", 12.5) - 10, f"título encosta no ano: {name}"
                y += 30
        parts.append(f'<g transform="translate({x:.1f} 0)">{"".join(g)}</g>')
    write("education.svg", d.svg(w, h, " · ".join(T(e[2]) for e in EDUCATION), "\n".join(parts)))


# ── Detalhes: botão "todos os repositórios", legendas da toolbox e rodapé ──
CAPTIONS = {
    "languages": {"en": "LANGUAGES & FRAMEWORKS", "pt": "LINGUAGENS E FRAMEWORKS"},
    "messaging": {"en": "MESSAGING & DATA", "pt": "MENSAGERIA E DADOS"},
    "platform": {"en": "PLATFORM & OBSERVABILITY", "pt": "PLATAFORMA E OBSERVABILIDADE"},
}
ALL_REPOS = {"en": "VIEW ALL REPOSITORIES", "pt": "VER TODOS OS REPOSITÓRIOS"}
THANKS = {"en": "Thanks for stopping by", "pt": "Obrigado pela visita"}


def build_details():
    # botão para todos os repositórios: olho + texto, tom azul e um brilho passando
    d = Doc()
    label = T(ALL_REPOS)
    h = 44
    tw = width(label, "s", 12.5, 2.2)
    w = int(tw + 112)
    tx = 52                                   # texto começa depois do olho
    body = (f'<defs><linearGradient id="bf" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{BLUE}" stop-opacity="0.18"/>'
            f'<stop offset="1" stop-color="{VIOLET}" stop-opacity="0.10"/></linearGradient>'
            f'<linearGradient id="bs" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{BLUE}" stop-opacity="0.75"/>'
            f'<stop offset="1" stop-color="{VIOLET}" stop-opacity="0.55"/></linearGradient>'
            '<linearGradient id="sh" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
            '<stop offset="0.5" stop-color="#fff" stop-opacity="0.16"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
            f'<clipPath id="pill"><rect width="{w}" height="{h}" rx="{h / 2}"/></clipPath></defs>'
            f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="{h / 2}" fill="url(#surf)"/>'
            f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="{h / 2}" fill="url(#bf)" stroke="url(#bs)"/>'
            f'<g clip-path="url(#pill)"><rect x="-90" y="0" width="70" height="{h}" fill="url(#sh)" transform="skewX(-20)">'
            f'<animate attributeName="x" values="-90;{w + 40}" dur="3.2s" begin="1s" repeatCount="indefinite"/></rect></g>'
            f'<g transform="translate(22 13) scale(1.15)" fill="none" stroke="{BLUE}" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round">'
            '<path d="M1 8s2.6-4.8 7-4.8S15 8 15 8s-2.6 4.8-7 4.8S1 8 1 8Z"/><circle cx="8" cy="8" r="2.2"/></g>'
            + d.t(tx, 27.5, label, 12.5, TEXT, "s", ls=2.2) + arrow(w - 38, 15, BLUE))
    write("all-repos.svg", d.svg(w, h, label.capitalize(), body))

    # legendas da toolbox
    for key, label in CAPTIONS.items():
        d = Doc()
        w, h = 620, 22
        line = d.t(w / 2, 16, T(label), 12, LABEL, "s", ls=2.4, anchor="middle")
        write_themed(f"caption-{key}.svg", d.svg(w, h, T(label).capitalize(), line))

    # rodapé
    d = Doc()
    w, h = 960, 114
    body = (f'<defs><linearGradient id="fl" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{BORDER}" stop-opacity="0"/>'
            f'<stop offset="0.5" stop-color="{CHIP_BORDER}"/><stop offset="1" stop-color="{BORDER}" stop-opacity="0"/></linearGradient></defs>'
            f'<rect x="0" y="12" width="{w}" height="1" fill="url(#fl)"/>'
            '<!--light-only-->'
            f'<svg x="{w / 2 - 34}" y="22" width="68" height="68" viewBox="0 0 96 96" overflow="visible">{bkr_glyph()}</svg>'
            + d.t(w / 2, 102, T(THANKS), 15, BODY, "r", anchor="middle"))
    # no tema claro o símbolo (prateado) ganha um ladrilho escuro para ter contraste
    tile_light = f'<rect x="{w / 2 - 38}" y="28" width="76" height="56" rx="16" fill="{SURF_TOP}"/>'
    write_themed("footer.svg", d.svg(w, h, T(THANKS), body), tile_light)


# ── Toolbox: linha de mensageria (ícones skill-icons, MIT), igual nos dois idiomas
# O Kafka do skill-icons só existe em tile claro; aqui ele ganha o tile escuro padrão.
STACK_ROWS = {"messaging": ["kafka", "rabbitmq", "postgres", "mongodb", "redis", "elasticsearch"]}


def icon_inner(name):
    s = (ROOT / "icons" / f"{name}.svg").read_text(encoding="utf-8")
    inner = re.search(r'translate\(0, 0\)">\s*<svg[^>]*>(.*)</svg>\s*</g>', s, re.S).group(1)
    if name == "kafka":
        inner = inner.replace('fill="#A9CBD4"', 'fill="#242938"').replace('fill="black"', 'fill="#fff"')
    return re.sub(r'(id="|url\(#)', rf"\g<1>{name}-", inner)  # ids únicos por ícone


def build_stack():
    for row, names in STACK_ROWS.items():
        w = len(names) * 300 - 44  # mesma geometria do skillicons.dev
        icons = "".join(f'<svg x="{i * 300}" width="256" height="256" viewBox="0 0 256 256">{icon_inner(n)}</svg>'
                        for i, n in enumerate(names))
        write(f"stack-{row}.svg", f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="256" viewBox="0 0 {w} 256" '
                                  f'role="img" aria-label="{", ".join(names)}">{icons}</svg>\n', shared=True)


# ── README (um por idioma, mesma estrutura) ────────────────────────────────
TOOLBOX = [
    ("https://skillicons.dev/icons?i=java,spring,maven,py,sklearn,ts,nextjs&theme=dark",
     "Java, Spring, Maven, Python, scikit-learn, TypeScript, Next.js", "languages"),
    ("assets/stack-messaging.svg", "Kafka, RabbitMQ, PostgreSQL, MongoDB, Redis, Elasticsearch", "messaging"),
    ("https://skillicons.dev/icons?i=docker,kubernetes,githubactions,prometheus,grafana,aws,azure,cloudflare&theme=dark",
     "Docker, Kubernetes, GitHub Actions, Prometheus, Grafana, AWS, Azure, Cloudflare", "platform"),
]


def build_readme():
    a = f"assets/{LANG}"

    def img(name, alt, size='width="100%"'):
        alt = escape(alt, {'"': "&quot;"})
        return f'<img src="{a}/{name}" {size} alt="{alt}">'

    def themed(name, alt, attr='width="100%"'):
        alt = escape(alt, {'"': "&quot;"})
        return (f'<picture><source media="(prefers-color-scheme: light)" srcset="{a}/{name}-light.svg">'
                f'<img src="{a}/{name}.svg" {attr} alt="{alt}"></picture>')

    def project_link(p):
        alt = f'{T(p["title"])}: {T(p["desc"])}'
        return f'<a href="{p["url"]}">{img("project-" + p["slug"] + ".svg", alt)}</a>'

    def block(*lines):
        return '<p align="center">\n' + "\n".join(f"  {ln}" for ln in lines) + "\n</p>\n"

    section = dict(SECTIONS)
    other = ("Português", PT_README) if LANG == "en" else ("English", PROFILE)
    # faixa do topo: my-links + Agora, sem espaço entre as imagens; larguras proporcionais
    # ao viewBox de cada uma (somam 100%), então as duas ficam com a mesma altura
    nw, mw, _ = TOPBAR
    pm, pn = f"{mw / (nw + mw) * 100:.3f}%", f"{nw / (nw + mw) * 100:.3f}%"
    pl = f"{(mw - TOPGAP) / (nw + mw) * 100:.3f}%"   # idioma com a mesma largura visível do my-links
    now_alt = f'{T(NOW["label"]).title()}: {T(NOW["headline"])} · {NOW["stack"]}'
    topbar = (img("now.svg", now_alt, f'width="{pn}"')
              + f'<a href="https://andrebecker84.github.io/my-links/"><img src="{a}/my-links.svg" width="{pm}" alt="my-links"></a>')
    out = [f"<!-- Gerado por scripts/build_assets.py — edite os textos lá e rode: python scripts/build_assets.py -->\n",
           f'<p align="right">\n  <a href="{other[1]}"><img src="{a}/lang.svg" width="{pl}" alt="{other[0]}"></a>\n</p>\n',
           f'<p align="center">\n  {topbar}\n</p>\n',
           block(img("hero.svg", f'{HERO["name"]} · {T(HERO["kicker"]).title()} · {T(HERO["tagline"])}')),
           block(themed("section-about", T(section["about"]).title())),
           block(img("about.svg", T(ABOUT["text"]))),
           block(themed("section-journey", T(section["journey"]).title())),
           block(themed("journey", T(JOURNEY["hook"]))),
           block(themed("section-focus", T(section["focus"]).title())),
           block(img("focus.svg", " · ".join(T(p[2]) for p in PILLARS))),
           block(themed("section-work", T(section["work"]).title())),
           block(*[project_link(p) for p in PROJECTS]),
           block(f'<a href="{PROFILE}?tab=repositories">{img("all-repos.svg", T(ALL_REPOS).capitalize(), 'height="40"')}</a>'),
           block(themed("section-education", T(section["education"]).title())),
           block(img("education.svg", " · ".join(T(e[2]) for e in EDUCATION))),
           block(themed("section-toolbox", T(section["toolbox"]).title()))]
    for src, alt, cap in TOOLBOX:
        out.append(block(f'<img src="{src}" height="44" alt="{alt}"><br>',
                         themed(f"caption-{cap}", T(CAPTIONS[cap]).capitalize(), 'height="20"')))
    out.append(block(themed("section-connect", T(section["connect"]).title())))
    out.append(block(*[f'<a href="{url}">{img("link-" + icon + ".svg", T(label), 'width="32%"')}</a>' for icon, _, label, _, url in LINKS]))
    out.append(block(themed("footer", T(THANKS))))
    name = "README.md" if LANG == "en" else "README.pt-BR.md"
    (REPO / name).write_text("\n".join(out), encoding="utf-8")
    print(f"  ok {name}")


if __name__ == "__main__":
    build_stack()
    for LANG in ("en", "pt"):
        OUT = ASSETS / LANG
        print(f"── {LANG}")
        build_lang_toggle()
        build_mylinks_pill()
        build_hero()
        build_sections()
        build_about()
        build_now()
        build_pillars()
        build_projects()
        build_links()
        build_journey()
        build_education()
        build_details()
        build_readme()
