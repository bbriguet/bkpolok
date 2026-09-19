# Components

Minimal HTML + CSS for each repeated component of the "Bożena Polok" page. All CSS uses the
custom properties from `tokens.css`; load that file first. Class names are the source's.

## Base (applies to everything)

```css
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0; padding:0 var(--gutter); background:var(--bg); color:var(--ink);
     font:var(--fw-regular) var(--fs-body)/var(--lh-body) var(--font-sans);
     -webkit-font-smoothing:antialiased}
.wrap{max-width:var(--wrap-max); margin:0 auto}
h1,h2,h3{font-family:var(--font-serif); font-weight:var(--fw-semibold); text-wrap:balance; margin:0; color:var(--ink)}
a{color:var(--accent)}
a:focus-visible,button:focus-visible,.btn:focus-visible{outline:2px solid var(--accent); outline-offset:2px}
::selection{background:var(--accent-soft); color:var(--ink)}
section{padding:var(--section-pad) 0}
@media (prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
```

---

## 1. Navigation bar

Sticky, translucent, blurred, hairline bottom. Brand left, links right, wraps on small screens.

```html
<nav>
  <div class="wrap">
    <div class="nav-name">B. Polok</div>
    <ul class="nav-links"><li><a href="#about">About</a></li>…</ul>
  </div>
</nav>
```
```css
nav{position:sticky; top:0; z-index:var(--z-nav); background:var(--nav-bg);
    backdrop-filter:blur(var(--nav-blur)); border-bottom:var(--border-hairline)}
nav .wrap{display:flex; align-items:center; justify-content:space-between;
          padding:var(--space-16) 0; gap:var(--space-16); flex-wrap:wrap}
.nav-name{font:var(--fw-semibold) var(--fs-body) var(--font-serif); letter-spacing:var(--ls-badge)}
.nav-links{display:flex; gap:var(--space-22); flex-wrap:wrap; list-style:none; margin:0; padding:0}
.nav-links a{color:var(--ink-muted); text-decoration:none; font-size:var(--fs-ui); font-weight:var(--fw-medium)}
.nav-links a:hover{color:var(--accent)}
```
Variants: none.

## 2. Eyebrow

Mono uppercase label above a heading. Amber accent.
```html
<p class="eyebrow">About</p>
```
```css
.eyebrow{font:var(--fw-medium) var(--fs-xs) var(--font-mono); letter-spacing:var(--ls-eyebrow);
         text-transform:uppercase; color:var(--accent-2)}
```
Variants: none (also used as the label above sub-section `h3`s: "Education", "Media").

## 3. Section head

Eyebrow + heading (+ optional lede / pills).
```html
<div class="section-head">
  <p class="eyebrow">Expertise</p>
  <h2>Where I add the most value</h2>
  <p class="lede">…</p>
</div>
```
```css
.section-head{margin-bottom:var(--space-36)}
.section-head h2{font-size:var(--fs-h2); margin-top:var(--space-8)}
.lede{color:var(--ink-muted); max-width:var(--measure-lede); margin-top:var(--space-12); font-size:var(--fs-lg)}
```
Variants:
- **with lede / pills** (Expertise, Publications, Personal).
- **sub-section**: `<h3>` instead of `<h2>` with inline `font-size` (24px Education, 22px Television / Press) and a larger top margin (52 / 48 / 36px).
- **personal-head**: two-column grid with a photo (component 14).

## 4. Section (default / tint)

```html
<section id="services" class="tint"> … </section>
```
```css
section.tint{background:var(--surface-tint); margin:0 calc(-1 * var(--gutter)); padding:var(--section-pad) var(--gutter)}
```
Variants: default (transparent) · `.tint`.

## 5. Button

```html
<a class="btn btn-primary" href="#contact">Get in touch</a>
<a class="btn btn-ghost" href="…" target="_blank" rel="noopener">LinkedIn ↗</a>
```
```css
.btn{display:inline-flex; align-items:center; gap:var(--space-8); padding:11px 20px;
     border-radius:var(--radius-btn); font-weight:var(--fw-semibold); font-size:var(--fs-ui);
     text-decoration:none; border:1px solid transparent}
.btn-primary{background:var(--accent); color:var(--on-accent)}
.btn-primary:hover{opacity:.92}
.btn-ghost{border-color:var(--line-strong); color:var(--ink)}
.btn-ghost:hover{border-color:var(--accent); color:var(--accent)}
```
Variants: `.btn-primary` · `.btn-ghost`. Container `.hero-cta{margin-top:28px; display:flex; gap:14px; flex-wrap:wrap}`.

## 6. Status badge

```html
<p class="status-badge"><span class="status-dot"></span>Currently at Santen · open to …</p>
```
```css
.status-badge{display:inline-flex; align-items:center; gap:var(--space-8); margin-top:var(--space-16);
  padding:var(--space-6) var(--space-14); border:var(--border-strong); border-radius:var(--radius-pill);
  background:var(--surface-tint); font:var(--fs-xs) var(--font-mono); color:var(--ink-muted); letter-spacing:var(--ls-badge)}
.status-dot{width:var(--size-dot-status); height:var(--size-dot-status); border-radius:var(--radius-round);
  background:var(--accent); box-shadow:var(--ring-status); flex-shrink:0}
```

## 7. Pill (therapeutic areas, languages)

```html
<div class="pill-row"><span class="pill">Ophthalmology</span>…</div>
<div class="lang-row"><span class="lang-pill">Polski</span>…</div>
```
```css
.lang-row,.pill-row{display:flex; flex-wrap:wrap; gap:var(--space-8); margin-top:var(--space-22)}
.lang-pill,.pill{font:var(--fs-xs) var(--font-mono); padding:var(--space-6) var(--space-12);
  border:var(--border-strong); border-radius:var(--radius-pill); color:var(--ink-muted)}
.lang-caption{font-size:var(--fs-sm); color:var(--ink-faint); margin-top:var(--space-10)}
```
Variants: `.pill` (therapeutic area) · `.lang-pill` with full language name (About) · `.lang-pill` with 2-letter code (footer).

## 8. Hero + iris portrait

Two columns (text, portrait), one column ≤ 640px with the portrait hidden.
```html
<header class="hero">
  <div>
    <p class="eyebrow">…</p>
    <h1>Bożena&nbsp;<em>Polok</em></h1>
    <p class="hero-role">…</p> <p class="status-badge">…</p> <p class="hero-thesis">…</p>
    <div class="hero-cta">…</div>
  </div>
  <div class="iris">
    <svg width="374" height="374" viewBox="0 0 168 168" fill="none" aria-hidden="true">
      <circle cx="84" cy="84" r="82" stroke="var(--line-strong)" stroke-width="1"/>
      <circle cx="84" cy="84" r="64" stroke="var(--accent)" stroke-width="1.2"/>
      <g stroke="var(--accent-2)" stroke-width="1.2">
        <line x1="84" y1="2" x2="84" y2="18"/><line x1="84" y1="150" x2="84" y2="166"/>
        <line x1="2" y1="84" x2="18" y2="84"/><line x1="150" y1="84" x2="166" y2="84"/>
      </g>
    </svg>
    <img width="204" height="204" src="…" alt="Portrait of Bożena Polok">
  </div>
</header>
```
```css
.hero{padding:var(--hero-pad); display:grid; grid-template-columns:1.3fr auto; gap:var(--space-40); align-items:center}
.hero h1{font-size:var(--fs-h1); line-height:var(--lh-tight)}
.hero h1 em{color:var(--accent); font-style:italic}
.hero-role{margin-top:var(--space-14); font-size:var(--fs-xl); color:var(--ink-muted); font-weight:var(--fw-medium); max-width:var(--measure-role)}
.hero-thesis{margin-top:var(--space-22); font-size:var(--fs-body-lg); max-width:var(--measure-thesis)}
.iris{flex-shrink:0; position:relative; width:var(--size-iris); height:var(--size-iris)}
.iris svg{position:absolute; inset:0}
.iris img{position:absolute; top:50%; left:50%; transform:translate(-50%,-50%);
  width:var(--size-portrait); height:var(--size-portrait); border-radius:var(--radius-round); object-fit:cover;
  border:var(--bw-portrait) solid var(--accent); box-shadow:var(--ring-portrait)}
@media (max-width:640px){.hero{grid-template-columns:1fr} .iris{display:none}}
```

## 9. Pull quote

```html
<blockquote class="pull-quote">
  <p>“It is far more important …”</p>
  <cite>— Hippocrates</cite>
</blockquote>
```
```css
.pull-quote{padding:var(--space-12) 0 var(--space-56); max-width:640px; margin:0 auto; text-align:center}
.pull-quote::before{content:""; display:block; width:32px; height:2px; background:var(--accent); margin:0 auto var(--space-24)}
.pull-quote p{font:italic var(--fw-medium) var(--fs-quote)/var(--lh-quote) var(--font-serif); margin:0}
.pull-quote cite{display:block; margin-top:var(--space-16); font:normal var(--fs-xs) var(--font-mono);
  letter-spacing:var(--ls-label); text-transform:uppercase; color:var(--accent-2)}
```

## 10. Hairline card grid (`.service-grid`, `.off-duty-grid`)

Cells share 1px gaps that show the `--line` background; the container clips the radius. Same pattern, two card types.
```html
<div class="service-grid">
  <div class="service">
    <svg viewBox="0 0 24 24" fill="none" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">…</svg>
    <h3>Medical Affairs Strategy &amp; Team Leadership</h3>
    <p>…</p>
  </div>
</div>
```
```css
.service-grid,.off-duty-grid{display:grid; grid-template-columns:repeat(3,1fr); gap:1px;
  background:var(--line); border:var(--border-hairline); border-radius:var(--radius-card); overflow:hidden}
@media (max-width:760px){.service-grid,.off-duty-grid{grid-template-columns:repeat(2,1fr)}}
@media (max-width:520px){.service-grid{grid-template-columns:1fr}}
@media (max-width:480px){.off-duty-grid{grid-template-columns:1fr}}

.service{background:var(--surface); padding:26px 22px; min-height:186px; display:flex; flex-direction:column; gap:var(--space-12)}
.service svg{width:var(--size-icon); height:var(--size-icon); color:var(--accent); stroke:currentColor}
.service h3{font:var(--fw-semibold) var(--fs-lg) var(--font-sans)}
.service p{margin:0; color:var(--ink-muted); font-size:var(--fs-ui); line-height:var(--lh-card)}

.off-card{background:var(--surface); padding:var(--space-28) var(--space-24)}
.off-card.wide{grid-column:span 2}
@media (max-width:480px){.off-card.wide{grid-column:span 1}}
.off-card svg{width:var(--size-icon-lg); height:var(--size-icon-lg); color:var(--accent-2); stroke:currentColor; margin-bottom:var(--space-14)}
.off-card h3{font:var(--fw-semibold) var(--fs-2xl) var(--font-serif)}
.off-card p{color:var(--ink-muted); font-size:var(--fs-md); margin-top:var(--space-10)}
```
Variants:
- **`.service`** — teal icon, sans `h3`, 6 cards.
- **`.off-card`** — amber icon, serif `h3`, 5 cards.
- **`.off-card.wide`** — spans two columns (last card).

## 11. Aside note

Tinted call-out. Three uses.
```html
<div class="aside-note"><svg …/>Text…</div>
```
```css
.aside-note{margin-top:var(--space-28); padding:var(--space-18) var(--space-20); border-radius:var(--radius-card);
  background:var(--accent-soft); font-size:var(--fs-md); color:var(--ink); max-width:var(--measure-aside)}
.aside-note svg{width:var(--size-icon-inline); height:var(--size-icon-inline); vertical-align:-3px; margin-right:var(--space-6); color:var(--accent)}
.aside-note + .aside-note{margin-top:var(--space-14)}
```
Variants:
- **plain** (single).
- **`.aside-row`** — two notes side by side, stacked ≤ 700px:
  `.aside-row{display:flex; gap:16px; margin-top:28px; align-items:stretch} .aside-row .aside-note{margin-top:0; flex:1; max-width:none}`
- **`.offer-note`** — full width, larger padding, contains a lead line and a 3-column definition list:
  ```html
  <div class="aside-note offer-note">
    <p class="offer-lead"><svg …/>Also available on a freelance or interim basis, …</p>
    <dl class="offer-list">
      <div class="offer-item"><dt>Medical Affairs Consulting</dt><dd>…</dd></div>
    </dl>
  </div>
  ```
  ```css
  .offer-note{max-width:none; padding:24px 26px}
  .offer-lead{margin:0 0 var(--space-18); font-weight:var(--fw-semibold)}
  .offer-list{display:grid; grid-template-columns:repeat(3,1fr); gap:var(--space-22); margin:0; padding:0}
  @media (max-width:760px){.offer-list{grid-template-columns:1fr; gap:var(--space-16)}}
  .offer-item dt{font:var(--fw-bold) var(--fs-ui) var(--font-sans); color:var(--ink); margin:0 0 var(--space-6)}
  .offer-item dd{margin:0; font-size:var(--fs-md-minus); color:var(--ink-muted); line-height:var(--lh-card)}
  ```

## 12. Timeline

Vertical rail with a dot per entry, grouped under a mono label. Two groups (Industry, Research).
```html
<p class="group-label">Industry — 2011 to present</p>
<div class="timeline">
  <div class="tl-item">
    <div class="tl-date">DEC 2022 — PRESENT</div>
    <h3>Associate Global Medical Director</h3>
    <div class="org">Santen — …</div>
    <div class="org-desc">…</div>
    <p>…</p>
    <ul class="tl-achievements"><li>…</li></ul>
  </div>
</div>
```
```css
.timeline{position:relative; padding-left:var(--space-28); border-left:var(--border-strong)}
.tl-item{position:relative; padding-bottom:var(--space-32)}
.tl-item:last-child{padding-bottom:0}
.tl-item::before{content:""; position:absolute; left:-33px; top:var(--space-4);
  width:var(--size-dot-timeline); height:var(--size-dot-timeline); border-radius:var(--radius-round);
  background:var(--accent); box-shadow:var(--ring-dot)}
.tl-date{font:var(--fw-medium) var(--fs-xs) var(--font-mono); color:var(--accent-2)}
.tl-item h3{font:var(--fw-semibold) var(--fs-xl) var(--font-sans); margin-top:var(--space-4)}
.tl-item .org{color:var(--ink-muted); font-size:var(--fs-ui); margin-top:var(--space-2)}
.tl-item .org-desc{color:var(--ink-faint); font-size:var(--fs-sm); font-style:italic; margin-top:var(--space-2); max-width:var(--measure-desc)}
.tl-item p{color:var(--ink-muted); font-size:var(--fs-md); margin-top:var(--space-8); max-width:var(--measure-text)}
.tl-achievements{list-style:none; margin:var(--space-10) 0 0; padding:0; display:flex; flex-direction:column; gap:var(--space-6); max-width:var(--measure-text)}
.tl-achievements li{font-size:var(--fs-md-minus); color:var(--ink-muted); padding-left:15px; position:relative}
.tl-achievements li::before{content:""; position:absolute; left:0; top:var(--space-8);
  width:var(--size-dot-bullet); height:var(--size-dot-bullet); border-radius:var(--radius-round); background:var(--accent-2)}
.group-label{font:var(--fs-2xs) var(--font-mono); letter-spacing:var(--ls-label); text-transform:uppercase;
  color:var(--ink-faint); margin:0 0 var(--space-18) -28px; padding-left:var(--space-28)}
.group-label:not(:first-child){margin-top:var(--space-8)}
```
Variants:
- **basic** — date, role, org, description, summary (Sanofi; CMU Geneva and BIDMC omit `.org-desc`).
- **with achievements** — adds `.tl-achievements` (Santen, Allergan, UCB, IRO, PhD).
- **with solo photo** (Olympus) — body wrapper places a thumbnail beside the text:
  ```html
  <div class="tl-item-body">
    <div class="tl-item-text">…org, org-desc, p…</div>
    <div class="research-photos tl-photos-solo"><figure class="research-thumb">…</figure></div>
  </div>
  ```
  ```css
  .tl-item-body{display:flex; gap:var(--space-26); align-items:flex-start; flex-wrap:wrap; margin-top:var(--space-2)}
  .tl-item-text{flex:1; min-width:220px}
  .tl-item-text .org{margin-top:0}
  .tl-photos-solo{flex-shrink:0; margin-top:var(--space-4)}
  .tl-photos-solo .research-thumb img{width:var(--size-thumb-solo); height:var(--size-thumb-solo); border-width:var(--bw-photo-sm); box-shadow:var(--ring-thumb-sm)}
  .tl-photos-solo .research-thumb figcaption{font-size:var(--fs-3xs); margin-top:var(--space-6); max-width:110px}
  @media (max-width:560px){.tl-photos-solo{order:-1}}
  ```
- **pair with spanning photos** (IRO + PhD) — two entries share a right-hand column of two thumbnails:
  ```html
  <div class="tl-pair">
    <div class="tl-item">…</div><div class="tl-item">…</div>
    <div class="research-photos tl-photos-span"><figure class="research-thumb">…</figure>×2</div>
  </div>
  ```
  ```css
  .tl-pair{display:grid; grid-template-columns:1fr auto; column-gap:var(--space-26); align-items:stretch}
  .tl-pair .tl-item{grid-column:1}
  .tl-photos-span{grid-column:2; grid-row:1 / 3; align-self:stretch; display:flex; flex-direction:column;
    justify-content:space-between; gap:var(--space-14); padding:var(--space-4) 0 var(--space-32)}
  .tl-photos-span .research-thumb img{width:var(--size-thumb-span); height:var(--size-thumb-span); border-width:var(--bw-photo-sm); box-shadow:var(--ring-thumb-sm)}
  .tl-photos-span .research-thumb figcaption{font-size:var(--fs-3xs); margin-top:var(--space-6)}
  @media (max-width:640px){
    .tl-pair{grid-template-columns:1fr}
    .tl-photos-span{grid-column:1; grid-row:auto; flex-direction:row; justify-content:flex-start; padding:0 0 var(--space-16); order:-1}
  }
  ```

## 13. Research thumbnail (figure)

```html
<figure class="research-thumb">
  <img src="…" alt="…">
  <figcaption>FIG. 1 <a href="#pub-02">Kotkamp et al., 2014 →</a></figcaption>
</figure>
```
```css
.research-photos{display:flex; gap:var(--space-16); flex-shrink:0}
.research-thumb{margin:0; text-align:center}
.research-thumb img{width:var(--size-thumb); height:var(--size-thumb); border-radius:var(--radius-round); object-fit:cover;
  border:var(--bw-photo) solid var(--accent); box-shadow:var(--ring-thumb); display:block}
.research-thumb figcaption{margin-top:9px; font:var(--fs-2xs) var(--font-mono); color:var(--ink-faint); letter-spacing:var(--ls-caption)}
.research-thumb figcaption a{color:var(--accent-2); text-decoration:none; margin-left:3px}
.research-thumb figcaption a:hover{text-decoration:underline}
```
Variants: default 108px · solo 84px · span 76px (see Timeline). Individual images may set `object-position` inline.

## 14. Circular photo (personal)

```html
<img class="personal-photo" src="…" alt="Bożena Polok" width="294" height="294">
```
```css
.personal-head{display:grid; grid-template-columns:1fr auto; gap:var(--space-32); align-items:center}
.personal-photo{width:var(--size-personal); height:var(--size-personal); border-radius:var(--radius-round); object-fit:cover;
  border:var(--bw-personal) solid var(--accent-2); box-shadow:var(--shadow); transform:rotate(-3deg); justify-self:end}
@media (max-width:640px){.personal-head{grid-template-columns:1fr} .personal-photo{justify-self:start; transform:rotate(-2deg)}}
```
Note: the hero portrait uses a teal border and an SVG ring; this one uses an amber border, a shadow and a tilt.

## 15. Education card

```html
<div class="edu-grid">
  <div class="edu-card"><div class="deg">PhD, Molecular &amp; Developmental Biology</div><div class="inst">University of Freiburg</div></div>
</div>
```
```css
.edu-grid{display:grid; grid-template-columns:1fr 1fr; gap:var(--space-20); margin-top:var(--space-8)}
@media (max-width:600px){.edu-grid{grid-template-columns:1fr}}
.edu-card{border:var(--border-hairline); border-radius:var(--radius-card); padding:var(--space-18) var(--space-20); background:var(--surface)}
.edu-card .deg{font-weight:var(--fw-semibold); font-size:var(--fs-md-plus)}
.edu-card .inst{color:var(--ink-muted); font-size:var(--fs-md-minus); margin-top:var(--space-4)}
```

## 16. Publication row

Numbered list, hairline between rows, PubMed link when available.
```html
<ol class="pub-list">
  <li class="pub" id="pub-02">
    <span class="pub-num">02</span>
    <div>
      <div class="pub-title">Pou5f1/Oct4 promotes cell survival …</div>
      <div class="pub-meta">Kotkamp K, … et al. · <em>PLoS One</em>, 2014 · <a href="…" target="_blank" rel="noopener">PMID 24643012</a></div>
    </div>
  </li>
</ol>
<div class="pub-source"><a href="…">Full record on PubMed →</a></div>
```
```css
.pub-list{list-style:none; margin:0; padding:0}
.pub{display:grid; grid-template-columns:34px 1fr; gap:var(--space-14); padding:var(--space-18) 0; border-top:var(--border-hairline)}
.pub:first-child{border-top:none}
.pub-num{font:var(--fs-sm) var(--font-mono); color:var(--ink-faint); padding-top:var(--space-2)}
.pub-title{font-weight:var(--fw-semibold); font-size:var(--fs-md-plus); line-height:var(--lh-snug)}
.pub-meta{color:var(--ink-muted); font-size:var(--fs-sm-plus); margin-top:var(--space-5); line-height:var(--lh-meta)}
.pub-meta a{color:var(--accent); text-decoration:none}
.pub-meta a:hover{text-decoration:underline}
.pub-source{margin-top:var(--space-14)}
.pub-source a{font-size:var(--fs-md-minus); color:var(--ink-muted)}
```
Variants: with PMID link (9 of 10) · without link (#10, 2002 paper). The row targeted by a cross-link carries an `id`.

## 17. Media list + note

```html
<ul class="media-list">
  <li><span class="media-date mono">14.01.2009</span> TSR — <a href="…">"Visually impaired: glimmers of hope"</a></li>
</ul>
<p class="media-note">Video not currently available online — …</p>
```
```css
.mono{font-family:var(--font-mono)}
.media-list{list-style:none; margin:var(--space-16) 0 0; padding:0; display:flex; flex-direction:column; gap:var(--space-10)}
.media-list li{display:flex; gap:var(--space-12); align-items:baseline; font-size:var(--fs-md); flex-wrap:wrap}
.media-date{font:var(--fw-medium) var(--fs-xs) var(--font-mono); color:var(--accent-2); min-width:88px}
.media-note{margin-top:var(--space-16); font-size:var(--fs-sm-plus); color:var(--ink-faint);
  border-left:2px solid var(--line-strong); padding-left:var(--space-12)}
.media-note a{color:var(--ink-muted)}
```
Variants: television list · press list. Item with link / item without link; date may be a dash "—" when unknown.

## 18. Footer / contact

```html
<footer id="contact">
  <div class="footer-grid">
    <div>
      <p class="eyebrow">Contact</p>
      <h2>Let's talk medical affairs.</h2>
      <a class="contact-email" href="mailto:…">…</a><br>
      <a class="contact-email" href="https://…" target="_blank" rel="noopener">…</a>
    </div>
    <div class="lang-row"><span class="lang-pill">PL</span>…</div>
  </div>
  <p class="copyright">© 2026 Bożena Karolina Polok.</p>
</footer>
```
```css
footer{padding:var(--space-56) 0 var(--space-64); border-top:var(--border-hairline)}
.footer-grid{display:flex; justify-content:space-between; align-items:flex-end; gap:var(--space-24); flex-wrap:wrap}
footer h2{font-size:var(--fs-5xl)}
footer .contact-email{font:var(--fs-md) var(--font-mono); margin-top:var(--space-10); display:inline-block}
.copyright{color:var(--ink-faint); font-size:var(--fs-sm); margin-top:var(--space-40)}
```

## 19. Line icons

All icons are inline SVG, `viewBox="0 0 24 24"`, `fill="none"`, `stroke-width="1.6"`, round caps and joins,
`aria-hidden="true"`, coloured by `currentColor`. Teal in service cards and aside notes, amber in off-duty cards.
The offer lead icon is a flag (`M4 4v16M4 4h11l-2 4 2 4H4`) inlined with `style="display:inline;"`.
