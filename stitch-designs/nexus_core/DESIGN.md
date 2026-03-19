```markdown
# Design System Specification

## 1. Overview & Creative North Star

### Creative North Star: "The Architectural Archivist"
This design system rejects the "flatness" of modern SaaS in favor of a digital environment that feels physical, permanent, and premium. It balances the high-velocity data density of platforms like Vercel with the quiet, intentional restraint of high-end editorial design. 

We achieve an "Institutional" feel not through heavy borders or dark colors, but through extreme typographic precision and a "Warm Minimalist" palette. The goal is to move away from generic "templates" and toward a bespoke interface that feels curated and human. By utilizing tonal layering and generous whitespace, we create a high-density environment that remains legible and calm under pressure.

---

## 2. Colors & Surface Philosophy

Our palette is rooted in a warm, sophisticated "Copper" and a range of "Warm Whites." These are not just colors; they are materials.

### The Color Tokens
- **Primary (Copper):** `primary: #7f5313` | `primary-container: #9b6b2a` 
- **Neutrals:** `on-surface: #1b1c1a` (High emphasis) | `on-surface-variant: #504539` (Medium emphasis)
- **Backgrounds:** `surface: #fbf9f6` (The base) | `surface-container-lowest: #ffffff` (The active card)

### The "No-Line" Rule
Standard UI relies on `1px` solid borders to separate content. **In this system, explicit borders are prohibited for sectioning.** Boundaries must be defined through background color shifts. To separate a sidebar from a content area, or a section from a page, use a shift from `surface` to `surface-container-low`.

### Surface Hierarchy & Nesting
Treat the UI as a series of stacked sheets of fine paper. 
- **Level 0 (Base):** `surface` (#fbf9f6)
- **Level 1 (Sections):** `surface-container-low` (#f5f3f0)
- **Level 2 (Active Elements/Cards):** `surface-container-lowest` (#ffffff)
- **Level 3 (Elevated Overlays):** Use `surface-bright` with a 4% ambient shadow.

### Signature Textures
While the system avoids loud gradients, use **"Micro-Gradients"** on Primary CTAs. A subtle transition from `primary` (#7f5313) to `primary-container` (#9b6b2a) at a 155° angle provides a "die-cast" metallic feel that flat colors cannot replicate.

---

## 3. Typography

The typography is the backbone of the "Institutional" personality. We use **Inter** but apply it with editorial intent—heavy contrast between display sizes and body copy.

- **Display (The Statement):** `display-lg` (3.5rem) or `display-md` (2.75rem). Use sparingly for dashboard welcomes or empty states. 
- **Headlines (The Anchor):** `headline-sm` (1.5rem) at Weight 700. These are the primary anchors for page sections.
- **Body (The Workhorse):** `body-lg` (1rem / 16px). We prioritize readability with a `1.6` leading. All body text uses `on-surface-variant` (#504539) to reduce harsh contrast and feel more "human."
- **Labels (The Data):** `label-md` (0.75rem). Used for metadata, table headers, and overlines. Always in all-caps with +0.05em letter spacing for an authoritative, "stamped" look.

---

## 4. Elevation & Depth

### The Layering Principle
Depth is achieved through **Tonal Layering** rather than structural lines. A card does not sit "on" a page; it is a higher-tier surface nested within it. 
*   **Example:** A `surface-container-lowest` (#ffffff) card sitting on a `surface-container-low` (#f5f3f0) background creates a natural, soft lift.

### Ambient Shadows
When an element must "float" (e.g., a dropdown or a modal), use an **Ambient Shadow**:
- `box-shadow: 0 12px 32px rgba(27, 28, 26, 0.04);`
- The shadow color is a low-opacity version of `on-surface`, never pure black.

### The "Ghost Border"
If a border is required for accessibility (e.g., in a high-density data table), use a **Ghost Border**: `outline-variant` (#d4c4b4) at 20% opacity. 

---

## 5. Components

### Buttons
- **Primary:** `primary` background, `on-primary` text. `8px (0.5rem)` radius. For an extra premium feel, apply the Micro-Gradient mentioned in Section 2.
- **Secondary:** Text-only using `primary` color. No background. Focus is indicated by a subtle `surface-container` highlight.
- **Tertiary:** `label-md` styling. Used for low-priority utility actions.

### Cards
Cards must be `surface-container-lowest` (#FFFFFF). 
- **Radius:** `1.0rem` (lg). 
- **Padding:** `1.75rem` (8) to `2.25rem` (10) for internal breathing room. 
- **Constraint:** Never use a divider line inside a card. Use `1.3rem` (6) of vertical whitespace to separate sections.

### Inputs
- **Shape:** Pill-shaped (`full` radius).
- **Surface:** `surface-container-lowest` (#FFFFFF) with a `px` Ghost Border.
- **State:** On focus, the border transitions to `primary` (#7f5313) at 40% opacity.

### Navigation (The Sidebar)
The sidebar uses `surface-container-lowest` (#FFFFFF). 
- **Active State:** Instead of a blocky highlight, use a `3px` vertical "Copper" line on the far left and transition the text weight to Semibold.
- **Spacing:** Use `spacing-4` (0.9rem) between nav items to maintain high density without clutter.

---

## 6. Do’s and Don'ts

### Do
- **Do** use `surface-container` shifts to define layout regions.
- **Do** lean into white space. If an interface feels "crowded," increase the padding to `spacing-16` (3.5rem) before removing data.
- **Do** use the `Copper` primary color as a surgical tool for emphasis, not a paint bucket.

### Don't
- **Don't** use 100% opaque, high-contrast borders (e.g., #000000).
- **Don't** use standard "Drop Shadows" with high opacity or small blurs.
- **Don't** introduce dark mode. This system is designed for the clarity and warmth of a well-lit architectural space.
- **Don't** use divider lines (`<hr>`). Separate content with Tonal Layering or vertical space.