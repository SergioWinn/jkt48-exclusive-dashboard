---
name: Global Exclusive Monitor
description: 'Release Grid: cool navy, cyan selection, and clear vertical member tickets.'
colors:
  band: '#153947'
  band-ink: '#f4fbff'
  highlight: '#8de8ef'
  highlight-ink: '#123645'
  brand-blue: '#166ee5'
  paper: 'light-dark(#f4fbff, #101c25)'
  paper-2: 'light-dark(#eaf1f6, #182934)'
  paper-3: 'light-dark(#dce8ef, #233d4b)'
  ink: 'light-dark(#152f3e, #edf7fc)'
  ink-2: 'light-dark(#365263, #c6dce8)'
  muted: 'light-dark(#546d7c, #a5c1d0)'
  rule: 'light-dark(#ccdae4, #3d5767)'
  rule-strong: 'light-dark(#7c97a9, #7799ac)'
  accent: 'light-dark(#11617b, #8de8ef)'
  accent-strong: 'light-dark(#0c465c, #b6f2f6)'
  accent-ink: 'light-dark(#f4fbff, #123645)'
  focus: 'light-dark(#11617b, #b6f2f6)'
  success: light-dark(oklch(56% 0.15 155), oklch(66% 0.13 155))
  success-soft: light-dark(oklch(94% 0.035 155), oklch(25% 0.045 155))
  success-ink: light-dark(oklch(14% 0.045 155), oklch(92% 0.01 155))
  warning: light-dark(oklch(78% 0.15 82), oklch(74% 0.13 82))
  warning-soft: light-dark(oklch(95% 0.035 82), oklch(26% 0.045 82))
  warning-ink: light-dark(oklch(25% 0.045 82), oklch(92% 0.012 82))
  status-warning-ink: oklch(20% 0.04 82)
  danger: oklch(52% 0.19 25)
  danger-soft: light-dark(oklch(94% 0.035 25), oklch(25% 0.05 25))
  danger-text: light-dark(oklch(38% 0.15 25), oklch(84% 0.09 25))
  danger-ink: oklch(98% 0.006 25)
  closed: oklch(42% 0.018 256)
  graphite: '#182934'
  graphite-2: '#233d4b'
  graphite-ink: '#edf7fc'
  graphite-muted: '#a5c1d0'
  overlay: oklch(16% 0.025 230 / 0.64)
  shadow: light-dark(oklch(24% 0.035 230 / 0.1), oklch(5% 0.01 230 / 0.36))
  surface: 'light-dark(#ffffff, #1b303d)'
typography:
  headline:
    fontFamily: Archivo, sans-serif
    fontSize: clamp(1.65rem, 3vw, 2.25rem)
    fontWeight: 600
    lineHeight: 1.08
    letterSpacing: -0.03em
  title:
    fontFamily: Archivo, sans-serif
    fontSize: 1.25rem
    fontWeight: 600
    lineHeight: 1.4
  member:
    fontFamily: Archivo, sans-serif
    fontSize: 0.875rem
    fontWeight: 600
    lineHeight: 1.3
  body:
    fontFamily: Public Sans, sans-serif
    fontSize: 1rem
  label:
    fontFamily: Public Sans, sans-serif
    fontSize: 0.75rem
    fontWeight: 600
    letterSpacing: 0.06em
  source:
    fontFamily: IBM Plex Mono, monospace
    fontSize: 0.75rem
    letterSpacing: 0.06em
  metric:
    fontFamily: Archivo, sans-serif
    fontSize: clamp(1.953rem, 2.5vw, 2.441rem)
    fontWeight: 600
    lineHeight: 1.08
rounded:
  input: 6px
  card: 8px
  pill: 999px
  circle: 50%
spacing:
  3xs: 0.125rem
  2xs: 0.25rem
  xs: 0.5rem
  sm: 0.75rem
  md: 1rem
  lg: 1.5rem
  xl: 2.5rem
  2xl: 4rem
components:
  support-button:
    backgroundColor: transparent
    textColor: '{colors.band-ink}'
    rounded: '{rounded.input}'
    height: 44px
    padding: 0 0.5rem
  member-card:
    backgroundColor: '{colors.surface}'
    rounded: '{rounded.card}'
    padding: '{spacing.sm}'
  member-card-closed:
    backgroundColor: '{colors.paper-2}'
    rounded: '{rounded.card}'
    padding: '{spacing.sm}'
  search-field:
    backgroundColor: '{colors.paper}'
    textColor: '{colors.ink}'
    rounded: '{rounded.input}'
    height: 44px
  date-selected:
    textColor: '{colors.accent-strong}'
    height: 44px
    padding: 0 0.5rem
  source-live:
    backgroundColor: '{colors.success-soft}'
    textColor: '{colors.success-ink}'
    rounded: '{rounded.input}'
    padding: 0.5rem 0.75rem
    typography: '{typography.source}'
  statistics-tab-selected:
    backgroundColor: '{colors.accent}'
    textColor: '{colors.accent-ink}'
    rounded: '{rounded.input}'
    height: 44px
    padding: 0.5rem 0.75rem
  roster-chip:
    backgroundColor: '{colors.graphite}'
    textColor: '{colors.graphite-ink}'
    rounded: '{rounded.pill}'
    padding: 4px 8px 4px 4px
---

# Design System: Global Exclusive Monitor

## Overview

**Creative North Star: "Release Grid"**

Release Grid uses a cool navy masthead, blue-white reading surfaces, and cyan selection to keep event choice and member availability clear. Portraits, aligned identity blocks, and explicit written states make compact tickets easy to compare. The existing product name and ticket logo remain the identity anchors.

The system is flat and practical. Public Sans carries reading and controls, Archivo gives event and session headings a compact voice, and IBM Plex Mono distinguishes the source readout. Native controls retain keyboard behavior, short feedback respects reduced motion, and the dark scheme keeps the same cool palette.

**Key Characteristics:**
- Cool navy framing with restrained cyan selection.
- Compact vertical tickets with circular portraits and aligned availability blocks.
- Written availability and compact source status.
- Flat bordered surfaces, visible focus, and responsive native controls.

## Colors

Cool navy frames a blue-white reading field; cyan marks selection. Source tokens preserve their `light-dark()` and OKLCH forms, with the light/dark app configuration following the same paper and ink values.

### Primary
- **Deep navy band:** masthead background with pale band ink.
- **Clear cyan highlight:** cool accent vocabulary; date choices stay transparent with a thin accent underline.
- **Ocean accent:** controls and primary actions, becoming cyan in the dark scheme.

### Secondary
- **Availability green, low-stock amber, unavailable red, and closed slate:** functional status colors with explicit written labels and dedicated contrast pairs.
- **Brand blue:** the retained ticket logo detail.

### Neutral
- **Blue-white paper:** page and field background; paper steps separate closed tickets and secondary surfaces.
- **Navy ink and slate:** primary, secondary, and muted reading text.
- **Cool rules:** regular dividers and stronger control boundaries.
- **Blue graphite:** statistics/share dialogs and their pale text.
- **White surface:** open member tickets, adapting to deep blue in the dark scheme.

**The Written State Rule.** Pair status color with explicit status text; a closed ticket reads CLOSED without historical quantities.

**The Selection Rule.** Keep selected dates transparent; use a 2px accent underline, a strong accent foreground, and the native radio marker. Preserve the 44px target.

## Typography

**Display Font:** Archivo, with sans-serif fallback.
**Body Font:** Public Sans, with sans-serif fallback.
**Label/Mono Font:** IBM Plex Mono, with monospace fallback, for source state and update time.

**Character:** Compact headings and clear reading text; the masthead uses the body face, while event, session, and member identity use Archivo. Exact role values are in the frontmatter.

### Hierarchy
- **Headline:** responsive event heading with balanced wrapping and tight tracking.
- **Title:** plain session heading with a smaller Public Sans time alongside it.
- **Member:** compact centered name, allowing long names to wrap.
- **Body:** native reading/control scale; smaller supporting copy uses the source small scale.
- **Label:** compact metadata and field labels; source status uses mono, with normal-case timestamps.
- **Metric:** tabular statistics; revenue uses a smaller responsive size.

The masthead uses `clamp(1.1rem, 2vw, 1.5rem)`, weight 700, line-height 1.15; below 40rem it becomes 1rem. Native text inputs, textareas, selects, and share selection use at least 1rem through 48rem. The unused display-size token is not a heading prescription.

## Layout

The application container stops at 1480px. Inline gutters interpolate from 1rem to 2.5rem and respect safe areas. The observed spacing scale runs from 0.125rem adjustments to 4rem footer separation; ordinary component gaps use the middle steps.

The reference-led surface follows masthead, shared filters, event/source heading, date rail, and session-grouped member cards. Desktop filters use four tracks; below 64rem they form two columns. Event heading and source status share a row from 64rem; on smaller screens the compact source readout follows the title. Date options scroll horizontally below 40rem, then wrap.

Member cards form two columns on phones, three from 40rem, four from 64rem, and six from 80rem. Each vertical card has a minimum height of 218px, 64px circular portrait, lane metadata, wrapping member identity, and an availability block aligned at the bottom. Minimum height never clips content. Statistics remain secondary after tickets; their summary grid changes from one to two to five columns. Footer alignment changes at 48rem.

Share capture remains a separate fixed 1080px canvas with seven member columns, 56px portraits, and a 190px card minimum; sparse available-only groups can use three columns. These export proportions do not govern the responsive interface. Synthetic review content is not product content or a design rule.

## Elevation & Depth

Surfaces are flat: fine borders, cool tonal steps, and the navy masthead establish hierarchy. Floating actions and dialogs use a small ambient shadow (`0 1px 2px` with the appropriate shadow token); modal backdrops dim the page.

**The Quiet Surface Rule.** Use borders and tonal contrast for ticket depth; reserve small ambient shadows for floating actions and dialogs.

Pointer hover lifts a purchase ticket by 1px, active feedback lowers it by 1px, and focus remains explicit. Micro feedback lasts 100ms; short status/support feedback uses 180ms and the shared ease-out curve. Reduced-motion rules remove practical animation.

## Shapes

Controls use gently rounded input corners; cards, the masthead, and dialogs use the slightly larger card corners. Portraits and floating action buttons are circular, while roster chips are pills. Regular boundaries are 1px; focus uses distinct 2px or 3px outlines with an offset. Preserve the ticket logo's notch/star geometry.

## Components

### Buttons

The masthead support link is transparent and outlined on navy, with a 44px minimum target and visible focus. Statistics/share actions are round 48px buttons with SVG icons. Dialog actions retain written loading, success, blocked, and error feedback.

### Chips

Statistics roster pills combine a small circular portrait and member name on the dialog background. They identify roster membership rather than acting as filters.

### Cards / Containers

Vertical bordered member tickets keep lane, circular portrait, centered name, quantities, and availability in a consistent order. Available tickets link to the existing purchase destination; sold-out and closed cards are non-links. Closed cards use the second paper tone and show CLOSED without quantities. Sold/closed portraits are grayscale and dimmed; missing portraits use initials. The availability track is a visual progress/status element within the card, not a separate action.

### Inputs / Fields

Search and selects use paper backgrounds, stronger cool boundaries, input corners, and 44px minimum heights. Hover moves to the next paper tone, focus adds a 2px outline, and disabled fields retain their shape at reduced opacity. The shared filter bar uses native controls.

### Navigation

Dates remain native radio choices: selected dates use a thin accent underline and a strong accent foreground, including nested label text, without a filled background. Statistics tabs use muted transparent labels and a filled accent for selection, with 44px minimum heights, keyboard navigation, and explicit focus. These are local navigation patterns.

### Session Heading

A plain Archivo heading, small muted Public Sans time, and fine bottom rule separate sessions. Member cards carry the detail; session headings do not repeat the heavy masthead treatment.

### Source Readout

A compact bordered mono readout combines written source state and update time. Live uses green, saved/partial/closed uses amber, and unavailable uses red. Long timestamps wrap without widening the page.

## Do's and Don'ts

### Do:
- Do preserve the existing product name and ticket logo.
- Do pair availability color with a written state and keep CLOSED free of quantities.
- Do retain circular portraits, vertical ticket identity, and aligned availability blocks.
- Do preserve visible focus, comfortable touch targets, and reduced-motion behavior.

### Don't:
- Don't replace the Public Sans and Archivo pairing with a system display face.
- Don't rely on color alone to convey availability.
- Don't turn compact source status into a dominant banner.
- Don't inherit fixed export proportions as interactive layout rules.

Not canonized or repaired: inherited statistics-image export CSS still uses literal cool-blue colors, spacing, and type sizes rather than the shared token scale; it is a separate pre-existing export path, not a rule for new surfaces.
