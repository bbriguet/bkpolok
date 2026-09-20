# bkpolok — Site architecture

How the design in `_artifact/design/` is implemented. Written 2026-09-20.

## Pages (URLs)

Created as **unpublished drafts** by `python manage.py create_site_pages` (idempotent; also
`apps.pages.services.create_site_pages`). Publish each one in the Wagtail admin once it has content.

| URL | Type | Notes |
|---|---|---|
| `/` | `HomePage` | hero, quote, cards, call to action |
| `/about/` | `StandardPage` | |
| `/expertise/` | `ServiceIndexPage` | lists its live `ServicePage` children automatically |
| `/expertise/medical-affairs-consulting/` `…/patient-programs-advocacy/` `…/coaching/` | `ServicePage` | the three offers; `summary` allows 600 characters |
| `/experience/` | `StandardPage` | timeline + education blocks |
| `/publications/` | `StandardPage` | publication + media blocks |
| `/personal/` | `StandardPage` | card grid ("off the clock" layout) + aside notes |
| `/contact/` | `ContactPage` | contact form + details; page fields override the site profile |
| `/contact/thank-you/` | route of `ContactPage` (`RoutablePageMixin`) | confirmation after a valid submission; `noindex`, not in the sitemap |

The nav lists live, "show in menus" pages under the home page, in tree order; the label is the page title.

## Contact form (`apps/contact`)

A real Django form (`ContactForm`, a `ModelForm` on `ContactMessage`) served by `ContactPage`:
CSRF token (passed explicitly to the include, which uses `only`), server-side validation (422 with
errors and the typed values kept), honeypot field `website` (hidden off-screen; a filled one is
answered with the normal redirect but nothing is saved or sent). A valid submission is saved, then
emailed (`apps/contact/services.py`) to the page email, else the site profile email, with the
sender in `Reply-To`, then redirected (POST/redirect/GET) to `/contact/thank-you/`. The message is
saved **before** sending: if SMTP fails, it stays in the admin (menu **Messages**, `email_error`
filled, `emailed_at` empty) and the visitor still sees the confirmation.
SMTP comes from environment variables in `config/settings/prod.py` (`EMAIL_HOST`, `EMAIL_PORT`,
`EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, `DEFAULT_FROM_EMAIL`, which defaults to
`EMAIL_HOST_USER`); in dev, emails are printed in the `web` container log.

## SEO

Every page: `<title>` (`seo_title` or title, then the site name), meta description, canonical URL,
Open Graph (`og:title/description/url/site_name/type`, `og:image` + size + alt) and `twitter:card`,
all built by `apps.pages.services.build_seo` (tag `{% page_seo %}`). Description: Promote-tab field, else the
page `summary` / `intro`, else the site profile description. Share image: page `og_image`, else
`SiteProfile.share_image` (rendition `fill-1200x630`, absolute URL on the site host). Exactly one
`<h1>`: the page title, or the hero when the body contains one (a second hero is refused by
`BodyPage.clean`, including inside sections). `/sitemap.xml` (live pages only) and `/robots.txt`
(admin disallowed, sitemap linked) exist.

## Data (`apps/profile`)

Site setting **Site profile** (name, short name, legal name, job title, employer, email, LinkedIn,
PubMed URL, publications page, footer heading, meta description) and snippets under the admin menu
**Profile**: Experience (+ achievements, images), Publication, Education, Media appearance, Language.
Logic lives in `apps/profile/services.py` (periods such as `DEC 2022 — PRESENT`, group labels
derived from the data, language caption, JSON-LD). Publications and media use an explicit
`sort_order`; the number shown beside a paper follows it.

## Blocks (`apps/pages/blocks.py`, `apps/profile/blocks.py`)

Editorial: hero, section heading (eyebrow, lede, pills, round photo), rich text, image, pull quote,
call to action, card grid (service / off-duty), aside notes (1 or 2), service offers, FAQ, and a
**Section** wrapper (anchor + default/tinted background). Dynamic (filled from the models):
timeline, education, publication list, media list, languages.
Icons come from the fixed set in `apps/pages/icons.py` (`{% icon "name" %}`).

## Front end

`static/css/tokens.css` (design tokens, light/dark, plus motion tokens that reduce to 0 under
`prefers-reduced-motion`) → `fonts.css` (self-hosted Fraunces, Source Sans 3, IBM Plex Mono, latin +
latin-ext, OFL licences in `static/fonts/LICENSES.txt`) → `base.css` → `components/<name>.css` (one file per
component, listed in `base.html`) → `site.css` (page layout only: page header, rich text, figure). Every
stylesheet uses only tokens; tests enforce it (no colours, no durations in the CSS). Wagtail wraps each
stream block in `<div class="block-<type>">`; the CSS relies on that.

**Components** are `templates/includes/<name>.html`, called with `{% include … with … only %}`; the
parameters are documented at the top of each file. The stream blocks (`pages/blocks/*.html`,
`profile/blocks/*.html`) are thin wrappers that build the parameters (links via
`apps/pages/services.py`) and include the component. Images reach the includes as renditions
(`url`, `width`, `height`) plus an explicit `alt`, so no include depends on the database.

- **Icons**: inline SVG files in `templates/includes/icons/<name>.svg`, rendered by `{% icon "name" %}`
  (no JS). `apps/pages/icons.py` lists the ones editors can pick; `chevron` is UI-only.
- **Interaction states**: buttons (normal, hover, keyboard focus from `base.css`, pressed, disabled via
  `disabled` or `aria-disabled="true"`), nav / footer / caption / publication / media links, accordion
  summary.
- **Motion**: CSS transitions, one `@keyframes` (status dot), `<details>` open animation via
  `::details-content` where supported, and scroll reveal (`data-reveal` + `static/js/reveal.js`,
  IntersectionObserver). Without JS, without IntersectionObserver or with reduced motion, everything
  stays visible and static.
- **Accordion**: native `<details>/<summary>` (`includes/accordion.html`, used by the FAQ block).
- **Demo page**: `/_composants` shows every component (DEBUG only; 404 otherwise). Temporary: delete
  `apps/pages/demo.py`, `components_demo` in `views.py` and `config/urls.py`, `templates/dev/`,
  `static/css/demo.css` and `static/demo/` once validated.

## Language and formats

`LANGUAGE_CODE = "en"`. Swiss formats are forced for the `en` locale by `config/formats/en/formats.py`
(dates `19.05.2008`, times `14:30`, numbers `1’234.50`). `USE_THOUSAND_SEPARATOR` is deliberately off
(it would print the year 2009 as `2’009`); use the `intcomma` filter for displayed quantities.

## Deviations from the design

- **Timeline pairs** (`tl-pair`, two entries sharing a photo column) are not implemented: an entry shows
  its own images beside its text.
- **Contrast**: `tokens.css` keeps the design's exact values. Light `--ink-faint` (#647268) and `--accent-2`
  (#9c5c1b) reach only 4.26:1 and 4.46:1 on `--surface-tint` (below the 4.5:1 AA threshold for small text).
- **Images**: all `<img>` carry `width`, `height`, `alt` and `loading="lazy"`, except the hero portrait,
  which is the first-screen image (lazy-loading it would delay the largest paint).
- **Hero portrait** stays visible on narrow screens (smaller) instead of being hidden.
- **Icons** in aside notes get `stroke: currentColor`; the source page left them without a stroke.
- **Research thumbnails** follow the design sizes (108px default, 84px inside a timeline); the 76px "span" variant is unused because the timeline pair is not implemented.
- **Accordion** and the interaction states / scroll reveal are additions: the source page has no FAQ and no hover states beyond a few colours.
- **Language caption** groups consecutive levels: "French, English & German (full professional)".
- **Footer heading** ("Let's talk…") is a site-profile field, since the footer appears on every page.
- **Anchors** in figure captions point to `<publications page>#pub-<id>` (set in the site profile).

## Initial content (`charger_contenu_initial`)

`python manage.py charger_contenu_initial` loads `_artifact/design/content.yaml` (`--file` for another
one). Logic in `apps/pages/initial_content.py`.

- **Where each section goes**: home = hero + pull quote; About = about section (paragraphs + languages);
  Expertise = heading, 6 service cards, offer block (the three offers are the `ServicePage` children, their
  `summary` is the offer text); Experience = timeline (industry, research) + education; Publications =
  publication list + television and press lists; Personal = off-the-clock cards + aside notes. The YAML
  `contact` section *is* the footer: it feeds the site profile (email, LinkedIn, footer heading) and the
  languages, so the Contact page body stays empty. Each section is a `Section` block (anchor from the YAML
  `id`; tinted background for Expertise and Publications, as in the design).
- **Structured data**: `SiteProfile`, `Language` (levels parsed from `languages_caption`), `Education`,
  `Experience` (+ achievements; period parsed from « DEC 2022 — PRESENT », start = 1st of the month, end =
  last day, checked by round trip), `Publication`, `MediaAppearance`.
- **Idempotent**: objects are found by natural key (PMID, code, category + title + start date, …); a
  filled value is never overwritten (the difference is reported), `--update` overwrites. A page body is
  written only when empty or identical. Pages stay drafts (a revision is saved, nothing is published).
- **TODO**: any value containing `TODO` is imported as is and listed with its YAML path and destination.
  A TODO in a year or a date cannot be stored verbatim: the import stops and rolls back. TODO in YAML
  comments are listed too (not importable).
- **Not imported** (reported at the end of each run): every image (no file in `_artifact/assets`) and the
  card / note icons (the YAML has none). Add them in the admin.
- Reported differences: the site name (`Site.site_name` is `bkpolok`, the YAML title is `Bożena Polok`), the
  grouped language caption, `alumniOf` (computed from education names).

## Not done yet

Images and icons (above). Claims flagged in the review (career figures, product names, quote attribution,
PMIDs) were imported as written in the YAML and are still to be validated. Pages are drafts.
