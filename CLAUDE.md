# CLAUDE.md

## Project Overview

**Auslex** is a modern legal reference platform, designed for clarity, accessibility, and trust. The project is structured as a full-stack web application with a React frontend and a FastAPI backend, containerized via Docker Compose for local development.

---

## Design & UX Principles

- **Atomic Consistency:** All UI elements use atomic design tokens for color, spacing (8px grid), typography, border radius (6–10px), and shadows.
- **Color Palette:** Core muted palette with deep/jet black surfaces (`#0D0D0D`, `#1C1C1C`), borders (`#3C3C3C`, `#CBAE88`), and ochre/gold accents (`#CE9A54`, `#C9A063`) for focus rings, lines, and icon highlights.
- **Typography:** Major-third type scale (H1 2.4rem, H2 1.92rem, H3 1.536rem, body 1rem), 60–75 characters per line, no all-caps in body text.
- **Icons:** Single minimal line-based icon set (1–1.5× text height), thin monochrome or `#C9A063`.
- **Buttons:** 
  - Primary: Jet black fill, ochre/pale copper text, slim ochre border.
  - Secondary: Transparent with `#CBAE88` border.
- **Microinteractions:** Simple fades (120–150ms), instant form feedback, subtle fade/slide reveals.
- **Layout:** Max content width 1120px, left sidebar on desktop, primary actions bottom-right, extra whitespace on desktop, mobile tap targets ≥44×44px.
- **Cards & Surfaces:** Standardized card sizes, modest border-radius, minimal shadows, pale-copper outlined trust badges.
- **Empty States:** Graceful, with clear action prompts.
- **Text:** Helper text is semibold muted gray at 85% size; action labels are precise and verb-led; headings are verb-led.
- **Serif fonts:** Reserved for citations only.

---

## Backend & Database

- **API:** FastAPI (see `backend/requirements.txt` for dependencies).
- **Database:** All SQL/PostgreSQL queries must explicitly schema-qualify tables (e.g., `auslex.legal_snippets`). Do **not** rely on `search_path`.
- **Schema:** Dedicated schema named `auslex`, owned by `app_writer`.
- **Production Branch:** Neon production branch is named `production` (not `main`).

---

## Development

- **Local Setup:** Use `docker-compose.yml` to run both frontend and backend.
- **Environment Variables:** Place secrets (e.g., `OPENAI_API_KEY`) in a local `.env` file (see `.gitignore` for exclusions).
- **Frontend:** Connects to backend at `http://localhost:8000` (see `REACT_APP_API_ENDPOINT`).
- **Backend:** Runs on Python 3.9, serves via Uvicorn.

---

## Contribution Guidelines

- **UI Consistency:** Adhere strictly to design tokens and spacing rules.
- **SQL:** Always schema-qualify table names (`auslex.*`).
- **Accessibility:** Ensure all interactive elements are accessible and have sufficient contrast.
- **Code Style:** Follow project linting and formatting rules.
- **Documentation:** Update this file with any major design or architectural changes.

---
