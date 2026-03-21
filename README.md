# Danny's Training Plan

A Progressive Web App (PWA) for an 8-week body recomposition cycling training plan.

## Features

- **8-Week Structured Training Plan** with expandable week cards and workout detail modals
- **Zwift .zwo Export** — generate valid Zwift workout files for any session
- **Nutrition Tracking** — 7-day meal plan with macro breakdown and compliance toggles
- **Progress Dashboard** — completion rings, streak counter, and compliance charts
- **Live Calorie Calculator** — global and per-week deficit sliders that update macros in real time
- **GitHub Gist Sync** — persist data across devices via a private Gist
- **Fully Offline** — service worker caches all assets after first load
- **Installable PWA** — add to home screen on iOS and Android

## Setup

1. Open `index.html` in a browser (or serve from a local server)
2. Install to home screen for the full standalone experience
3. Optionally add a GitHub Personal Access Token in Settings for cross-device sync

## Tech Stack

- Vanilla JS, HTML, CSS — zero build step
- Chart.js 4.4 (CDN)
- Inter font (Google Fonts)
- Service Worker for offline support

## Live

Hosted at: `https://[your-username].github.io/training-plan/`
