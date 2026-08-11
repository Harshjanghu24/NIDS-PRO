# ADR-005: Selection of React + TypeScript for Presentation Dashboard

**Status:** Approved  
**Date:** 2026-08-04  
**Deciders:** Senior Frontend Engineer, Principal Software Architect  

---

## 1. Problem Statement
Version 1.0 used server-rendered Jinja2 HTML templates in Flask. To deliver an enterprise-grade Security Operations Center (SOC) dashboard, Version 2.0 requires real-time telemetry streaming, interactive chart filtering, dark-mode styling, and client-side state management without triggering full web page reloads.

## 2. Decision
Build a Single-Page Application (SPA) using **React 18**, **TypeScript**, **Tailwind CSS**, and **Chart.js**.

## 3. Alternatives Considered
- **Jinja2 + Tailwind (Retained V1.0)**: Low setup overhead, but requires full page reloads or complex manual DOM manipulation via vanilla JavaScript for WebSockets.
- **Vue.js**: Excellent framework, but React has a larger component ecosystem for security dashboards and stronger TypeScript integration patterns.
- **Next.js (SSR)**: Great for public SEO web apps, but adds server-side rendering complexity unnecessary for an internal authenticated single-page SOC dashboard.

## 4. Consequences & Impact
- **Positive**: Rich visual design, modular reusable UI component architecture, client-side type safety with TypeScript, fast canvas chart re-rendering.
- **Negative**: Requires separate build pipeline (`Vite` / `npm`) and NGINX configuration for serving static bundle files.

## 5. Tradeoffs & Risk Mitigation
- *Risk*: High-frequency WebSocket alert pushes cause excessive React component re-renders.
- *Mitigation*: Utilize `React.memo`, virtualized lists for alert tables, and throttled state updates (1000ms render window).
