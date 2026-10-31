---
name: BluPe × EmbodiedEvo
description: Forest navigation and a quiet, inspectable research workspace.
colors:
  forest: "#163f3a"
  deep: "#123530"
  ink: "#203b36"
  muted: "#596d63"
  subtle-ink: "#53694f"
  line: "#dce5df"
  paper: "#f5f7f4"
  white: "#fff"
  mint: "#c7e6cd"
  selected-mint: "#d0e7d0"
  selected-ink: "#234a3d"
  primary-hover: "#285d4f"
  on-primary: "#f0f7ef"
  field-border: "#d3ddd1"
  field-ink: "#344e38"
  status-surface: "#edf1e9"
  observation-surface: "#e8eeE7"
  focus: "#6c9a79"
typography:
  headline:
    fontFamily: "Manrope, Arial, sans-serif"
    fontSize: "28px"
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: "-0.035em"
  section:
    fontFamily: "Manrope, Arial, sans-serif"
    fontSize: "22px"
    fontWeight: 600
    lineHeight: 1.35
    letterSpacing: "-0.03em"
  title:
    fontFamily: "Manrope, Arial, sans-serif"
    fontSize: "18px"
    fontWeight: 600
    lineHeight: 1.4
    letterSpacing: "-0.025em"
  body:
    fontFamily: "Manrope, Arial, sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.6
  navigation:
    fontFamily: "Manrope, Arial, sans-serif"
    fontSize: "13px"
    fontWeight: 500
    lineHeight: 1.6
  action:
    fontFamily: "Manrope, Arial, sans-serif"
    fontSize: "12px"
    fontWeight: 600
    lineHeight: 1.6
  field:
    fontFamily: "Manrope, Arial, sans-serif"
    fontSize: "12px"
    fontWeight: 400
    lineHeight: 1.6
  label:
    fontFamily: "Manrope, Arial, sans-serif"
    fontSize: "11px"
    fontWeight: 600
    lineHeight: 1.6
  mono:
    fontFamily: "ui-monospace, monospace"
    fontSize: "11px"
    fontWeight: 400
    lineHeight: 1.6
rounded:
  label: "4px"
  compact: "5px"
  control: "6px"
  navigation: "7px"
  observation: "8px"
  container: "12px"
spacing:
  xs: "8px"
  sm: "10px"
  md: "12px"
  regular: "16px"
  inset: "18px"
  panel: "22px"
  gutter: "24px"
  section: "28px"
  page: "40px"
components:
  button-primary:
    backgroundColor: "{colors.forest}"
    textColor: "{colors.on-primary}"
    typography: "{typography.action}"
    rounded: "{rounded.control}"
    padding: "10px 15px"
  button-primary-hover:
    backgroundColor: "{colors.primary-hover}"
  button-secondary:
    backgroundColor: "{colors.white}"
    textColor: "#3e5f50"
    typography: "{typography.action}"
    rounded: "{rounded.control}"
    padding: "10px 15px"
  button-secondary-hover:
    backgroundColor: "#eef4ec"
  button-stop:
    backgroundColor: "#f7e9e3"
    textColor: "#903e25"
    typography: "{typography.action}"
    rounded: "{rounded.control}"
    padding: "10px 15px"
  field:
    backgroundColor: "{colors.white}"
    textColor: "{colors.field-ink}"
    typography: "{typography.field}"
    rounded: "{rounded.control}"
    padding: "10px"
  navigation-selected:
    backgroundColor: "{colors.selected-mint}"
    textColor: "{colors.selected-ink}"
    rounded: "{rounded.navigation}"
    padding: "12px 13px"
  state-label:
    backgroundColor: "{colors.status-surface}"
    textColor: "{colors.subtle-ink}"
    rounded: "{rounded.label}"
    padding: "2px 7px"
  work-panel:
    backgroundColor: "{colors.white}"
    rounded: "{rounded.container}"
  observation:
    backgroundColor: "{colors.observation-surface}"
    rounded: "{rounded.observation}"
---

# Design System: BluPe × EmbodiedEvo

## Overview

**Creative North Star: "Research journal index"**

The implemented system pairs a forest navigation area with cool white work surfaces and compact humanist type. Hierarchy comes from alignment, restrained borders and clearly named controls. This describes the built workspace; it does not imply a standing user aesthetic preference.

Standard forms, tabs and tables keep research operations inspectable. The connected protocol rail adds identity through a functional diagram, while observation and knowledge areas separate explanatory graphics from returned evidence.

**Key Characteristics:**
- Forest navigation with mint selection.
- Flat white panels on cool off-white paper.
- Compact Manrope type and aligned controls.
- Explicit readiness, provenance and protocol state.

Extracted from `app/page.tsx` and `app/globals.css`, checked against desktop and mobile review captures. Token structure follows the [DESIGN.md format](https://raw.githubusercontent.com/google-labs-code/design.md/main/docs/spec.md); extensions live in `.impeccable/design.json`.

## Colors

Forest and muted greens carry the interface; white and cool paper keep its dense information calm.

### Primary
- **Forest** anchors navigation, selected tab underlines and primary actions; **Deep** supplies selection text.
- **Primary hover** brightens enabled primary actions; **On primary** supplies their pale text.

### Secondary
- **Mint** is the text-selection fill. **Selected mint** and **Selected ink** are the sidebar's active destination pair. Protocol progress uses its own closely related green literals in the component snippet.

### Neutral
- **Ink** is the base text; **Muted** supports top-level descriptions. **Subtle ink** carries most panel metadata, help text and table labels.
- **Paper** is the page canvas; **White** is the work surface; **Line** divides and outlines panels.
- **Field border** and **Field ink** define native inputs; **Status surface** and **Observation surface** distinguish metadata and camera work areas.

Waiting indicators use muted amber text, with separate header and action-footer values. Errors and Stop use warm pale fills and brown-red text. These are functional states, not decorative accents. **Focus** is the shared visible keyboard outline.

**The Evidence State Rule.** Color accompanies a written state; it never substitutes for the label or establishes that a run succeeded.

## Typography

Manrope is self-hosted at `/manrope.ttf`, with Arial and sans-serif fallbacks. The shipped font face supports weights (400–800) and uses swap loading. Technical digests and file paths use the platform monospace stack.

- **Headline:** the page title; responsive overrides range from (24–28px), with the narrowest breakpoint using (26px).
- **Section:** method headings; mobile uses (21px).
- **Title:** run headings; narrow mobile uses (17px), wide desktop (20px).
- **Body:** base text; method prose uses a more open line height (1.9).
- **Navigation / Action / Field / Label:** compact controls and metadata. Selected navigation and tabs rise to weight (700).
- **Mono:** digests, paths and logs; long values wrap rather than truncate their identity.

The frontmatter records default desktop roles, not a universal type scale. Panel explanatory text usually uses (12–13px); secondary metadata commonly uses (11px).

## Layout

Desktop uses a fixed navigation width (224px), a top bar (76px high) and a main content maximum (1550px). Content has side insets (40px); the workspace divides into a flexible run panel and a configuration column (302px), separated by a gutter (24px). Method content is capped at (850px).

At (1200px) and below, navigation narrows to (190px), page insets to (28px), and the configuration column to (270px). At (1000px), the workspace stacks and configuration fields use two columns. At (760px), navigation becomes an in-flow horizontal header and the protocol becomes two columns. At (480px), navigation wraps below the brand, headings and search stack, the setup form returns to block flow, and page side insets become (18px). Paired numeric fields remain paired. At (1550px) and above, run and observation areas gain height.

Spacing tokens describe reused dimensions, not a strict arithmetic scale. Tables scroll within their own container; long hashes and manifest paths wrap. The mobile knowledge heading stacks its Download action. Preserve document order when columns stack.

## Elevation & Depth

The interface has no box shadows. White panels, pale observation areas, single-pixel borders and sectional dividers create depth. Buttons change background and text color over (180ms); reduced-motion preference removes transitions.

**The Flat Work Surface Rule.** Use tonal separation and borders for work areas; preserve the existing shadow-free hierarchy.

## Shapes

Controls have gently rounded corners; larger work panels use the container radius. Labels are tighter, observation wells intermediate. Protocol nodes and readiness dots are circles. One-pixel solid borders define panels and fields; dashed outlines distinguish the empty campaign area and task-diagram target.

## Components

### Buttons
Primary, secondary and Stop share compact type, a control radius, horizontal icon spacing (9px), and minimum height (42px). Secondary actions have a thin border. Disabled buttons retain their treatment at opacity (0.45) with a not-allowed cursor. Keyboard focus uses a visible outline (3px) and offset (4px). Icon buttons are compact squares (34px) and have descriptive accessible names.

### Inputs / Fields
Native inputs and selects use a white fill, field border, control radius and minimum height (41px). Labels sit above controls. Disabled saved configuration fields use a pale fill and remain readable at full opacity. Validation uses native field constraints; request failures appear in a dismissible alert above the workspace.

### Navigation and Tabs
Sidebar destinations combine line icons and sentence-case text. Mint fill and heavier type mark the selected destination. Environment and run tabs use forest text plus a bottom rule; run-detail tabs support arrow keys, Home and End. Mobile preserves text labels and moves navigation into the header.

### State Labels and Work Panels
State labels are compact, pale badges; failed campaign labels use a warm exception treatment. Panels share white fill, a line border and container radius. Their headings, tabs and action footers are separated structurally. Table headers use a pale fill; campaign names remain underlined buttons with adjacent task metadata.

### Protocol Rail and Observation Area
Numbered circular nodes connect Practice, Freeze, Test in simulation and Test on YAM. Only recorded campaign state changes progress styling. Mobile wraps the rail into two rows and removes connectors at its narrowest width. The observation well shows a labelled CSS task diagram until a native image is available. A returned image remains visible after a job reaches a terminal state; the caption describes whether a simulation is active separately.

## Do's and Don'ts

### Do:
- **Do** use forest for navigation and primary actions, with mint for selected navigation.
- **Do** preserve flat white panels, explicit borders and compact aligned controls.
- **Do** retain visible keyboard focus, text labels and local table scrolling on mobile.
- **Do** distinguish a task diagram, a native observation, and a campaign outcome in their labels.

### Don't:
- **Don't** replace readiness or protocol labels with color alone.
- **Don't** style queued work as completed evidence or imply physical task success without a reviewed physical result.
- **Don't** treat local QA fixture campaigns or their knowledge files as real research results.
- **Don't** add decorative raster imagery to the existing evidence areas; retain their current CSS diagram and native-image roles.
