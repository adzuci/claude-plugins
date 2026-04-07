---
name: battle
description: Run a Pokemon-style battle between Apollo employees using Trainer Cards derived from real work activity. Activate when user says battle, pokemon, trainer card, fight, matchup, who would win, or /battle.
---

# Pokemon Battle Skill

Run a Pokemon-style battle between Apollo employees using Trainer Card stats derived from real work activity — Snowflake queries, GitHub PRs, Slack presence, Jira tickets, and more.

## Commands

```
/apollo-data:battle                → you vs random opponent, battle type randomly chosen
/apollo-data:battle @name          → you vs them
/apollo-data:battle team           → your team fusion vs random team
/apollo-data:battle explain        → data rationale for last battle's cards
/apollo-data:battle hand           → show your current card and stats
/apollo-data:battle leaderboard    → ELO rankings
```

No interactive prompts. No menus. One message in, one battle out.

## Card Data

All card data lives in this skill's `data/` directory. These files are auto-updated weekly from the analytics-copilot repo.

- `data/player_cards.md` — individual Trainer Cards (types, stats, moves, Ghost status, rationale)
- `data/team_cards.md` — team fusion cards
- `data/dept_cards.md` — department and pillar cards
- `data/terrain_cards.md` — battle arenas and weather effects

### Card Format

```
### {Name}
- tier: {1|2|3}
- type: {Primary}/{Secondary}
- nature: {Nature}
- department: {Department}
- team: {Team}
- ghost: {false|secondary|primary|phantom}
- hp: {N} | atk: {N} | def: {N} | spd: {N} | spatk: {N} | spdef: {N}
- signature: {MOVE NAME} ({Type}, {Power} power)
- moves: {Move2} ({Type}, {Power}), {Move3} ({Type}, {Power})
- held_item: {Item}
- passive: {Ability}
- wild_pool: [{CARD1}, {CARD2}]
- quote: "{Quote}"
- refreshed: {date}
- rationale: |
    HP {N}: {explanation}
    ATK {N}: {explanation}
    ...
```

If a requested fighter isn't found, generate a temporary card:

- Type: Normal/Ghost
- All stats: 40
- Signature: UNKNOWN TECHNIQUE (Normal, 50 power)
- Quote: "Who is this person? Even Jarvis doesn't know."

______________________________________________________________________

## Step 1: Identify the Fighters

- **No name specified:** Ask who they are (or use their git/Slack identity if detectable), pick a random opponent from a different department.
- **@name specified:** User vs that person.
- **`team` specified:** Load team cards from `data/team_cards.md`, user's team vs random opposing team.

______________________________________________________________________

## Step 2: Roll Battle Type

Randomly select:

| Battle Type | Weight | Description |
|-------------|--------|-------------|
| Wild Encounter | 40% | 1v1, your terrain. "A wild Shyam appeared!" |
| Gym Battle | 15% | 1v1 on THEIR home terrain. You're the challenger. |
| Fusion Battle | 15% | Your team fuses vs their team. |
| Rival Battle | 15% | Jarvis picks someone you've battled before or work adjacent to. |
| Gigantamax | 10% | Department cards clash. Massive stats. |
| Legendary Raid | 5% | You + 2 allies vs an exec card. Nearly impossible. |

Overrides: `/battle team` forces Fusion. C-suite opponent forces Legendary Raid. Henry forces Wild Encounter.

______________________________________________________________________

## Step 3: Set the Terrain

Read arenas from `data/terrain_cards.md`.

| Arena | Type | Effect |
|-------|------|--------|
| The Analytics Forge | Steel/Electric | AI queries 1.5x power |
| The Pipeline Depths | Rock/Ground | Ground/Rock +20% DEF |
| The Revenue Colosseum | Fire/Fighting | Fighting +20% ATK end-of-quarter |
| The Conversion Funnel | Grass/Electric | +25% SP.ATK |
| The Feature Factory | Electric/Psychic | +15% SPD |
| The Support Trenches | Water/Fairy | Water moves +20% |
| The Shadow Network | Dark/Steel | Dark moves guaranteed hit |
| The Expansion Chamber | Fighting/Ground | Uncovered types 3x damage |
| The Alliance Hall | Fairy/Normal | 2x SP.ATK |
| The Waterfall Cascade | Water/Grass | Fill rate = damage modifier |

**Ghost primary types are IMMUNE to terrain bonuses.**

Arena selection: Wild=yours, Gym=theirs, Fusion/Gigantamax=random, Rival=50/50, Legendary=exec's.

Active weather based on calendar: end-of-quarter=QUOTA PRESSURE, Friday=SHIP-IT WINDS, Monday AM=WEEKLY SYNC FOG.

______________________________________________________________________

## Step 4: Deal Hands

Each fighter gets 3 cards. User sees theirs. Opponent's hidden until post-battle.

1. **Move card** — best type-advantage move from their list (or user-specified)
1. **Terrain card** — their home arena. HOME FIELD bonus (+10% all stats) if it matches battle arena.
1. **Wild card** — from their `wild_pool`. Effects: MOMENTUM (+15% SPD), ON FIRE (+15% ATK), BLOCKED (-10% SPD), DORMANT (-20% all), FADING (-5% all for Ghosts), etc.

Display:

```
YOUR HAND:
  🃏 FOUNDATION FORGE (Steel, 95 power)
  🃏 THE ANALYTICS FORGE (terrain) — home field! +10% all stats
  🃏 MOMENTUM (wild) — +15% SPD

OPPONENT: Shyam SK (Psychic/Dark)
  🃏 🂠 🂠 🂠
```

______________________________________________________________________

## Step 5: Execute Battle

### Pre-battle modifiers (apply in order):

1. Nature: +10%/-10% per nature table
1. Ghost penalty: secondary -10%, primary -15%, phantom base 10 all
1. Terrain bonus: type match → arena effect
1. Wild card effect
1. Home field: terrain card matches arena → +10% all
1. Fusion aura: team provides +5% DEF (not if team is Ghost/LEADERLESS)

### Combat (4-6 turns):

```
Turn order: higher SPD first (ties random)

Damage:
  base = move_power * (ATK / 100)
  type_mod = effectiveness (2.0 super, 0.5 not very, 0.0 immune)
  crit = 2.0 if random < 0.10, else 1.0
  random = 0.85 to 1.15
  defense = 100 / (100 + DEF)
  effective_damage = base * type_mod * crit * random * defense

Signature moves use higher of ATK/SP.ATK.
Secondary moves alternate physical/special.
8% miss chance. Ghost types: 15% dodge.
```

### Fusion: team cards fight, LEADERLESS = -20% DEF, Ghost teams = -10% all

### Gigantamax: 3x stat scale, Max moves at 1.5x power, ABANDONED depts can't Gigantamax

### Legendary Raid: player + 2 allies vs exec at 500+ HP scale, execs win ~70%

______________________________________________________________________

## Step 6: Narrate

**The narration IS the product.** It must be entertaining, screenshottable, and weave in real work context.

Structure:

```
⚔️ {BATTLE TYPE}

{Opening — introduce fighters with personality}
{Terrain + weather announcement}

🎴 YOUR HAND:
  {cards}

🂠 Opponent's hand: three cards, face down.

───────────────────────────────

{Turn-by-turn combat, 4-6 turns}
{Reference real work in flavor text}
{Wild card activation moment}
{Dramatic finish}

───────────────────────────────

🏆 WINNER: {Name}
   FINAL HP: {Winner} {N}% | {Loser} 0%
   MVP: {Move} ({detail})

🂠→🎴 OPPONENT'S HAND REVEALED:
  {Move} | {Terrain} | {Wild card}

GG. /apollo-data:battle explain for the data.
    /apollo-data:battle for another.
```

### Narration rules:

- Reference real work: "14 tables slam into existence like a dbt run with zero warnings!"
- Use fighter quotes from cards
- Ghost types get eerie narration
- Henry ALWAYS loses hilariously
- Legendary Raids are genuinely scary
- Crits reference recent achievements
- Fusion names the members

______________________________________________________________________

## Step 7: Post-Battle

### `/apollo-data:battle explain`

Show stat rationale for both fighters from the card's `rationale` field.

### `/apollo-data:battle hand`

Show the user's full card without fighting.

### `/apollo-data:battle leaderboard`

Track wins/losses/ELO across battles. Store in memory or local state.

______________________________________________________________________

## Ghost Type Rules

| Status | Penalty | Terrain | Dodge | Moves | Special |
|---|---|---|---|---|---|
| Full | None | Normal | 8% | 4 | — |
| Ghost secondary | -10% all | Normal | 12% | 3 | — |
| Ghost primary | -15% all | Immune | 15% | 1 | Immune to Normal/Fighting |
| Phantom | Base 10 all | Immune | 20% | 1 | Dodge 1 free |

Team: >50% Ghost → Ghost fusion. Ghost manager → LEADERLESS (-20% DEF). Dept >50% Ghost managers → ABANDONED (no Gigantamax).

______________________________________________________________________

## Type Chart

| Attacking ↓ \\ Defending → | Normal | Fire | Water | Electric | Grass | Ice | Fighting | Ground | Flying | Psychic | Dark | Rock | Ghost | Dragon | Steel | Fairy |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Normal | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | .5 | 0 | 1 | .5 | 1 |
| Fire | 1 | .5 | .5 | 1 | 2 | 2 | 1 | 1 | 1 | 1 | 1 | .5 | 1 | .5 | 2 | 1 |
| Water | 1 | 2 | .5 | 1 | .5 | 1 | 1 | 2 | 1 | 1 | 1 | 2 | 1 | .5 | 1 | 1 |
| Electric | 1 | 1 | 2 | .5 | .5 | 1 | 1 | 0 | 2 | 1 | 1 | 1 | 1 | .5 | 1 | 1 |
| Grass | 1 | .5 | 2 | 1 | .5 | 1 | 1 | 2 | .5 | 1 | 1 | 2 | 1 | .5 | .5 | 1 |
| Ice | 1 | .5 | .5 | 1 | 2 | .5 | 1 | 2 | 2 | 1 | 1 | 1 | 1 | 2 | .5 | 1 |
| Fighting | 2 | 1 | 1 | 1 | 1 | 2 | 1 | 1 | .5 | .5 | 2 | 2 | 0 | 1 | 2 | .5 |
| Ground | 1 | 2 | 1 | 2 | .5 | 1 | 1 | 1 | 0 | 1 | 1 | 2 | 1 | 1 | 2 | 1 |
| Flying | 1 | 1 | 1 | .5 | 2 | 1 | 2 | 1 | 1 | 1 | 1 | .5 | 1 | 1 | .5 | 1 |
| Psychic | 1 | 1 | 1 | 1 | 1 | 1 | 2 | 1 | 1 | .5 | 0 | 1 | 1 | 1 | .5 | 1 |
| Dark | 1 | 1 | 1 | 1 | 1 | 1 | .5 | 1 | 1 | 2 | .5 | 1 | 2 | 1 | .5 | .5 |
| Rock | 1 | 2 | 1 | 1 | 1 | 2 | .5 | .5 | 2 | 1 | 1 | 1 | 1 | 1 | .5 | 1 |
| Ghost | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 2 | .5 | 1 | 2 | 1 | 1 | 1 |
| Dragon | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 2 | .5 | 0 |
| Steel | 1 | .5 | .5 | .5 | 1 | 2 | 1 | 1 | 1 | 1 | 1 | 2 | 1 | 1 | .5 | 2 |
| Fairy | 1 | .5 | 1 | 1 | 1 | 1 | 2 | 1 | 1 | 1 | 2 | 1 | 1 | 2 | .5 | 1 |

2 = super effective, .5 = not very, 0 = immune. Dual types: multiply both.

## Natures

| Nature | +10% | -10% |
|--------|------|------|
| Adamant | ATK | SPD |
| Bold | DEF | ATK |
| Careful | DEF | SPD |
| Jolly | SPD | DEF |
| Quiet | SP.ATK | SPD |
| Modest | — | — |
| Timid | SPD | ATK |
| Brave | ATK | SPD |
| Impish | DEF | ATK |
| Hasty | SPD | DEF |

______________________________________________________________________

## About This Skill

Cards are generated from real work activity by the Analytics team's company-wide scan. Stats reflect actual Snowflake queries, GitHub PRs, Slack presence, Jira tickets, documentation, and tool usage. Ghost typing means low visibility across work systems — not low performance.

**Card data is refreshed weekly** from the analytics-copilot repo. To learn more about how stats are calculated, ask for `/apollo-data:battle explain` after any battle.

Built by the Analytics team. Leo is Jarvis's father. Bridie is Jarvis's godmother. Henry is to blame for everything else.
