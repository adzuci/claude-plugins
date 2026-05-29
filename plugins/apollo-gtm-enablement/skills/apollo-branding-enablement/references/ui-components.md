# Apollo UI Component Patterns — Extended Reference

Use these specs when composing slide elements in python-pptx. Translate CSS values to EMU/Pt as needed.

## Badge / Pill Label

```text
background:     #FBF500
color:          #252521
font:           ABC Diatype 700, 12px, All-Caps, letter-spacing: 0.1em
fallback:       Arial Bold
border-radius:  24px
padding:        4px 12px
```

## Numbered Action Circle

```text
background:     #FBF500
color:          #252521
shape:          circle, 32x32px
font:           SeasonMix Variable 550, 16px
fallback:       Georgia Bold
```

## Dashed Action Callout Box

```text
border:         1.5px dashed rgba(37,37,33,0.4)
border-radius:  8px
background:     transparent
padding:        20px
```

## PRO TIP Block

```text
background:     #F9F9F6
border-left:    4px solid #FBF500
border-radius:  0 8px 8px 0
padding:        14px 16px
font:           ABC Diatype 400, 14px, #252521
fallback:       Arial
label:          PRO TIP
label font:     ABC Diatype 700 All-Caps, #252521
box-shadow:     var(--shadow-1)
```

## Content Card / Info Box

```text
background:     #F9F9F6 or #FFFFFF
border-radius:  12px
padding:        24px
box-shadow:     var(--shadow-1)
```

## KPI Card

```text
background:     #F9F9F6
border-radius:  8px
padding:        16px
box-shadow:     var(--shadow-1)
eyebrow:        10px ABC Diatype All-Caps, #252521 at 50% opacity
value:          24px SeasonMix Variable 550, #252521
delta:          14px ABC Diatype 400, one line below value
```

## Apollo Sun Callout

```text
background:     #F9F9F6
border-left:    4px solid #FBF500
border-radius:  0 8px 8px 0
padding:        14px 16px
Use sparingly. One per section maximum.
```

## Routing Logic Chip

```text
border:         1.5px solid #252521
border-radius:  999px
background:     transparent
padding:        4px 10px
font:           ABC Diatype 400, 10px, All-Caps, letter-spacing: 0.08em
fallback:       Arial
color:          #252521
```

## Section Divider

```text
border-top:     1px solid #252521
width:          100%
margin:         8px 0 16px
```

## Timeline Node

```text
background:     #FBF500
color:          #252521
border-radius:  999px
padding:        4px 10px
font:           SeasonMix Variable 550, 13px
fallback:       Georgia Bold
```

## Timeline Card

```text
background:     #F9F9F6
border-radius:  0 0 16px 0
padding:        16px
min-height:     120px
```

## Host Photo Circle

```text
shape:          circle
fill:           #252521 at 20% opacity
use:            placeholder only. Never generate faces.
sizes:          1 host=400px, 2 hosts=320px, 3 hosts=260px, 4 hosts=220px
```

## Engagement Activity Slide

```text
background:     #FBF500
watermark:      Apollo sunburst, large, bottom-right, Stone outline ~15% opacity
badge:          ENGAGEMENT ACTIVITY pill, Stone bg, Off-White text
headline:       SeasonMix Variable 550, 64-96px, #252521
fallback:       Georgia Bold
types:          Polling, Zoom Chat, Breakout Exercise, Quiz Time
```

## Weekly Rundown Table

```text
header row:     bg #252521, text #FFFFFF, ABC Diatype 700 All-Caps
body rows:      bg #F9F9F6, separator 1px solid rgba(37,37,33,0.15)
link icon:      #252521
status marks:   use Stone or White only unless an approved semantic palette has been explicitly provided
```
