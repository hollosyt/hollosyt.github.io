# TeamKid Williamston — site

A rebuild of [teamkidwilliamston.com](https://teamkidwilliamston.com/) as static HTML.
All copy, contact details, the belief statement, the covenants, the FAQs and the
registration form link are taken from the live site; nothing is invented.

## Run it

```bash
python3 -m http.server 4173
```

Then open <http://localhost:4173>. There is no build step and no dependencies —
just open `index.html` if you prefer.

## Files

| File | What's on it |
| --- | --- |
| `index.html` | Hero, welcome, when & where, the season, an afternoon, ways in, contact |
| `about.html` | Vision / mission / program, who we are, the 11-point belief statement |
| `volunteer.html` | Filterable roles, expectations, adult & student covenants, FAQs |
| `donate.html` | The $4,000 story, what it buys, four ways to give |
| `assets/styles.css` | The whole design system — tokens, components, light + dark |
| `assets/site.js` | Theme toggle, sticky nav, filters, tabs, reveals, mail hand-off |
| `assets/favicon.svg` | The mark |

The original ten pages collapse into these four; every page of content survives.

## Design notes

**"Wednesday Afternoon Light."** TeamKid runs November through March, 3:45–5:00 PM,
in Michigan — which means it happens almost entirely after dark. The site is built
on that: a dusk-indigo night outside, warm cream light inside, and a hand-drawn
school with its cafeteria windows lit.

- **No stock photography.** The original leans on placeholder images (its logo file
  is literally named `lol.png`). This version is illustrated instead — one custom SVG
  scene, a paper-star mark, and hand-drawn icons. Drop in real photos later if you
  have releases for them; the layout has room.
- **The words are theirs.** Body copy is taken from the live site, verbatim or close
  to it. Only headings, section labels, nav and button text are newly written, and
  those stay factual — no atmosphere added, no facts dropped for the sake of a phrase.
- **Type**: Fraunces for display (a warm soft-serif, with its `SOFT` and `WONK` axes
  turned up), Figtree for text.
- **Two themes.** Every colour is a token; light is the default, dark is honoured from
  the OS and overridable by the toggle in the header (stored in `localStorage`).
- **Accessibility**: skip link, visible focus rings, labelled form fields, ARIA on the
  filters/tabs/accordion, and `prefers-reduced-motion` respected throughout.

## Two things to wire up before this goes live

1. **The contact form has no backend.** Submitting composes an email to
   `teamkidwilliamston@gmail.com` in the visitor's mail client. Point it at Formspree,
   Netlify Forms or similar if you want real submissions.
2. **The PayPal handle** is shown as text ("PayPal @TeamKid") rather than a link,
   because the site never gives the URL. Add the real link once you have it.
