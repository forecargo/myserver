---
colors:
  surface: '#faf9fd'
  surface-dim: '#dad9dd'
  surface-bright: '#faf9fd'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f4f3f7'
  surface-container: '#efedf1'
  surface-container-high: '#e9e7eb'
  surface-container-highest: '#e3e2e6'
  on-surface: '#1a1c1e'
  on-surface-variant: '#43474e'
  inverse-surface: '#2f3033'
  inverse-on-surface: '#f1f0f4'
  outline: '#74777f'
  outline-variant: '#c4c6cf'
  surface-tint: '#455f88'
  primary: '#002045'
  on-primary: '#ffffff'
  primary-container: '#1a365d'
  on-primary-container: '#86a0cd'
  inverse-primary: '#adc7f7'
  secondary: '#505f76'
  on-secondary: '#ffffff'
  secondary-container: '#d0e1fb'
  on-secondary-container: '#54647a'
  tertiary: '#321b00'
  on-tertiary: '#ffffff'
  tertiary-container: '#4f2e00'
  on-tertiary-container: '#c6955e'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d6e3ff'
  primary-fixed-dim: '#adc7f7'
  on-primary-fixed: '#001b3c'
  on-primary-fixed-variant: '#2d476f'
  secondary-fixed: '#d3e4fe'
  secondary-fixed-dim: '#b7c8e1'
  on-secondary-fixed: '#0b1c30'
  on-secondary-fixed-variant: '#38485d'
  tertiary-fixed: '#ffddba'
  tertiary-fixed-dim: '#f2bc82'
  on-tertiary-fixed: '#2b1700'
  on-tertiary-fixed-variant: '#633f0f'
  background: '#faf9fd'
  on-background: '#1a1c1e'
  surface-variant: '#e3e2e6'
typography:
  h1-display:
    fontFamily: Inter
    fontSize: 36px
    fontWeight: '700'
    lineHeight: '1.2'
    letterSpacing: -0.02em
  h2-section:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: '1.3'
    letterSpacing: -0.01em
  h3-card:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '600'
    lineHeight: '1.4'
    letterSpacing: 0em
  body-reading:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.65'
    letterSpacing: 0em
  body-meta:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: '1.5'
    letterSpacing: 0em
  label-caps:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '700'
    lineHeight: '1'
    letterSpacing: 0.05em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  base: 8px
  container-max: 1280px
  reading-width: 720px
  gutter: 24px
  margin-page: 40px
---

## Brand & Style

The design system is engineered to project an image of unwavering stability and technical precision. Designed for the high-stakes environment of financial cybersecurity compliance, the aesthetic prioritizes information density and legibility over decorative flair. The style sits at the intersection of **Corporate Modernism** and **Minimalism**, utilizing a structured grid and a restrained color palette to reduce cognitive load during complex search tasks.

The user experience should evoke a sense of being "in safe hands." By utilizing high-contrast typography and a surgical application of color, the design system guides users through dense regulatory frameworks with the efficiency of a professional investigative tool. It avoids the playfulness of consumer apps in favor of a formal, institutional character that respects the gravity of cybersecurity guidelines.

## Colors

The palette is anchored by **Deep Navy (#1A365D)**, a color synonymous with financial institutions and traditional security. This primary tone is used for structural elements such as headers, primary navigation, and critical actions to reinforce authority. 

A muted blue-grey is employed for secondary interface elements—such as icons and metadata—to prevent the interface from feeling overwhelming. The background remains a clean, clinical white to maximize contrast for long-form reading.

The semantic system is deliberate:
- **Basic Requirements:** Utilizes a subtle, low-saturation blue background with deep blue text to indicate a foundational necessity without alarming the user.
- **Desirable Measures:** Employs an emerald green to signify optimal security posture and positive progression.
- **Borders & Dividers:** High-lightness greys are used to create structure without introducing visual noise.

## Typography

This design system utilizes **Inter** for its exceptional legibility in data-heavy environments and its neutral, systematic character. The typographic hierarchy is strictly enforced to help users parse multi-level guidelines.

For long-form guideline text, the line height is increased to `1.65` to prevent eye fatigue during extended reading sessions. Headlines use a tighter tracking and heavier weight to provide clear anchoring points on the page. Labels for categories and scores utilize a bold, uppercase style to differentiate functional metadata from the primary narrative text.

## Layout & Spacing

The layout philosophy follows a **Fixed Grid** model for content-heavy views to ensure an optimal line length for reading. 

The application utilizes a 12-column grid system, but for the core "guideline view," the content is restricted to a specialized `reading-width` of 720px. This prevents the eye from having to travel too far across the screen, a common issue in technical documentation. Sidebars are reserved for hierarchical navigation and "mini-map" document outlines. Spacing follows a strict 8px rhythmic scale, ensuring all components align to a predictable vertical and horizontal flow.

## Elevation & Depth

To maintain a formal and authoritative tone, this design system avoids heavy shadows and vibrant blurs. Instead, it uses **Low-contrast outlines** and **Tonal layers** to create depth.

Most surface containers (like search cards) sit flat on the `background_secondary` using a 1px border in `border_subtle`. When an element requires focus, such as a hovering result card, a very soft, ambient shadow (4% opacity, 12px blur) is applied to suggest lift without breaking the "paper-like" feel of the document interface. This restrained approach ensures that the user's focus remains on the text, not the interface itself.

## Shapes

The shape language is conservative. A **Soft (0.25rem)** radius is applied to standard components like input fields, buttons, and badges. This provides a modern touch that removes the "sharpness" of legacy software while remaining professional.

Larger containers, such as result cards, may use a slightly more pronounced `rounded-lg` (0.5rem) to subtly distinguish them from the background. Search bars, as the primary interaction point, maintain the standard 0.25rem radius to align with the formal visual language.

## Components

### Search Bar
The primary search interface must be prominent but clean. It uses a thick `border_subtle` that darkens on focus, with no heavy glow effects. A clear "Search Guidelines" placeholder and a leading magnifying glass icon in `secondary_color` are mandatory.

### Result Cards
Structured cards display search results with a clear hierarchy:
1. **Header:** Guideline Title (Navy).
2. **Relevance Score:** A numerical percentage (e.g., "98% Match") placed in the top right, using a light grey background.
3. **Category Badges:** Tags indicating the source or type of guideline.
4. **Snippet:** 2-3 lines of guideline text with the search keywords highlighted in a subtle yellow background.

### Status Badges
Badges for 'Basic' and 'Desirable' measures use a pill-shape (fully rounded) with the semantic background and text colors defined in the palette. They must be placed consistently near the guideline title.

### Guidelines Reader
The reading view features a "sticky" table of contents on the left and an annotation gutter on the right. Annotations should appear as small, clickable icons in the margin that expand to show commentary or links to related regulations without obscuring the main text.

### Buttons
- **Primary:** Solid Deep Navy with white text for main actions (e.g., Export, Save).
- **Secondary:** Outlined grey for navigation or secondary actions.
- **Text Buttons:** Used for inline references or "See more" actions to maintain a document-first feel.