# 🧩 UI/UX Design Plan — All-In-One Urban Mobility Platform

## 1. Problem Definition

The modern urban traveler faces a **fragmented mobility experience** — having to switch between multiple apps for bus schedules, ride-hailing, and walking navigation.  
This leads to:
- Inefficient trip planning under multiple constraints (time, cost, distance).  
- Lack of real-time actionable insights (congestion, ETA drift).  
- User frustration and decision fatigue.

🎯 **UI/UX Goal:**  
Design a **unified, intuitive, and responsive interface** that allows users to:
- Plan, book, and monitor their trips end-to-end in one platform.  
- Receive **real-time recommendations** with transparent trade-offs.  
- Experience **safety and clarity** through alert-driven, contextual UI design.

---

## 2. Decomposition

| **Module** | **Description** | **Deliverables** |
|-------------|-----------------|------------------|
| **A. User Research & Persona** | Interview urban commuters & visitors to define pain points and goals. | Persona profiles, user journey map |
| **B. Information Architecture** | Design system flow across pre-trip, in-trip, and alerting modules. | Sitemap, navigation flow diagram |
| **C. Wireframe (Low-Fidelity)** | Build structural layout of screens: trip planner, results, tracking. | Low-fi wireframes |
| **D. Prototype (High-Fidelity)** | Visual design with color system, icons, and dynamic states. | Figma interactive prototype |
| **E. UI Implementation** | Convert Figma design to functional UI using React/Next.js. | Responsive frontend integrated with backend APIs |
| **F. UX Testing & Iteration** | Conduct usability tests, gather feedback, and refine flows. | UX test report & iteration summary |

---

## 3. Solution Design

### **Pre-Trip Planning UI**
- Input start/end locations and preferred transport modes.  
- Show 2 optimized itineraries: **Fastest** and **Normal**, with ETA and cost estimates.  
- Step-based flow: **Plan → Review → Confirm**.  

### **In-Trip Recommender UI**
- Kanban-style recommendation panel: top 3 modes ranked by ETA, cost, and confidence.  
- Dynamic cards update in real-time (via GPS and live APIs).  
- Visual indicators for route quality and delay warnings.

### **Safety & Alerting Module**
- “Corridor Load Index” visualization with color-coded congestion (green, yellow, red).  
- Pop-up alerts for traffic jams or safety concerns.  
- One-tap reroute suggestion.

### **UX Principles**
- **Minimal Effort, Maximum Clarity:** ≤3 taps for major actions.  
- **Accessibility First:** Font ≥14px, high-contrast UI, colorblind-safe palette.  
- **Consistency:** Uniform button styles, iconography, and feedback states.  

---

## 4. Tools & Frameworks

| **Purpose** | **Tools / Frameworks** |
|--------------|------------------------|
| UI Design | Figma, Adobe XD, Illustrator |
| Prototyping | Figma Prototype, Framer, InVision |
| Frontend | React.js, Next.js, Tailwind CSS, shadcn/ui |
| UX Testing | Maze, Hotjar, Google Analytics |
| Collaboration | Notion, Trello, Slack, GitHub |

---

## 5. Timeline (UI/UX Focused)

| **Week** | **Phase** | **Key Activities** | **Deliverables** |
|-----------|------------|--------------------|------------------|
| **Week 1–2** | Research & Persona | Conduct surveys and interviews. Build user journey maps. | Persona profiles & journey map |
| **Week 3** | Information Architecture | Design sitemap & navigation structure. | Sitemap & flow diagram |
| **Week 4–5** | Wireframing | Create low-fidelity layouts for all key screens. | Approved wireframes |
| **Week 6–7** | High-Fidelity Design | Apply colors, icons, branding. Develop Figma prototype. | Clickable prototype |
| **Week 8** | UI Integration | Implement frontend with React/Next.js and connect APIs. | Working UI on staging |
| **Week 9–10** | UX Testing & Refinement | Usability testing, CSAT measurement, improvements. | Final UX v2 + Test Report |
| **Week 11** | Presentation & Launch | Prepare final demo and pitch deck. | Live demo & presentation materials |

---

## 6. Final Deliverables

- 📱 **Figma prototype** (mobile-first, responsive)  
- 🧭 **Navigation flow & component system** (Tailwind-based)  
- 🎨 **Design system** (color palette, typography, icons, states)  
- 🧩 **Functional UI connected to APIs**  
- 📊 **UX testing report & iteration summary**  

---

## 7. Success Metrics (UI/UX Perspective)

| **Metric** | **Target** |
|-------------|------------|
| User Acceptance of Plans | ≥ 60% select top-3 routes |
| CSAT (Planning + In-Trip Guidance) | ≥ 4.2 / 5 |
| App Stability (Crash-Free Sessions) | ≥ 99.5% |
| Response Latency (p95) | ≤ 1.5 seconds |
| Usability Task Success Rate | ≥ 85% during testing |

---

## 8. Contributors (UI/UX Team)

| **Name** | **Role** | **Responsibilities** |
|-----------|-----------|----------------------|
| **Hiếu** | UI/UX Designer | Overall design system, in-trip UI, prototype creation |
| **Khôi** | Frontend Developer | Integrate design with React/Next.js frontend |
| **Đạt** | Backend Support | API integration & data structure alignment for UI |
| **Khoa** | QA / UX Tester | Conduct UX testing, collect metrics & feedback |

---

## 9. Summary

The **UI/UX component** of the All-In-One Urban Mobility Platform focuses on creating a seamless, unified experience that bridges pre-trip planning, real-time navigation, and safety feedback — ensuring that users move through the city **efficiently, confidently, and safely**.

