---
name: iis-website
description: Plan, build, and maintain the official website of the Institute of Islamic Studies Daharki (and its affiliated madaris network), and coach the non-technical administrator step by step through domain purchase, hosting, and publishing. Use for anything about the website, domain, hosting, email addresses, or online donation/admission pages.
---

# IIS Daharki — Website

## Decisions (recommended defaults — confirm with the user)
- **Same repository**: website lives in `website/` in this repo, so it reads the same facts as videos and documents (`institute/*.md`, `brand/brand.json`). No separate copy of information.
- **Type**: fast static site (plain HTML/CSS or Astro), bilingual — Urdu (RTL, Noto Nastaliq from `brand/fonts`) as primary, English secondary. Mobile-first: most visitors come from Facebook/WhatsApp on phones.
- **Hosting**: free static hosting (Cloudflare Pages or GitHub Pages) deployed from this repo → zero monthly cost, no server to maintain.
- **Domain**: `.org` is the convention for non-profit/educational bodies (e.g. `iisdaharki.org`); alternative `.edu.pk` only if the institute qualifies via HEC-recognised affiliation, or `.org.pk` via PKNIC. Check availability before the user pays. Prices change — verify on the registrar's site at purchase time.
- **Email**: free forwarding (e.g. Cloudflare Email Routing) `info@<domain>` → the administrator's Gmail.

## Coaching the user (they are not technical)
Explain one step at a time, in their language, with what to click and what to send back. Never ask for passwords; the user enters credentials themselves.
1. Pick 2–3 domain name options → you check availability.
2. User creates a registrar account (Cloudflare Registrar or Namecheap; PKNIC for .pk) and buys the domain with their card. Enable auto-renew; record renewal date in `institute/tasks.md`.
3. User creates a Cloudflare account (free) and connects this GitHub repo to Cloudflare Pages (build output: `website/dist` or `website/`).
4. Point the domain to Pages; set up email forwarding.
5. You build and push; every push to the main branch updates the site.

## Content needed (collect into `institute/profile.md` / `affiliates.md` / `events.md`)
- Logo, colours, 10–20 good photos (building, classes, events — consent and adab in mind)
- تعارف (introduction), mission, history, founder/patrons
- Leadership & teachers (names with exact titles, photos optional)
- Departments & programs: duration, eligibility, fee, admission dates
- Affiliated madaris/makatib: name, location, in-charge, contact
- Projects & donation needs; verified bank details (shown only after user confirmation)
- Contact: address, Google Maps pin, phone/WhatsApp, Facebook/YouTube links
- Downloadable admission form, prospectus (PDF)

## Site map
Home · تعارف/About · شعبہ جات/Programs · داخلہ/Admissions · ہمارے ادارے/Our Network · منصوبے و تعاون/Projects & Support · ویڈیوز/Media (embed Facebook/YouTube) · خبریں و اعلانات/News · رابطہ/Contact

## Build standards
- Semantic HTML, `lang="ur" dir="rtl"` for Urdu pages; WCAG-readable contrast; images compressed (WebP); works on slow mobile data.
- Generate pages from `institute/*.md` data where practical so updates happen in one place.
- No tracking scripts beyond simple privacy-friendly analytics (Cloudflare Web Analytics).
- Test locally (open the built HTML with the browser/Playwright, check phone width 375 px) before pushing.
