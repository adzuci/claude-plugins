---
name: experiment-cleanup
description: Remove a shipped experiment from the leadgenie codebase, keeping the winning code path, and open the cleanup PR.
disable-model-invocation: true
---

# Experiment Cleanup

## Invocation

Direct-invocation only. Run against a `apolloio/leadgenie` checkout:

```text
/apollo-eng-experimentation:experiment-cleanup FooBar
```

The argument is the experiment name in any form — `FooBar`, `ExperimentNames.FooBar`,
`fooBar`, or the kebab Amplitude key. Step 1 normalizes it.

## Model Recommendation

**Use Sonnet or equivalent.** Experiment cleanup requires multi-hop reasoning: tracing derived variables through prop threading, identifying dead code in child components, and making correct branch-elimination decisions. Haiku should be avoided — it has been observed missing secondary cleanup steps (e.g., removing a prop from a child component that was only introduced for the experiment).

## Steps

### Step 0 — Preflight

Phase 4 opens the PR and labels it with `gh label create` / `gh pr edit`. Check `gh` before touching
any code, so an auth problem surfaces now instead of after a full cleanup is sitting uncommitted:

```bash
gh auth status
```

Non-zero exit means `gh` is missing or not logged in. Stop and tell the user:

> **GitHub CLI is not authenticated.**
> Run `gh auth login` (install `gh` first if the command is missing), then restart the skill.

______________________________________________________________________

### Phase 1 — Discovery (read before asking anything)

**1. Parse the experiment name** from the user's request. Normalize all of these formats to the `ExperimentNames` enum key:

- `ExperimentNames.FooBar` → `FooBar`
- `foo-bar` → search for matching enum key (kebab-case to PascalCase)
- `FooBar` → `FooBar`

**2. Find the YAML entry** by grepping `config/experiments/*.yml` for the `code_ref` value `ExperimentNames.<name>`. Note which file it lives in (determines the owning team) and the `amplitude_key`.

**3. Determine scope by grepping — do not ask the user** unless the results are ambiguous:

- Check `assets/types/experiments.ts` for the `ExperimentNames` enum entry → frontend usages exist
- Grep `packs/`, `app/`, and `spec/` for the `amplitude_key` and its snake_case equivalent → backend usages exist

From the grep results, determine scope:

- **frontend only** → `ExperimentNames` entry exists, no backend references
- **backend only** → no `ExperimentNames` entry, backend references found
- **fullstack** → both exist

**Only ask the user** if grep results are genuinely unclear (e.g., matches are ambiguous or the `code_ref` points to something unexpected). In that case, combine into one message with the variant question below.

**4. (frontend / fullstack only) Read `assets/types/experiments.ts`** and locate:

- The enum entry in `ExperimentNames`
- The entry in `activeExperiments` — note the exact `variants` array (e.g., `['control', 'treatment']`, `['control', 'treatment-a', 'treatment-b']`, or custom names)

**⚠️ Early exit — already partially cleaned up:** If the enum entry does NOT exist in `experiments.ts` but the YAML entry still exists, the frontend code has already been removed. Skip directly to step 10 (delete the YAML entry) and then Phase 4 (PR). Tell the user what you found.

**🛑 Then, immediately — before opening any other file — present the exact variants array to the user and ask which variant won. Do not proceed to step 5 until you have their answer.** This is what completing step 4 means. The wrong variant choice will silently ship the wrong behavior.

**5. (frontend / fullstack only) Find all frontend usages** by grepping `assets/` for `ExperimentNames.<name>`. Build a complete list of files to edit.

**6. (backend / fullstack only) Find all backend usages** by grepping `packs/`, `app/`, and `spec/` for the `amplitude_key` (e.g., `foo-bar` or its snake_case equivalent `foo_bar`). Look specifically for:

- `Experimentation::Experiments.get_experiment_variant` calls
- `Experimentation::Experiments.get_cached_experiment_variant` calls
- Constants holding the flag key (e.g., `FOO_BAR_EXPERIMENT_FLAG = 'foo-bar'`)

**⚠️ Flipper flag vs Amplitude experiment:** If grep results include `FeatureFlag.on?(:foo_bar)` but no `get_experiment_variant` calls, those are **Flipper feature flag** usages — a separate system from Amplitude experiments. Do not touch them. Only edit files that reference the Amplitude experiment via `get_experiment_variant` / `get_cached_experiment_variant` or a `MockExperiment`.

Build a complete list of Ruby files to edit.

______________________________________________________________________

### Phase 2 — Code Changes

**Before writing any code:** confirm you have the user's answer to the variant question from step 4. If you do not have it, ask now and wait for their answer before proceeding.

Make changes in this order:

#### Frontend changes (skip if backend-only)

**7. Edit each frontend file that references the experiment**

For each file found in step 5, apply the appropriate cleanup pattern:

##### Hook patterns

- **Simple boolean hook**:

  ```ts
  // Before
  const variant = useExperiment(ExperimentNames.Foo, 'control');
  return variant === 'treatment';

  // After (treatment won)
  return true;

  // After (control won)
  return false;
  ```

- **Ternary rendering**:

  ```tsx
  // Before
  {variant === 'treatment' ? <NewUI /> : <OldUI />}

  // After (treatment won)
  <NewUI />
  ```

- **If/else block**:

  ```ts
  // Before
  if (variant === 'treatment') { /* new */ } else { /* old */ }

  // After (treatment won)
  /* new */
  ```

- **Compound condition**:

  ```ts
  // Before
  return isAdmin && variant === 'treatment';

  // After (treatment won)
  return isAdmin;
  ```

- **Multi-variant (3-way split)** — remove all non-winning branches regardless of which variant won:

  ```ts
  // Before
  if (variant === 'treatment-a') { /* A */ }
  else if (variant === 'treatment-b') { /* B */ }
  else { /* control */ }

  // After (treatment-b won)
  /* B */

  // After (control won)
  /* control */
  ```

##### `useExperimentExposure` pattern

When a file uses `useExperimentExposure` instead of `useExperiment`, remove the entire destructured call and inline the winning variant:

```ts
// Before
const { exposeExperiment, variant, exposureStatus } = useExperimentExposure(ExperimentNames.Foo);
useEffect(() => {
  if (exposureStatus === 'not exposed') exposeExperiment();
}, [exposureStatus, exposeExperiment]);
// ... later ...
return variant === 'treatment' ? <NewUI /> : <OldUI />;

// After (treatment won) — remove hook, useEffect, and all variant checks; inline winning path
return <NewUI />;

// After (control won)
return <OldUI />;
```

Remove the hook call, the `useEffect`, and every reference to `variant`, `exposeExperiment`, and `exposureStatus`. Do not leave `variant` as an unresolved identifier.

##### `selectExperimentVariant` selector pattern

When the experiment is accessed via Redux selector (common in listeners and non-component files):

```ts
// Before
const variant = selectExperimentVariant(state, ExperimentNames.Foo);
if (variant !== 'treatment') return;

// After (treatment won) — remove the check entirely, the listener always runs
```

##### Variant passed as prop (prop threading)

After editing the hook call site, check if the variant variable — or any **derived boolean** (e.g., `const shouldUseOceanButton = variant === 'treatment'`) — is passed as a prop to child components. Grep for both the variable name and any prop names it is passed under to find downstream usages. Trace through all layers — grandchildren may also receive the prop — and simplify each one.

When a derived boolean prop becomes a constant after cleanup (always `true` or always `false`):

1. **Remove the prop from the JSX call site** — don't leave `shouldUseFoo={true}` behind
1. **Remove the prop from the child component's type definition and function signature**
1. **Collapse the conditional in the child** to always render the winning branch, and delete the losing branch

Example:

```tsx
// BulkSelectDialog.tsx — Before
const shouldUseOceanButton = variant === 'treatment';
<GenericDialog shouldUseExperimentalHighContrastButton={shouldUseOceanButton} />

// BulkSelectDialog.tsx — After (treatment won)
<GenericDialog />   // prop removed entirely

// GenericDialog.tsx — Before
type Props = { shouldUseExperimentalHighContrastButton?: boolean; ... };
const GenericDialog = ({ shouldUseExperimentalHighContrastButton = false, ... }) => (
  {shouldUseExperimentalHighContrastButton ? <OceanButton /> : <Button />}
);

// GenericDialog.tsx — After (treatment won) — prop removed, always render OceanButton
type Props = { ... };  // prop removed from type
const GenericDialog = ({ ... }) => (
  <OceanButton />
);
```

______________________________________________________________________

After simplifying all usages, remove:

- The `useExperiment` / `useExperimentExposure` call itself
- The `useExperiment` / `useExperimentExposure` import if no longer used in the file
- The `ExperimentNames` import if no longer used in the file
- The `selectExperimentVariant` import if no longer used in the file
- Any dead components, hooks, or utilities that were only used in the losing branch — see step 7a below for the explicit sweep procedure

**7a. Dead-code sweep — files introduced exclusively for the experiment**

After editing all experiment references, look back at the branches you removed and identify any component, hook, or utility that was **exclusively imported or used inside the deleted code path**. Common indicators:

- A component that was only rendered in the treatment branch (e.g., `<SocialProofFeatureGateDialog />`)
- A hook that was only called inside the removed `if (variant === 'treatment')` block
- A utility function only referenced by the above

**First, grep `FeatureGatesPlayground.tsx`** for any playground entries added to demo the treatment variant, and remove those too. Do this **before** checking for external callers — a playground demo entry is not a production caller, and its presence should not prevent deletion of a dead component.

For each remaining candidate:

1. **Grep for the identifier across the entire `assets/` tree**:

   ```bash
   grep -r "SocialProofFeatureGateDialog" assets/ --include="*.ts" --include="*.tsx"
   ```

   The following do **not** count as external callers — exclude them from your count:

   - The component's own definition file (its `function`/`const` declaration and its own exports)
   - Its own `.test.tsx` / `.test.ts` file
   - Its own `.stories.tsx` Storybook story file
   - Any `FeatureGatesPlayground.tsx` entry you already removed in the step above

   If the only remaining hits fall into those categories, treat it as **zero external callers**.

1. If **zero external callers** exist, delete the file and all co-located artefacts:

   - The component/hook/utility file itself (`.tsx` / `.ts`)
   - Its test file (`.test.tsx` / `.test.ts`)
   - Its SCSS module (`.module.scss`)
   - Its Storybook story file (`.stories.tsx`)

1. If **any non-excluded callers remain**, leave the file — it has production use beyond the experiment.

> **Why this step exists:** The final reference check in step 16 only searches for the experiment name/key strings. A component built exclusively for the treatment variant contains no experiment-name string — grep will never flag it. This explicit sweep catches that category of dead code.

**8. Update `assets/types/experiments.ts`**

- Remove the entry from the `ExperimentNames` enum
- Remove the entry from the `activeExperiments` object
- Both must remain **alphabetically sorted** (there is a test that enforces this)

______________________________________________________________________

#### Backend changes (skip if frontend-only)

**9. Edit each backend file that references the experiment**

For each file found in step 6, apply the appropriate cleanup pattern:

##### `get_experiment_variant` / `get_cached_experiment_variant` pattern

```ruby
# Before
variant = Experimentation::Experiments.get_experiment_variant(
  FOO_BAR_EXPERIMENT_FLAG, user, expose_variant: false
)
if variant.to_s == 'treatment'
  # treatment logic
else
  # control logic
end

# After (treatment won) — remove the variant check, keep treatment logic
# treatment logic

# After (control won) — remove the variant check, keep control logic
# control logic
```

- Remove the `get_experiment_variant` / `get_cached_experiment_variant` call entirely
- Remove the flag key constant (e.g., `FOO_BAR_EXPERIMENT_FLAG = 'foo-bar'`) if no longer used
- Remove any `expose_variants` calls for this experiment
- Remove any `Experimentation::Experiments` import/include if no longer used in the file
- Remove dead methods or classes that were only used in the losing branch (verify with a project-wide search before deleting)

##### RSpec cleanup

- Remove `allow(Experimentation::Experiments).to receive(:get_experiment_variant).with(FOO_BAR_EXPERIMENT_FLAG, ...)` stubs
- Remove `allow(Experimentation::Experiments).to receive(:get_cached_experiment_variant).with(...)` stubs
- Delete test contexts/examples that exist solely to test the losing variant path
- Keep tests that remain valid (testing non-experiment behavior) but remove the experiment setup from them

______________________________________________________________________

**10. Delete the YAML entry** from `config/experiments/<team>.yml`

**11. Clean up frontend test files** *(frontend / fullstack only)*

Search for references to the experiment in test files:

- `makeExperiment({ name: ExperimentNames.X, ... })` calls used to set up Redux experiment state — remove these and simplify the wrappers
- `vi.mock('common/hooks/useExperiment')` blocks or `vi.mocked(useExperiment).mockReturnValue(...)` calls scoped to this experiment
- Any `MockExperiment` entries in Playwright/E2E test scenario files
- Tests that exist solely to test the removed/legacy code path — delete them; tests that remain valid (testing non-experiment behavior) — keep them but remove the experiment setup

______________________________________________________________________

### Phase 3 — Validation

**12. (frontend / fullstack only) Run TypeScript check**:

```bash
npx tsc --noEmit
```

Fix any type errors before proceeding.

**13. (frontend / fullstack only) Run the experiments alphabetical order test**:

```bash
pnpm test assets/types/experiments.test.ts
```

**14. (frontend / fullstack only) Run tests for each affected frontend file**:

```bash
pnpm test <path/to/affected.test.tsx>
```

Run this for each test file you modified or deleted. Fix any failures before proceeding.

**15. (backend / fullstack only) Run RSpec for each affected backend file**:

```bash
SKIP_COVERAGE=1 bin/rspec <path/to/affected_spec.rb>
```

Fix any failures before proceeding.

**16. Final reference check** — search the entire repo for every form of the experiment name and confirm zero results remain:

- `ExperimentNames.<Name>` (enum key) — frontend
- The camelCase value (e.g., `addonTrials`) — frontend
- The amplitude_key / kebab-case (e.g., `addon-trials`) — both
- The snake_case equivalent (e.g., `addon_trials`) — backend
- The flag key constant name (e.g., `ADDON_TRIALS_EXPERIMENT_FLAG`) — backend

Search across `assets/`, `config/`, `packs/`, `app/`, `spec/`, and `playwright/`. If any references remain, go back and clean them up before proceeding to the PR.

**⚠️ Exception — `assets/types/feature-flags.ts`:** This file is auto-generated by CI from the backend Flipper flag definitions. Any match here is a Flipper feature flag entry, not experiment code. Do **not** remove entries from this file during experiment cleanup.

**16a. Ownership file cleanup** — if any components or files were deleted in step 7, grep `CODEOWNERS` and `apollo-dev-teams.yml` for references to those deleted paths and remove any matching entries:

```bash
# Replace OceanPrimaryButton with the name of each deleted component/file
grep -n "OceanPrimaryButton" CODEOWNERS apollo-dev-teams.yml
```

Remove any lines that reference deleted files. These ownership entries become stale dead config if left behind.

______________________________________________________________________

### Phase 4 — Hand Off

**17. Present a summary and hand off to the user.**

Show a brief summary of what was cleaned up:

- Which experiment was removed
- Whether it was frontend, backend, or fullstack
- Which variant won (and what behavior is now the permanent default)
- Files changed, deleted, and tests updated

Then prompt the user with:

```
Cleanup complete. Before creating the PR:

- [ ] Review all diffs and confirm the correct variant was kept
- [ ] Test the affected UX flows manually to verify app behavior
- [ ] Once confirmed, create the PR (e.g. via `/ship-it` or `gh pr create`)

When writing the PR description, note:
- Which experiment was removed and which variant won
- That dead code and tests were cleaned up
- ⚠️ Changes were AI-generated — please review all diffs carefully before merging

After creating the PR, add the `claude-experiment-cleanup` label:
gh label create "claude-experiment-cleanup" --color "0E8A16" --description "PR opened via Claude Code experiment-cleanup skill" 2>/dev/null || true
gh pr edit "$(gh pr view --json number --jq .number)" --add-label "claude-experiment-cleanup"
```
