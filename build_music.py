#!/usr/bin/env python3
"""Rebuild the release grid, playlist embed and lyrics data in music.html from releases.json.
Usage: python3 build_music.py   (run from the site folder, then commit + push)"""
import json, os, re, sys, html
from urllib.parse import quote
sys.dont_write_bytecode = True   # keep __pycache__ out of the site folder
from build_popups import BLOCK as POPUPS_BLOCK

data = json.load(open('releases.json', encoding='utf-8'))
rels = data['releases'][::-1] if data.get('newest_first') else data['releases']
pl = data['playlist']

cards = []
for r in rels:
    t = html.escape(r['title'])
    subj = quote('Licensing Inquiry: ' + r['title'], safe='')
    cards.append(f'''                <div class="volume-card" style="cursor: default;">
                    <img src="{r['cover']}" alt="{t}" class="volume-artwork">
                    <div class="volume-info">
                        <h3 class="volume-title">{t}</h3>
                        <p class="volume-subtitle">{html.escape(r.get('type','Single'))}</p>
                        <button class="volume-btn lyrics-btn" data-track="{r['id']}" style="width: 100%; cursor: pointer; font-family: inherit; margin-bottom: 0.75rem;">View Lyrics</button>
                        <a class="volume-btn" href="/licensing">Explore Licensing</a>
                    </div>
                </div>''')

player_html = f'''                <iframe width="100%" height="{pl['height']}" scrolling="no" frameborder="no" allow="autoplay; encrypted-media" title="SUNOLICIOUS on SoundCloud" src="{pl['embed_src']}"></iframe>
                <div style="font-size: 10px; color: #cccccc; line-break: anywhere; word-break: normal; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; font-family: Interstate, Lucida Grande, Lucida Sans Unicode, Lucida Sans, Garuda, Verdana, Tahoma, sans-serif; font-weight: 100; text-align: left;"><a href="{pl['credit_profile']}" title="SUNOLICIOUS™" target="_blank" rel="noopener" style="color: #cccccc; text-decoration: none;">SUNOLICIOUS™</a> · <a href="{pl['credit_set']}" title="{html.escape(pl['credit_set_name'])}" target="_blank" rel="noopener" style="color: #cccccc; text-decoration: none;">{html.escape(pl['credit_set_name'])}</a></div>'''

grid = '<div class="volumes-grid">\n' + '\n'.join(cards) + '\n            </div>\n            <div style="max-width: 900px; margin: 0 auto 3rem;">\n' + player_html + '\n            </div>\n            '

lyrics = {r['id']: {'title': r['title'], 'lyrics': r['lyrics']} for r in data['releases']}
lj = json.dumps(lyrics, ensure_ascii=False, indent=2).replace('</', '<\\/')

s = open('music.html', encoding='utf-8').read()
s, n1 = re.subn(r'(<!-- RELEASES:START -->).*?(<!-- RELEASES:END -->)',
                lambda m: m.group(1) + '\n            ' + grid + m.group(2), s, flags=re.S)
s, n2 = re.subn(r'/\*LYRICS_START\*/.*?/\*LYRICS_END\*/',
                lambda m: '/*LYRICS_START*/' + lj + '/*LYRICS_END*/', s, flags=re.S)
assert n1 == 1 and n2 == 1, (n1, n2)
open('music.html', 'w', encoding='utf-8').write(s)

def song_slug(r):
    """URL slug for a song's licensing page: pitch.slug if set, else derived from the title."""
    return (r.get('pitch') or {}).get('slug') or re.sub(r'[^a-z0-9]+', '-', r['title'].lower()).strip('-')

# licensing page grid: same cards as Music, one License button each, player underneath
lic = []
for r in rels:
    t = html.escape(r['title'])
    subj = quote('Licensing Inquiry: ' + r['title'], safe='')
    lic.append(f'''                <div class="volume-card">
                    <img src="{r['cover']}" alt="{t}" class="volume-artwork">
                    <div class="volume-info">
                        <h3 class="volume-title">{t}</h3>
                        <p class="volume-subtitle">{html.escape(r.get('type','Single'))}</p>
                        <a class="volume-btn" href="licensing/{song_slug(r)}.html">Explore This Track</a>
                    </div>
                </div>''')
lgrid = '<div class="volumes-grid">\n' + '\n'.join(lic) + '\n            </div>\n            <div style="max-width: 900px; margin: 0 auto 3rem;">\n' + player_html + '\n            </div>'
L = open('licensing.html', encoding='utf-8').read()
L, n3 = re.subn(r'(<!-- LICENSING-GRID:START -->).*?(<!-- LICENSING-GRID:END -->)',
                lambda m: m.group(1) + '\n            ' + lgrid + '\n            ' + m.group(2), L, flags=re.S)
assert n3 == 1
open('licensing.html', 'w', encoding='utf-8').write(L)

# ---- song licensing pages: licensing/<slug>.html for EVERY release (basic), plus sync concepts when it has a "pitch" block ----
# Menu, footer, signup pop-up, CSS and script are lifted from licensing.html so these pages always match it.
# Template: pitch_template.html. To add a song, give its releases.json entry a "pitch" block and re-run this script.
def _nested(h):
    """pages live one folder down: root-relative links and assets need ../"""
    return re.sub(r'(href|src)="(?!https?:|mailto:|#|\.\./|/)([^"]+)"', r'\1="../\2"', h)

def _grab(pattern, text, what):
    m = re.search(pattern, text, re.S)
    assert m, 'licensing.html: could not find ' + what
    return m.group(0)

shared = {
    'SHARED_CSS': re.search(r'<style>(.*?)</style>', L, re.S).group(1),
    'MENU': _nested(_grab(r'<!-- Hamburger Menu -->.*?</nav>', L, 'menu')),
    'SIGNUP': _nested(_grab(r'<!-- EMAIL POPUP BUTTON -->.*?(?=\s*<!-- BIO MODAL -->)', L, 'signup pop-up')),
    'FOOTER': _nested(_grab(r'<footer>.*?</footer>', L, 'footer')),
    'SCRIPT': _grab(r'<script>\s*// Hamburger menu toggle.*?</script>', L, 'page script'),
    'NEWSLETTER': _nested(_grab(r'<script src="newsletter\.js[^"]*"[^>]*></script>', L, 'newsletter script')),
    'POPUPS': POPUPS_BLOCK,
}
tpl = open('pitch_template.html', encoding='utf-8').read()

def build_pitch(r):
    p = r.get('pitch'); slug = song_slug(r); esc = html.escape
    assert re.fullmatch(r'[a-z0-9-]+', slug), slug
    t = r['title']
    sc = r['soundcloud']
    src = ('https://w.soundcloud.com/player/?url=' + quote(sc, safe='/') +
           '&color=%23c5b7a0&auto_play=false&hide_related=true&show_comments=false&show_user=false&show_reposts=false&show_teaser=false&visual=false')
    player = (f'            <iframe width="100%" height="166" scrolling="no" frameborder="no" allow="autoplay; encrypted-media" title="{esc(t)} on SoundCloud" src="{src}"></iframe>\n'
              f'            <div class="pitch-credit"><a href="{data["soundcloud_profile"]}" target="_blank" rel="noopener">SUNOLICIOUS™</a> · <a href="{sc}" target="_blank" rel="noopener">{esc(t)}</a></div>')
    lyr = '\n'.join('                <p>' + esc(st).replace('\n', '<br>') + '</p>' for st in r['lyrics'].strip().split('\n\n'))
    # facts: only what is verified. Add more via "facts": [["Duration","3:12"], ...] in the pitch block.
    rows = [('Artist', 'SUNOLICIOUS™'), ('Track', t.upper()), ('Release', r.get('type', 'Single'))] + [tuple(x) for x in (p or {}).get('facts', [])]
    facts = '\n'.join(f'                <dt>{esc(k)}</dt><dd>{esc(v)}</dd>' for k, v in rows)
    facts += '\n                <dt>Licensing</dt><dd><a href="mailto:info@sunolicious.com">info@sunolicious.com</a></dd>'
    mailto = 'mailto:info@sunolicious.com?subject=' + quote('Licensing Inquiry: ' + t, safe='')
    out = tpl
    if p:   # enhanced song: sync concepts, lede and lyrical theme
        fc = p['featured_concept']
        tiles = '\n'.join(f'                <div class="tile"><h3>{esc(c["title"])}</h3><p>{esc(c["text"])}</p></div>' for c in p['additional_concepts'])
        desc = p['page_description']
        lede = f'                <p class="pitch-lede">{esc(p["short_pitch"])}</p>\n'
        secondary = '                    <a class="version-btn" href="#in-context">See it in action</a>\n'
        theme_p = f'            <p class="pitch-theme">{esc(p["lyrical_theme"])}</p>'
        heading = 'Lyrical theme'
        concept = dict(CONCEPT_TITLE=esc(fc['title']), CONCEPT_STATUS=esc(fc['status']), CONCEPT_DISCLAIMER=esc(fc['disclaimer']),
                       CONCEPT_DESC=esc(fc['description']), TILES=tiles)
    else:   # basic song: verified data only, no concepts
        out = re.sub(r'<!--PITCH-ONLY:START-->.*?<!--PITCH-ONLY:END-->\n', '', out, flags=re.S)
        desc = f'{t} by SUNOLICIOUS™. Listen, read the lyrics and inquire about sync licensing.'
        lede = secondary = theme_p = ''
        heading = 'Lyrics'
        concept = {}
    out = out.replace('<!--PITCH-ONLY:START-->\n', '').replace('<!--PITCH-ONLY:END-->\n', '')
    vals = dict(shared, **concept, LEDE=lede, HERO_SECONDARY=secondary, THEME_P=theme_p, LYRICS_HEADING=heading,
                TITLE=esc(f'{t} | Sync Licensing | SUNOLICIOUS™'), DESC=esc(desc), SLUG=slug,
                COVER=r['cover'], COVER_ALT=esc(f'{t} cover art'), SONG_TITLE_UPPER=esc(t.upper()),
                PLAYER=player, LYRICS=lyr, FACTS=facts, MAILTO=mailto)
    for k, v in vals.items():
        out = out.replace('{{' + k + '}}', v)
    assert '{{' not in out, re.findall(r'\{\{\w+\}\}', out)
    os.makedirs('licensing', exist_ok=True)
    open(f'licensing/{slug}.html', 'w', encoding='utf-8').write(out)
    return slug

built = [build_pitch(r) for r in data['releases']]
print(f'music.html + licensing.html rebuilt: {len(rels)} releases; song pages: {built}')
