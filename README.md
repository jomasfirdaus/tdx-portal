# TDx — Timor Diagnostics Website

A full-stack Django + MySQL profile website for **Timor Diagnostics (TDx)**,
built to be secure by default, fast under real traffic, and easy for
non-technical staff to keep up to date in three languages (English, Tetun,
Português) through a purpose-built staff dashboard — **not** Django's
built-in `/admin/`.

---

## 1. What's included

**Public site**
- Home, Profile (About + Governance + Org chart), Vision & Mission
- Programs & Activities (with categories, status, pagination)
- Team & Structure (Board, Leadership, Operational Units — org-chart style)
- News (with search, categories, sanitized rich text)
- Photo Gallery (albums + lightbox)
- Contact page (spam-resistant contact form)
- Full English / Tetun / Português support, switchable per page

**Staff dashboard** (`/dashboard/` by default, configurable)
- Custom-built (no Django admin exposed at all — nothing to fingerprint at `/admin/`)
- Role-based access: Super Admin vs. Content Editor
- CRUD screens for every content type, with English/Tetun/Português tabs
- Contact message inbox
- Login audit log (Super Admin only)
- Staff account management (Super Admin only)

---

## 2. Tech stack

| Layer      | Choice |
|------------|--------|
| Backend    | Django 6.0 (Python 3.12) |
| Database   | MySQL 8 (via `mysqlclient`) |
| Frontend   | Server-rendered Django templates, hand-written CSS (no framework/CDN), vanilla JS |
| Auth       | Custom `AdminUser` model, Argon2 password hashing |
| i18n       | Lightweight custom system (see §6) — no `gettext` system dependency |

No third-party JS/CSS CDNs are used anywhere, intentionally — see §5.

---

## 3. Local setup

```bash
# 1. Clone and enter the project
cd tdx_website

# 2. Create a virtual environment
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
python manage.py generate_secret_key     # paste the output into DJANGO_SECRET_KEY in .env

# 5. Create the MySQL database (run in a MySQL client)
#    CREATE DATABASE tdx_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
#    CREATE USER 'tdx_user'@'localhost' IDENTIFIED BY 'a-strong-password';
#    GRANT ALL PRIVILEGES ON tdx_db.* TO 'tdx_user'@'localhost';
#    FLUSH PRIVILEGES;
#    Then fill in DB_NAME / DB_USER / DB_PASSWORD in .env to match.

# 6. Migrate & seed TDx's real profile content
python manage.py migrate
python manage.py seed_tdx

# 7. Create your first Super Admin account
python manage.py createsuperuser
#    then, in the shell, promote them:
python manage.py shell -c "
from accounts.models import AdminUser
u = AdminUser.objects.get(username='YOUR_USERNAME')
u.role = 'superadmin'; u.is_superuser = True; u.is_staff = True; u.save()
"

# 8. Run it
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` for the public site and
`http://127.0.0.1:8000/dashboard/` for the staff dashboard.

> **Local testing without MySQL:** set `DB_ENGINE=sqlite` in `.env` to run
> against a local SQLite file instead. Production should always use
> `DB_ENGINE=mysql` (the default).

### First things to edit in the dashboard
1. **Site Profile** — logo, tagline, About text, Vision/Mission, phone/email/address, social links, Google Maps embed URL.
2. **Team & Structure → Team Members** — the seed data intentionally does **not** invent board members or staff names (the source profile document didn't name individuals); add real people here.
3. Review the **Tetun** and **Português** columns on every seeded item — they're a solid first draft, but a native-speaker review before launch is strongly recommended for a health-sector organization.

---

## 4. Project layout

```
config/         Django settings, root urls, wsgi/asgi
core/           SiteProfile, Services, Core Values, Statistics, shared i18n/middleware
accounts/       Custom staff user model, login/logout, password change, audit log model
structure/      Departments (org chart) & Team Members
programs/       Programs & Activities
news/           News posts & categories (HTML sanitized with bleach)
gallery/        Albums & Photos
contact/        Contact form + stored messages
dashboard/      The custom staff admin (generic CRUD factory + hand-written views)
templates/      All HTML templates (public/, dashboard/, accounts/, partials/)
static/         Hand-written CSS, vanilla JS, icons — no external CDN
```

### The dashboard's generic CRUD factory
Most content types (Services, Values, Statistics, Departments, Team Members,
Program/News categories & posts, Albums, Photos, Staff accounts) are wired up
through `dashboard/crud.py::build_crud_views()`, which generates a
List/Create/Update/Delete view set per model. This keeps ~12 content types
from needing hand-written boilerplate while still going through the same
access control, CSRF protection, and pagination as a hand-written view.

---

## 5. Security measures

- **No Django admin exposed.** `django.contrib.admin` is not in
  `INSTALLED_APPS` at all — there's no `/admin/` surface to probe or
  brute-force. Staff manage content through the custom dashboard only.
- **Custom staff auth**: Argon2 password hashing, a custom complexity
  validator (upper/lower/digit/symbol, 10+ chars), per-IP+username login
  throttling with temporary lockout, session rotation on login, and a
  `LoginActivity` audit trail reviewable by Super Admins.
- **CSRF protection** on every form (Django's CSRF middleware + `{% csrf_token %}` everywhere).
- **SQL injection**: 100% Django ORM, parameterized queries throughout — no raw SQL anywhere in the codebase.
- **XSS**: Django's auto-escaping templates by default; the one place rich HTML is allowed (News post body) is sanitized server-side with `bleach` against a strict tag/attribute allow-list before it's ever saved, and only that pre-sanitized field is rendered with `|safe`-equivalent output.
- **File upload hardening**: extension allow-list + size cap enforced both in Django's `ImageField` and again in form-level validation, for every image field across the whole dashboard.
- **Security headers**: a strict `Content-Security-Policy` (script-src/style-src/font-src all `'self'`), `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy`, HSTS (production), secure/HttpOnly/SameSite cookies.
- **Contact form spam resistance**: honeypot field, a render-timestamp "time trap" (rejects near-instant scripted submissions), and per-IP rate limiting — no external CAPTCHA service/CDN required.
- **Environment-based secrets**: nothing sensitive is hard-coded; `DJANGO_SECRET_KEY` is required and the app refuses to start with `DEBUG=False` and no key set.
- **Least-privilege dashboard roles**: Content Editors can manage all content; only Super Admins can manage staff accounts or view the login audit log.

Before going live, also:
- Set `DJANGO_DEBUG=False` and fill in a real `DJANGO_SECRET_KEY`.
- Serve over HTTPS and set `DJANGO_SECURE_SSL_REDIRECT=True`, `DJANGO_SESSION_COOKIE_SECURE=True`, `DJANGO_CSRF_COOKIE_SECURE=True`.
- Put the app behind a real WSGI server (gunicorn/uwsgi) + reverse proxy (nginx), not `runserver`.
- Consider changing `DASHBOARD_URL_PREFIX` in `.env` away from the default `dashboard` for a little extra obscurity (not a substitute for the access controls above, but it does stop generic bots that only probe `/admin/` and `/wp-admin/`).

---

## 6. How translation works (English / Tetun / Português)

Two different mechanisms are used deliberately:

1. **Dynamic content** (Profile, Programs, News, Team, Gallery captions, etc.)
   stores one column per language directly on the model —
   `title_en` / `title_tet` / `title_pt`. The dashboard renders these as
   language tabs on every content form. Only English is required; if a
   Tetun or Português column is left blank, the public site automatically
   falls back to English for that field (see `core/translation.py::tr()`).

2. **Static UI strings** (menu items, buttons, labels) live in a small
   Python dictionary at `core/i18n.py`. This project deliberately does
   **not** use Django's built-in `gettext`-based `USE_I18N` system — with
   almost all real content in the database already, gettext would just add
   a system dependency (the `gettext` binary + `.po`/`.mo` compilation) for
   a handful of strings. Add a new UI string by adding one line to
   `core/i18n.py::STRINGS` and calling `{% t "your.key" %}` in a template.

The active language is resolved by `core/middleware.py::LanguageMiddleware`
from `?lang=`, then the session, then a cookie, defaulting to English — no
page reload framework needed, just `?lang=tet` / `?lang=pt` links (see the
language switcher in the navbar).

---

## 7. Performance / query optimization notes

- Every list view uses `select_related`/`prefetch_related` where a foreign
  key or reverse relation is displayed, to avoid N+1 queries (see
  `programs/models.py::PublishedProgramManager`, `news/models.py::PublishedNewsManager`, etc.).
- Indexes are defined directly on the models for every field used in a
  `filter()`/`order_by()` in the views (`is_published`, `slug`, `category`,
  `published_at`, etc.) — see each app's `Meta.indexes`.
- The homepage aggregates several small queries behind a single short-lived
  cache key (`core/views.py::home`), so repeat visits don't re-hit MySQL for
  content that rarely changes; the cache is explicitly invalidated when the
  Site Profile is saved from the dashboard.
- Pagination (`Paginator`) is used on every list page instead of loading
  full tables.
- `CONN_MAX_AGE` + `CONN_HEALTH_CHECKS` keep MySQL connections warm across
  requests instead of reconnecting every time.
- News view counts are incremented with an atomic `F()` expression update
  instead of a read-modify-write round trip.

For heavier production traffic, swap `CACHE_BACKEND=locmem` for
`CACHE_BACKEND=redis` in `.env` (Redis client is already listed, commented
out, in `requirements.txt`).

---

## 8. Deployment checklist

1. `pip install -r requirements.txt` (uncomment `gunicorn`/`whitenoise`).
2. `.env` with production values (see `.env.example`).
3. `python manage.py migrate`
4. `python manage.py seed_tdx` (safe to re-run; only touches TDx's own profile/services/values/structure records)
5. `python manage.py collectstatic`
6. Run behind gunicorn/uwsgi + nginx (or your platform's equivalent), with HTTPS termination.
7. Point `DB_HOST`/`DB_USER`/`DB_PASSWORD` at your managed MySQL instance.
8. Set up a real e-mail backend for contact-form notifications (`EMAIL_*` vars).

---

## 9. Content the seed script does *not* invent

`python manage.py seed_tdx` loads TDx's actual Profile, Vision, Mission,
Services & Expertise, Core Values, and organizational structure (Board →
Managing Director → Finance / Logistics & Admin / Technical Core → Testing /
Phlebotomy / Wellbeing & Care units) from the reference profile document.

It deliberately leaves **Team Members, Programs, News, and Gallery empty** —
the source document didn't name specific people, so real staff names,
photos, and bios should be added by TDx through the dashboard rather than
invented here.
