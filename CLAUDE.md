# CLAUDE.md — BaseMod LandOS Project Memory

## Project identity
You are working on **BaseMod LandOS — Event Mesh** ("Land Swarm").

LandOS is the operating system that turns fragmented land supply into attainable homeownership inventory by mapping signals, waking the right agents, packaging homes that fit, and routing the market toward transaction.

## Non-negotiable architectural truths
1. LandOS is an event mesh, not a pipeline.
2. The moat is the wake-up logic.
3. Listings, clusters, and municipalities are co-equal trigger families.
4. Municipalities are first-class active objects, not passive metadata.
5. Historical stallouts and site condos are strategic supply wedges.
6. Packaging is a first-class system layer.
7. File-based memory is the source of truth, not chat memory.
8. Major changes must update the handoff and decisions log.

## BaseMod NEXUS — Frontend Design System

The frontend app (agents.basemodhomes.com) is called **BaseMod NEXUS**. It is a React + Vite + Tailwind CSS application.

### Design North Star: "The Architectural Archivist"
Warm, confident, institutional. Between Apple's restraint and a premium fintech platform. No explicit borders for sectioning — use background color shifts (tonal layering). No dark mode. No gradients except the signature copper micro-gradient on CTAs.

### Color Tokens (M3 Tonal Palette)
- Primary Copper: `#7f5313` | Primary Container: `#9b6b2a`
- Surface (base): `#fbf9f6` | Card White: `#ffffff` | Surface Low: `#f5f3f0`
- Text Primary: `#1b1c1a` | Text Secondary: `#504539`
- Outline: `#827567` | Outline Variant: `#d4c4b4`
- Copper Gradient: `linear-gradient(155deg, #7f5313, #9b6b2a)`
- Ambient Shadow: `0 12px 32px rgba(27, 28, 26, 0.04)`

### Typography
Font: Inter. Labels: uppercase, tracking-widest, font-bold, text-[10px]. Body: text-on-surface-variant (#504539), leading-relaxed.

### Key Patterns
- Active nav: `border-l-[3px] border-primary text-primary bg-primary/5 font-semibold`
- Cards: white bg, rounded-xl (0.75rem), padding 1.75-2.25rem, no border lines
- Primary buttons: copper-gradient, white text, rounded-lg
- Ghost border (when needed): `outline: 1px solid rgba(212, 196, 180, 0.2)`
- Icons: Lucide React (NOT Material Symbols)

### Reference Files
- `stitch-designs/nexus_core/DESIGN.md` — full design system spec
- `stitch-designs/[screen_name]/code.html` — source HTML for each screen
- `stitch-designs/[screen_name]/screen.png` — visual reference for each screen
- `NEXUS_CLAUDE_CODE_PROMPTS.md` — sequenced build prompts
- `basemod-brand/SKILL.md` — brand identity rules
- `AGENTS_PRODUCT_SPEC.md` — full product specification
