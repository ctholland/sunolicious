#!/usr/bin/env python3
"""Shared site components, stamped onto every page: Artist Bio + AI Ethics pop-ups AND the Join the List sign-up.

Edit the copy in BIO / ETHICS / SIGNUP below, then run:  python3 build_music.py   (or python3 build_popups.py on its own)
  * Pop-up markup lives between <!-- POPUPS:START --> and <!-- POPUPS:END --> on each page.
  * Sign-up markup lives between <!-- SIGNUP:START --> and <!-- SIGNUP:END --> on each page.
  * Styling lives in popups.css, behaviour in newsletter.js (both linked from every page; cache-bust versions are added here).
Any new page (blog post, song page, ...) only needs to contain a POPUPS block; the sign-up, stylesheet and script are added on the next build.
"""
import glob, hashlib, html as _html, os, re, sys

# ---- Join the List: ONE place for the form, wording and Mailchimp settings ----
SIGNUP = {
    # Mailchimp audience "Sunolicious Music" (list id c2b49f4fa3). Copy from Mailchimp > Audience > Signup forms > Embedded forms.
    'action': 'https://noahmusic.us6.list-manage.com/subscribe/post?u=634485f7f15097e5aecc9af5f&id=c2b49f4fa3&f_id=004911e2f0',
    'honeypot': 'b_634485f7f15097e5aecc9af5f_c2b49f4fa3',   # Mailchimp's bot trap field; leave as is
    # Subscriber tag. PENDING: paste the numeric tag ID of the "sunolicious" tag here (Mailchimp embedded-form code:
    # <input type="hidden" name="tags" value="NNNN">). Empty = no tag is sent.
    'tag_id': '4059298',
    'button': 'Join the List',
    'heading': 'SUNOLICIOUS',
    'tagline': 'Human. Machine. Manifest.',
    'description': 'Join the journey. Get exclusive updates, new releases, and insights into the evolution of human-machine musical collaboration.',
    'email_label': 'Email Address *',
    'email_placeholder': 'your@email.com',
    'submit': 'Subscribe',
}

BIO = [
    ("p", "I came up in music before everything went fully digital."),
    ("p", "I learned recording in analog studios where tape was finite, decisions mattered, and commitment was part of the craft. I worked across multiple eras and cities — Chicago, London, New York — from early multitrack recording and sampling systems through large-format tape and into the digital age that rewrote the industry entirely."),
    ("p", "I'm Christofer Holland, a/k/a NOAH®, with more than twenty UK Music Week chart placements as well as Billboard and DJ Times chart entries. My work has crossed underground club culture and commercial dance music, giving me a perspective shaped by both the creative and business sides of the industry."),
    ("p", "I didn't arrive at AI as a shortcut. I arrived at it through decades of adapting to changing tools while protecting authorship."),
    ("quote", "Throughout my career, musicians have always modeled other musicians — singers studying phrasing, drummers internalizing feel, guitarists chasing tone. That's not new. What's new is that modeling has become explicit."),
    ("p", "Today, I use AI as part of a creative feedback loop — prompting, responding, refining, selecting, reshaping, and taking responsibility for the final work. Platforms may introduce variation and randomness, but the core decisions — melody, lyrics, emotional direction, arrangement, identity, and what ultimately gets released — remain human."),
    ("p", "Any vocals that aren't my physical voice are still extensions of my musical identity: my melodies, my words, my intent, my taste."),
    ("sign", "The tools evolve.<br>The authorship doesn't."),
]

ETHICS = [
    ("lead", "SUNOLICIOUS™ is where human artistry meets technological possibility."),
    ("p", "My music is shaped by my melodies, lyrics, creative direction, and musical judgment."),
    ("p", "AI doesn't replace my artistry — it extends it. It's a tool, not a ghostwriter; an instrument, not a replacement for the artist."),
    ("p", "I develop the concepts. I write and shape the songs. I define the sonic identity. I work through an iterative creative feedback loop — prompting, responding, refining, editing, and making the final decisions about what gets released."),
    ("p", "AI enters the process as part of a long tradition of musical technology — synthesizers, samplers, drum machines, pitch correction, and amplifier modeling — expanding what an artist can create and how that vision can be expressed."),
    ("p", "Every SUNOLICIOUS™ release is developed, curated, and produced under my creative direction. Vocal models, generated textures, and other AI-assisted elements serve the composition, not the other way around."),
    ("lead", "The technology contributes possibilities. The artist determines the work."),
    ("sign", "Human first.<br>Machine second.<br>The creative vision is mine."),
    ("byline", "C.T. Holland | NOAH®"),
]

CLS = {"p": "", "lead": "pp-lead", "quote": "pp-quote", "sign": "pp-sign", "byline": "pp-byline"}


def body(items):
    out = []
    for kind, text in items:
        c = CLS[kind]
        out.append('                <p%s>%s</p>' % (' class="%s"' % c if c else '', text))
    return "\n".join(out)


def overlay(oid, close_id, title, items):
    return f'''    <div class="pp-overlay" id="{oid}">
        <div class="pp-panel">
            <button class="pp-close" id="{close_id}" aria-label="Close">&times;</button>
            <div class="pp-head">
                <div class="pp-wordmark">SUNOLICIOUS<sup>™</sup></div>
                <div class="pp-tag">Human. Machine. Manifest.</div>
                <h2 class="pp-title">{title}</h2>
            </div>
            <div class="pp-body pp-scroll">
{body(items)}
            </div>
        </div>
    </div>'''


BLOCK = ("<!-- POPUPS:START (generated by build_popups.py) -->\n"
         + overlay("bioOverlay", "closeBio", "Artist Bio", BIO) + "\n"
         + overlay("aiEthicsOverlay", "closeAiEthics", "AI Ethics &amp; Creative Statement", ETHICS) + "\n"
         + "    <!-- POPUPS:END -->")

def signup_block():
    c = SIGNUP
    e = _html.escape
    tag = ('\n                <input type="hidden" name="tags" value="%s">' % e(str(c['tag_id']), quote=True)) if str(c['tag_id']).strip() else ''
    return f'''<!-- SIGNUP:START (generated by build_popups.py) -->
    <button class="signup-trigger" id="openPopup">{e(c['button'])}</button>
    <div class="popup-overlay" id="popupOverlay">
        <div class="popup-content">
            <button class="close-btn" id="closePopup" aria-label="Close">&times;</button>
            <div class="popup-header">
                <h1>{e(c['heading'])}<sup style="font-size: 0.3em">™</sup></h1>
                <p>{e(c['tagline'])}</p>
            </div>
            <p class="popup-description">
                {e(c['description'])}
            </p>
            <form class="popup-form" action="{e(c['action'], quote=True)}" method="post" id="mc-embedded-subscribe-form" name="mc-embedded-subscribe-form" target="_blank">
                <div class="form-group">
                    <label for="mce-EMAIL">{e(c['email_label'])}</label>
                    <input type="email" name="EMAIL" id="mce-EMAIL" required placeholder="{e(c['email_placeholder'], quote=True)}">
                </div>{tag}
                <div class="hidden-field" aria-hidden="true">
                    <input type="text" name="{e(c['honeypot'], quote=True)}" tabindex="-1" value="">
                </div>
                <button type="submit" class="submit-btn">{e(c['submit'])}</button>
            </form>
        </div>
    </div>
    <!-- SIGNUP:END -->'''


SIGNUP_BLOCK = signup_block()


def asset_version(path):
    """short content hash: changes only when the file changes, so browsers/Cloudflare refetch exactly when needed"""
    return hashlib.md5(open(path, 'rb').read()).hexdigest()[:8]


# blog index has no pop-up code of its own: small self-contained wiring
BLOG_INDEX_JS = '''
    <script>
    (function () {
        var bio = document.getElementById('bioOverlay'), ai = document.getElementById('aiEthicsOverlay');
        function show(el, e) { if (e) e.preventDefault(); el.classList.add('active'); var m = document.getElementById('menuOverlay'); if (m) m.classList.remove('active'); }
        document.querySelectorAll('.bio-trigger').forEach(function (a) { a.addEventListener('click', function (e) { show(bio, e); }); });
        document.querySelectorAll('.ai-trigger').forEach(function (a) { a.addEventListener('click', function (e) { show(ai, e); }); });
        [[bio, 'closeBio'], [ai, 'closeAiEthics']].forEach(function (p) {
            document.getElementById(p[1]).addEventListener('click', function () { p[0].classList.remove('active'); });
            p[0].addEventListener('click', function (e) { if (e.target === p[0]) p[0].classList.remove('active'); });
        });
        document.addEventListener('keydown', function (e) { if (e.key === 'Escape') { bio.classList.remove('active'); ai.classList.remove('active'); } });
    })();
    </script>
'''


def balanced_end(s, start):
    """index just past the </div> that closes the <div> starting at `start`."""
    depth = 0
    for m in re.finditer(r'<div\b|</div>', s[start:]):
        depth += 1 if m.group(0).startswith('<div') else -1
        if depth == 0:
            return start + m.end()
    raise ValueError('unbalanced div')


def process(path):
    s = open(path, encoding='utf-8').read()
    prefix = '../' if path.startswith(('blog/', 'licensing/')) else ''
    link = '<link rel="stylesheet" href="%spopups.css">' % prefix
    changed = False

    if 'POPUPS:START' in s:                       # re-run: swap generated block
        s2 = re.sub(r'<!-- POPUPS:START.*?POPUPS:END -->', lambda m: BLOCK, s, flags=re.S)
    else:
        first = None
        for oid in ('bioOverlay', 'aiEthicsOverlay'):
            while True:
                m = re.search(r'<div\b[^>]*\bid="%s"[^>]*>' % oid, s)
                if not m:
                    break
                end = balanced_end(s, m.start())
                # swallow the leading indentation so the layout stays tidy
                st = m.start()
                while st > 0 and s[st - 1] in ' \t':
                    st -= 1
                if first is None or st < first:
                    first = st
                s = s[:st] + '\x00POP\x00' + s[end:]
        if first is None:
            if path != 'blog/index.html':
                return False
            anchor = s.find('id="contactOverlay"')
            sc = s.find('<script', anchor)
            s = s[:sc] + '\x00POP\x00' + BLOG_INDEX_JS.replace('\n    <script>', '\n    <script>', 1) + '\n    ' + s[sc:]
        # keep only the first placeholder
        parts = s.split('\x00POP\x00')
        s2 = parts[0] + BLOCK + ''.join(parts[1:])

    if 'popups.css' not in s2:
        s2 = s2.replace('</head>', '    ' + link + '\n</head>', 1)

    # Join the List: swap the generated block, or add it just above the pop-ups on pages that have none yet
    if 'SIGNUP:START' in s2:
        s2 = re.sub(r'<!-- SIGNUP:START.*?SIGNUP:END -->', lambda m: SIGNUP_BLOCK, s2, flags=re.S)
    else:
        s2 = s2.replace('<!-- POPUPS:START', SIGNUP_BLOCK + '\n    <!-- POPUPS:START', 1)

    # shared stylesheet + script, with centrally managed cache-busting versions
    css_v, js_v = asset_version('popups.css'), asset_version('newsletter.js')
    s2 = re.sub(r'(<link rel="stylesheet" href="%spopups\.css)(?:\?v=\w+)?(")' % re.escape(prefix), r'\g<1>?v=%s\2' % css_v, s2)
    tag = '<script src="%snewsletter.js?v=%s" data-cfasync="false" defer></script>' % (prefix, js_v)
    if re.search(r'<script src="[^"]*newsletter\.js[^"]*"[^>]*></script>', s2):
        s2 = re.sub(r'<script src="[^"]*newsletter\.js[^"]*"[^>]*></script>', lambda m: tag, s2)
    else:
        s2 = s2.replace('</body>', '    ' + tag + '\n</body>', 1)

    if s2 != open(path, encoding='utf-8').read():
        open(path, 'w', encoding='utf-8').write(s2)
        return True
    return False


def run_all():
    """Stamp the shared components onto every page; fail loudly if a real page ends up without them."""
    n = 0
    pages = sorted(glob.glob('*.html') + glob.glob('blog/*.html') + glob.glob('licensing/*.html'))
    for f in pages:
        if process(f):
            n += 1
            print('updated', f)
    missing = []
    for f in pages:
        t = open(f, encoding='utf-8').read()
        if 'POPUPS:START' in t and not all(k in t for k in ('SIGNUP:START', 'popups.css', 'newsletter.js')):
            missing.append(f)
    assert not missing, 'pages missing the shared sign-up / assets: %s' % missing
    print(n, 'pages updated by build_popups;', len([p for p in pages if 'SIGNUP:START' in open(p, encoding='utf-8').read()]), 'pages carry Join the List')


if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    run_all()
