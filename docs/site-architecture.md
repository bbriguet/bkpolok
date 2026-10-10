# bkpolok — Site architecture

How the design in `_artifact/` is implemented. Written 2026-09-20, updated 2026-10-10 for the new
version of the artifact (https://claude.ai/artifact/BLup8P24VeWbH4hJMK9yFf).

## The design files (`_artifact/`)

| Path | Content |
|---|---|
| `source/index.html` | copy of the artifact page; its embedded images point to `../assets/` |
| `assets/` | the 13 images of the artifact (portrait, figures, personal photo, gallery) |
| `design/structure.md` | sections, heading hierarchy, behaviour, and what changed since 2026-09 |
| `design/components.md` | every component: markup, variants, accessibility rules |
| `design/tokens.css` | design tokens extracted from the page (copied as is into `static/css/tokens.css`) |
| `design/content.yaml` | every text, link, alt text and image file, imported by `charger_contenu_initial` |

## Pages (URLs)

Created as **unpublished drafts** by `python manage.py create_site_pages` (idempotent; also
`apps.pages.services.create_site_pages`). Publish each one in the Wagtail admin once it has content.

| URL | Type | Notes |
|---|---|---|
| `/` | `HomePage` | hero, quote |
| `/about/` | `StandardPage` | heading with a two-image figure, paragraphs, language caption |
| `/services/` | `ServiceIndexPage` | offer cards (its live `ServicePage` children), “What I bring”, call to action |
| `/services/medical-affairs-consulting/` `…/patient-programs-advocacy/` `…/coaching/` | `ServicePage` | the three offers; `summary` (600 characters) is the offer card text |
| `/experience/` | `StandardPage` | industry timeline; research timeline + education under “show more” |
| `/publications/` | `StandardPage` | featured paper, research papers (3 + “show more”), TV & press under “show more” |
| `/personal/` | `StandardPage` | cards, “Through my lens” gallery, aside notes |
| `/contact/` | `ContactPage` | contact form + details; page fields override the site profile |
| `/contact/thank-you/` | route of `ContactPage` (`RoutablePageMixin`) | confirmation after a valid submission; `noindex`, not in the sitemap |
| `/legal-notice/` | `StandardPage` | Legal notice (Impressum); not in the menu, linked from the footer |
| `/privacy/` | `StandardPage` | Privacy statement; not in the menu, linked from the footer |

The nav lists live, “show in menus” pages under the home page, in tree order; the label is the page
title. The services index was called “Expertise” (`/expertise/`) before 2026-10; the design now says
“Services”, so the page was renamed (title and slug). In the artifact the legal texts are
disclosures inside the footer; here they are pages (`page--legal` styling), chosen in the site
profile. A services index whose body already has a “Service offers” block does not repeat the list.

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
The artifact itself has no form (only a mailto link): the form is a feature of the site.

## SEO

Every page: `<title>` (`seo_title` or title, then the site name), meta description, canonical URL,
Open Graph (`og:title/description/url/site_name/type`, `og:image` + size + alt) and `twitter:card`,
all built by `apps.pages.services.build_seo` (tag `{% page_seo %}`). Description: Promote-tab field, else the
page `summary` / `intro`, else the site profile description. Share image: page `og_image`, else
`SiteProfile.share_image` (rendition `fill-1200x630`, absolute URL on the site host). Exactly one
`<h1>`: the page title, or the hero when the body contains one (a second hero is refused by
`BodyPage.clean`, including inside sections and “show more” blocks). `/sitemap.xml` (live pages only)
and `/robots.txt` (admin disallowed, sitemap linked) exist. JSON-LD `Person` on the home page.

## Data (`apps/profile`)

Site setting **Site profile**: name (+ `name_language`, so the `<h1>` reads `lang="pl"`), short and
legal name, job title, employer, email, LinkedIn, PubMed URL, publications page, meta description,
share image, and the **footer**: heading, lede, accessibility statement (rich text), legal notice
and privacy pages, copyright notice (the sentence after “© year legal name.”).

Snippets under the admin menu **Profile**:
- **Experience** (+ achievements, images): `parallel_role` (“In parallel: …”), `pair_with_next` (the
  entry's images are shown in one column beside it and the next, older entry: the design's
  `tl-pair`). An achievement can link some of its words (`link_text`) to a **Publication**.
- **Publication**: `category` *medical affairs work* (highlighted ★ cards) or *research* (numbered,
  numbering restarts per category), `note` (sentence under a highlighted paper).
- **Education**: `description`; `listed` (unticked: kept for the JSON-LD `alumniOf` but not shown as
  a card — the PhD, which the design shows in the timeline).
- **Media appearance**: `language` (of the linked page or video, announced to screen readers) and
  `title_language` (`lang` attribute on the title).
- **Language**: name, level; feeds the caption under About and the footer line “Working in …”.

Logic lives in `apps/profile/services.py` (periods such as `Dec 2022 — present` and their parts,
timeline rows and pairs, achievement links, group labels, language caption and footer line, JSON-LD,
footer parameters).

## Blocks (`apps/pages/blocks.py`, `apps/profile/blocks.py`)

Editorial: hero (+ “Today: …” line), section heading (eyebrow, lede, pills, and on the right a photo
or a one/two-image **figure**; level h2, h3 or *small subheading*), rich text, image, pull quote
(+ comment), call to action (band), card grid (service / off-duty; card titles h3 or h4), aside
notes (1 or 2, with optional titles), service offers (cards), **tag line**, **photo gallery**, FAQ,
a **Section** wrapper (anchor + default/tinted background) and a **Show more** wrapper
(`<details>`, usable at the top level and inside sections).
Dynamic (filled from the models): timeline, education, publications (by category, with the number
shown before “show more” and its label), media list, languages.
`PublicationListBlock` (the former static block) is kept only because old migrations reference it;
pages use `PublicationsBlock`, which still reads old `null` values.
Icons come from the fixed set in `apps/pages/icons.py` (`{% icon "name" %}`).

## Front end

`static/css/tokens.css` (design tokens: light, dark, high contrast light and dark,
`prefers-contrast`, text-size steps, plus site tokens for motion that reduce to 0 under
`prefers-reduced-motion`) → `fonts.css` (self-hosted Fraunces, Source Sans 3, IBM Plex Mono) →
`base.css` (reset, text-size steps, focus ring, skip link, underlined links, forced colours, print)
→ `components/<name>.css` (one file per component, listed in `base.html`) → `site.css` (page layout:
page header, rich text, legal pages, figure). Every stylesheet uses only tokens; tests enforce it
(no colours, no durations, no literal font sizes; text sizes are `rem`).

Scripts:
- `static/js/preferences.js` (in `<head>`, not deferred): **Display settings** — text size (5 steps),
  high contrast, dark mode, stored in `localStorage` and applied to `<html>` before the first paint;
  wires the bar (`includes/display_settings.html`), which stays hidden without JavaScript.
- `static/js/site.js` (deferred): opens a “show more” when a link or the URL hash targets something
  inside it, opens them all before printing, gives focus to `<main>` from the skip link, blocks the
  context menu and dragging on protected galleries.
- `static/js/reveal.js`: scroll reveal (`data-reveal`), off under reduced motion.

**Components** are `templates/includes/<name>.html`, called with `{% include … with … only %}`; the
parameters are documented at the top of each file. The stream blocks (`pages/blocks/*.html`,
`profile/blocks/*.html`) are thin wrappers that build the parameters (links via
`apps/pages/services.py`, images via `image_props`) and include the component. Images reach the
includes as renditions (`url`, `width`, `height`, `alt`), so no include depends on the database.

- **Icons**: inline SVG files in `templates/includes/icons/<name>.svg`, rendered by `{% icon "name" %}`
  (no JS). `apps/pages/icons.py` lists the ones editors can pick; `chevron` and `settings` are UI-only.
- **Accessibility** (from the design): skip link, Display settings, 44px targets, sr-only texts
  (“to” in periods, “(opens in a new tab)”, “in French”, “Date unknown”), `lang` attributes,
  underlined links, high-contrast theme, forced colours, print.
- **Motion**: CSS transitions, one `@keyframes` (status dot), `<details>` open animation via
  `::details-content` (accordion), scroll reveal. Without JS or with reduced motion, everything stays
  visible and static.
- **Demo page**: `/_composants` shows every component (DEBUG only; 404 otherwise). Temporary: delete
  `apps/pages/demo.py`, `components_demo` in `views.py` and `config/urls.py`, `templates/dev/`,
  `static/css/demo.css` and `static/demo/` once validated.

## Language and formats

`LANGUAGE_CODE = "en"`. Swiss formats are forced for the `en` locale by `config/formats/en/formats.py`
(dates `19.05.2008`, times `14:30`, numbers `1’234.50`). `USE_THOUSAND_SEPARATOR` is deliberately off
(it would print the year 2009 as `2’009`); use the `intcomma` filter for displayed quantities.
The design writes media dates `19 May 2008` (day first, with `<time datetime>`) and periods
`Dec 2022 — present`: the templates follow it.

## Deviations from the design

- **Multi-page site** instead of the one-page artifact (anchors become pages; see above), and the
  legal texts are pages instead of footer disclosures.
- **Contact form** on `/contact/` in addition to the mailto link (see the privacy note below).
- **Images**: all `<img>` carry `width`, `height`, `alt` and `loading="lazy"`, except the hero portrait,
  which is the first-screen image. The design's `object-position` crops of the two figures are Wagtail
  focal points (set by the import).
- **Display settings bar** hidden without JavaScript (in the artifact the button shows but does
  nothing).
- **Brand** in the nav is a link to the home page (the artifact's is `aria-hidden` text).
- **Offer card titles** link to the service pages.
- **Language caption** groups consecutive levels: “French, English & German (full professional)”.
- **Research thumbnails** linking to a paper have no sr-only “(see publication 2)”: the number is not
  known to the timeline.
- **Accordion**, interaction states and scroll reveal are additions: the source has no FAQ.
- No colour deviation any more: the 2026-10 palette reaches AA on every surface by itself
  (`tests/test_tokens_contrast.py` checks the four themes; high contrast reaches AAA).

## Initial content (`charger_contenu_initial`)

`python manage.py charger_contenu_initial` loads `_artifact/design/content.yaml` (`--file` for another
one) and the images it names from `_artifact/assets/` (`--assets` for another folder). Logic in
`apps/pages/initial_content.py`.

- **Where each section goes**: home = hero + quote; About = heading with the figure + paragraphs +
  languages; Services = heading, offer cards (the three `ServicePage` children: title and `summary`),
  “What I bring” subheading, tag line, service cards (h4), call to action; Experience = industry
  timeline + “show more” (research timeline + education); Publications = featured paper, research
  papers (3 visible), “show more” for TV & press; Personal = heading with photo, cards, gallery, notes.
  The YAML `contact` section *is* the footer (site profile); the Contact page body stays empty. The
  `legal_notice` and `privacy` texts fill `/legal-notice/` and `/privacy/` (one rich text block each,
  section titles as `h2`). Each section is a `Section` block (anchor from the YAML `id`; tinted
  background for Services and Publications).
- **Links**: an anchor (`#contact`, `#services`, …) becomes the page that carries it; `#pub-ma` and
  `#pub-02` become the corresponding `Publication` (achievement link, figure captions).
- **Images**: imported once as Wagtail images (title = file name, description = alt text, found again
  by the file's hash); each use carries its own alt text. A missing file is reported, not fatal.
- **Idempotent**: objects are found by natural key (PMID, code, category + title + start date, file
  hash, …); a filled value is never overwritten (the difference is reported), `--update` overwrites.
  A page body is written only when empty or identical. Pages stay drafts (a revision is saved,
  nothing is published). **Nothing is deleted**: records that are in the database but not in the
  YAML are listed (“absent du YAML”), to delete in the admin if needed.
- **TODO**: any value containing `TODO` is imported as is and listed with its YAML path and
  destination. The real file has five, all placeholders of the legal texts (address, phone, VAT
  number, hosting provider and log retention, email provider). A TODO in a year, a date or an image
  position cannot be stored verbatim: the import stops and rolls back.
- Reported differences: the grouped language caption, `alumniOf` (computed from the education
  records: “Jagiellonian University, Kraków” and “University of Freiburg”).

## Not done yet

- **Legal texts**: fill the five `[TODO: …]` placeholders on `/legal-notice/` and `/privacy/`
  (hosting is planned on an Infomaniak VPS — to confirm before writing it).
- **Privacy statement vs. the site**: the artifact's text says the site sets *no cookies* and that
  personal data reaches the owner *by email*. The site's contact form stores messages in the database
  (admin menu Messages) and sets Django's CSRF cookie on the contact page; section 5 (and 2) must
  mention the form before the privacy page is published.
- **Image rights**: the Olympus/Evident product photo (IXplore SpinSR) is not the owner's work; the
  Kotkamp et al. 2014 figures come from PLoS One (CC BY, credited beside them).
- Claims flagged in the 2026-09 review (career figures such as “15 years”) are imported as written.
