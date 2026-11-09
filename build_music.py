#!/usr/bin/env python3
"""Rebuild the release grid, playlist embed and lyrics data in music.html from releases.json.
Usage: python3 build_music.py   (run from the site folder, then commit + push)"""
import glob, json, os, re, sys, html
from urllib.parse import quote
sys.dont_write_bytecode = True   # keep __pycache__ out of the site folder
import build_popups
from build_popups import BLOCK as POPUPS_BLOCK, SIGNUP_BLOCK

data = json.load(open('releases.json', encoding='utf-8'))
rels = data['releases'][::-1] if data.get('newest_first') else data['releases']
pl = data['playlist']

def song_slug(r):
    """URL slug for a song's licensing page: the release's own "slug" if set, else pitch.slug, else derived from the title.
    (The Release Manager freezes the slug on save so a later title edit never changes a live URL.)"""
    return r.get('slug') or (r.get('pitch') or {}).get('slug') or re.sub(r'[^a-z0-9]+', '-', r['title'].lower()).strip('-')


def concept_shown(fc):
    """Concept section is public only when a concept exists and featured_concept.show is not false (old records have no 'show' = visible)."""
    return bool(fc) and fc.get('show', True) is not False


def enhanced(r):
    """a release gets sync-concept content only if it has a pitch block that is not switched off ("enabled": false)"""
    p = r.get('pitch')
    return p if p and p.get('enabled', True) is not False else None


def video_embed(url):
    """(kind, src) for a concept-video URL: YouTube / Vimeo embed, or a direct .mp4/.webm/.mov file. Anything else is rejected."""
    u = (url or '').strip()
    m = re.match(r'https://(?:www\.|m\.)?(?:youtube\.com/(?:watch\?(?:[^#]*&)?v=|embed/|shorts/)|youtu\.be/)([A-Za-z0-9_-]{11})', u)
    if m:
        return 'iframe', 'https://www.youtube-nocookie.com/embed/' + m.group(1) + '?autoplay=1&rel=0'
    m = re.match(r'https://(?:www\.)?vimeo\.com/(?:video/)?(\d+)', u)
    if m:
        return 'iframe', 'https://player.vimeo.com/video/' + m.group(1) + '?autoplay=1'
    if re.match(r'https://[^\s"<>]+\.(?:mp4|webm|mov)(?:\?[^\s"<>]*)?$', u, re.I):
        return 'file', u
    raise ValueError('concept video URL must be a YouTube, Vimeo or direct .mp4/.webm link: ' + u)


def validate_release(r, seen):
    """fail the build with a clear message instead of publishing a broken page"""
    errs = []
    for k in ('id', 'title', 'cover', 'soundcloud', 'lyrics'):
        if not str(r.get(k, '')).strip():
            errs.append(f'missing "{k}"')
    slug = song_slug(r)
    if not re.fullmatch(r'[a-z0-9-]+', slug):
        errs.append(f'bad slug "{slug}" (letters, numbers, hyphens)')
    if slug in seen:
        errs.append(f'slug "{slug}" is also used by "{seen[slug]}"')
    seen[slug] = r.get('title', '?')
    p = enhanced(r)
    if p:
        fc = p.get('featured_concept') or {}
        for k, v in list(p.items()) + list(fc.items()):
            if isinstance(v, str) and '{{' in v:
                errs.append(f'"{k}" contains "{{{{" (not allowed)')
        if not concept_shown(fc): fc = {}      # hidden concept: content is kept, not validated or rendered
        if fc.get('video_url'):
            try: video_embed(fc['video_url'])
            except ValueError as e: errs.append(str(e))
        if fc.get('poster') and not os.path.isfile(fc['poster']):
            errs.append(f'concept poster file not found: {fc["poster"]}')
        for c in p.get('additional_concepts', []):
            if not str(c.get('title', '')).strip() or not str(c.get('text', '')).strip():
                errs.append('a placement needs both a title and a description')
    if errs:
        sys.exit(f'BUILD STOPPED. "{r.get("title", "?")}" ({r.get("id", "?")}): ' + '; '.join(errs))


_seen = {}
for _r in data['releases']:
    validate_release(_r, _seen)      # stop before writing anything if a release is incomplete or a slug collides


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
    'SIGNUP': SIGNUP_BLOCK,                       # shared Join the List component (build_popups.py)
    'FOOTER': _nested(_grab(r'<footer>.*?</footer>', L, 'footer')),
    'SCRIPT': _grab(r'<script>\s*// Hamburger menu toggle.*?</script>', L, 'page script'),
    'NEWSLETTER': '<script src="../newsletter.js" data-cfasync="false" defer></script>',   # version added by build_popups
    'POPUPS': POPUPS_BLOCK,
}
tpl = open('pitch_template.html', encoding='utf-8').read()

def build_pitch(r):
    p = enhanced(r); slug = song_slug(r); esc = html.escape
    assert re.fullmatch(r'[a-z0-9-]+', slug), slug
    t = r['title']
    sc = r['soundcloud']
    src = ('https://w.soundcloud.com/player/?url=' + quote(sc, safe='/') +
           '&color=%23c5b7a0&auto_play=false&hide_related=true&show_comments=false&show_user=false&show_reposts=false&show_teaser=false&visual=false')
    player = (f'            <iframe width="100%" height="166" scrolling="no" frameborder="no" allow="autoplay; encrypted-media" title="{esc(t)} on SoundCloud" src="{src}"></iframe>\n'
              f'            <div class="pitch-credit"><a href="{data["soundcloud_profile"]}" target="_blank" rel="noopener">SUNOLICIOUS™</a> · <a href="{sc}" target="_blank" rel="noopener">{esc(t)}</a></div>')
    lyr = '\n'.join('                <p>' + esc(st).replace('\n', '<br>') + '</p>' for st in r['lyrics'].strip().split('\n\n'))
    # facts: only what is verified. Add more via "facts": [["Duration","3:12"], ...] in the pitch block.
    rows = [('Artist', 'SUNOLICIOUS™'), ('Track', t.upper()), ('Release', r.get('type', 'Single'))] + [tuple(x) for x in (r.get('pitch') or {}).get('facts', [])]
    facts = '\n'.join(f'                <dt>{esc(k)}</dt><dd>{esc(v)}</dd>' for k, v in rows)
    facts += '\n                <dt>Licensing</dt><dd><a href="mailto:info@sunolicious.com">info@sunolicious.com</a></dd>'
    mailto = 'mailto:info@sunolicious.com?subject=' + quote('Licensing Inquiry: ' + t, safe='')
    out = tpl
    video_js = ''
    if p:   # enhanced song: every piece below is optional and only shown when it has content
        fc = p.get('featured_concept') or {}
        if not concept_shown(fc): fc = {}      # "Show Sync Concept Section" off: no section, no hero button, no player; saved fields stay in releases.json
        esc_ = esc
        concepts = p.get('additional_concepts') or []
        tiles = '\n'.join(f'                <div class="tile"><h3>{esc(c["title"])}</h3><p>{esc(c["text"])}</p></div>' for c in concepts)
        desc = p.get('page_description') or f'{t} by SUNOLICIOUS™. Listen, read the lyrics and inquire about sync licensing.'
        lede = f'                <p class="pitch-lede">{esc(p["short_pitch"])}</p>\n' if p.get('short_pitch') else ''
        secondary = '                    <a class="version-btn" href="#in-context">See it in action</a>\n' if fc else ''
        theme_p = '\n'.join(f'            <p class="pitch-theme">{esc(x)}</p>' for x in p['lyrical_theme'].split('\n') if x.strip()) if p.get('lyrical_theme') else ''
        heading = 'Lyrical theme' if theme_p else 'Lyrics'
        poster = fc.get('poster')
        video_btn = ''
        if fc.get('video_url'):
            kind, vsrc = video_embed(fc['video_url'])
            video_btn = f'                        <button type="button" class="poster-play" data-kind="{kind}" data-src="{esc(vsrc)}">Play concept reel</button>\n'
            video_js = ("    <script>\n    (function () {\n        var b = document.querySelector('.poster-play'); if (!b) return;\n"
                        "        b.addEventListener('click', function () {\n            var box = b.closest('.concept-poster'), el;\n"
                        "            if (b.dataset.kind === 'file') { el = document.createElement('video'); el.controls = true; el.autoplay = true; el.playsInline = true; el.src = b.dataset.src; }\n"
                        "            else { el = document.createElement('iframe'); el.src = b.dataset.src; el.allow = 'autoplay; encrypted-media; picture-in-picture; fullscreen'; el.allowFullscreen = true; el.title = 'Concept reel'; }\n"
                        "            box.classList.add('playing'); box.appendChild(el);\n        });\n    })();\n    </script>\n")
        concept = dict(CONCEPT_TITLE=esc(fc.get('title', '')), CONCEPT_STATUS=esc(fc.get('status', '')), CONCEPT_DISCLAIMER=esc(fc.get('disclaimer', '')),
                       CONCEPT_DESC=esc(fc.get('description', '')), TILES=tiles, VIDEO_BTN=video_btn,
                       POSTER_CLASS='concept-poster' + (' has-poster' if poster else ''), POSTER_SRC=poster or r['cover'])
        if not fc:
            out = re.sub(r'<!--CONTEXT:START-->.*?<!--CONTEXT:END-->\n', '', out, flags=re.S)
        if not concepts:
            out = re.sub(r'<!--TILES:START-->.*?<!--TILES:END-->\n', '', out, flags=re.S)
    else:   # basic song: verified data only, no concepts
        out = re.sub(r'<!--CONTEXT:START-->.*?<!--CONTEXT:END-->\n', '', out, flags=re.S)
        out = re.sub(r'<!--TILES:START-->.*?<!--TILES:END-->\n', '', out, flags=re.S)
        desc = f'{t} by SUNOLICIOUS™. Listen, read the lyrics and inquire about sync licensing.'
        lede = secondary = theme_p = ''
        heading = 'Lyrics'
        concept = {}
    for mk in ('CONTEXT', 'TILES'):
        out = out.replace(f'<!--{mk}:START-->\n', '').replace(f'<!--{mk}:END-->\n', '')
    vals = dict(shared, **concept, LEDE=lede, HERO_SECONDARY=secondary, THEME_P=theme_p, LYRICS_HEADING=heading, VIDEO_JS=video_js,
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
# a removed release must not leave its generated page live: delete licensing/*.html that this script generated but no release owns
for _f in sorted(glob.glob('licensing/*.html')):
    if os.path.basename(_f)[:-5] not in built and 'GENERATED by build_music.py' in open(_f, encoding='utf-8').read(400):
        os.remove(_f); print('removed orphan page', _f)
print(f'music.html + licensing.html rebuilt: {len(rels)} releases; song pages: {built}')

# ---- shared components on EVERY page (Join the List, Bio / Ethics pop-ups, cache-busted assets) ----
build_popups.run_all()
