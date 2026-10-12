#!/usr/bin/env python3
"""Rebuild the release grid, playlist embed and lyrics data in music.html from releases.json.
Usage: python3 build_music.py   (run from the site folder, then commit + push)"""
import json, re, html
from urllib.parse import quote

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
                        <a class="volume-btn" href="mailto:info@sunolicious.com?subject={subj}">License This Track</a>
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
                        <a class="volume-btn" href="mailto:info@sunolicious.com?subject={subj}">License This Track</a>
                    </div>
                </div>''')
lgrid = '<div class="volumes-grid">\n' + '\n'.join(lic) + '\n            </div>\n            <div style="max-width: 900px; margin: 0 auto 3rem;">\n' + player_html + '\n            </div>'
L = open('licensing.html', encoding='utf-8').read()
L, n3 = re.subn(r'(<!-- LICENSING-GRID:START -->).*?(<!-- LICENSING-GRID:END -->)',
                lambda m: m.group(1) + '\n            ' + lgrid + '\n            ' + m.group(2), L, flags=re.S)
assert n3 == 1
open('licensing.html', 'w', encoding='utf-8').write(L)
print(f'music.html + licensing.html rebuilt: {len(rels)} releases')
