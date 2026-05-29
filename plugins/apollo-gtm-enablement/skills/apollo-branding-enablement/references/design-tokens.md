# Apollo Design Tokens — Extended Reference

## Spacing

```text
Base unit: 4px
--sp-1: 4px   --sp-2: 8px   --sp-3: 12px   --sp-4: 16px
--sp-5: 24px  --sp-6: 32px  --sp-7: 48px   --sp-8: 64px   --sp-9: 96px
All paddings, gaps, and margins snap to this grid.
```

## Border Radius

```text
Card:       8px
Container:  12px
Pill:       24px (or 999px for full round)
Nothing else. Never 6px. Never 16px standalone.
```

## Shadows

```text
--shadow-1: resting
--shadow-2: hover / active
--shadow-3: overlays / floating panels
--shadow-glow: 0 0 24px rgba(251,245,0,0.45) <- logo and Apollo Sun CTA only
```

## Motion Presets

> Applies only when this skill is used for HTML artifacts, mockups, or adjacent digital surfaces. Not required for PPTX production.

```text
Entrance:   reveal (1s spring), fade-up (0.8s expo), assemble (4-ray stagger)
Continuous: spin (20s linear), spin-fast (8s), pulse (2s), glow (2.5s), breathe (4s)
Hover:      lift (translateY -4px + scale 1.05), glow drop-shadow
Press:      scale(0.98) 150ms
Easing:     --ease-out-expo, --ease-spring, --ease-smooth
Never:      raw ease-in-out on brand motion. Never stretch, recolor mid-animation, or morph shape.
```

## Glassmorphism

> Applies only when this skill is used for HTML artifacts or mockups. Not a PPTX pattern.

```text
backdrop-filter: blur(20px), surface 60-80% opaque
Use on: floating toolbars, slide-over panels
Not on: primary cards
Never: semi-transparent text
```

## Typography Fallback Size Mapping

For Google Slides / Docs environments where licensed fonts are unavailable:

```text
Cover headline:      48-64pt   Georgia Bold
Section headline:    24-36pt   Georgia Bold
Doc / slide title:   18pt      Georgia Bold
Body text:           12pt      Arial Regular   MINIMUM
Supporting text:     11pt      Arial Regular
Badge / label:       10pt      Arial Bold, All-Caps
Footer:              10pt      Arial Regular, All-Caps
```

## Letter Spacing

```text
Headlines:  -0.02em
Badges:     +0.1em
Body:       0
```
