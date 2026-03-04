# Contributing to Apollo Skills

This repo is the central place for shared Claude skills and skill packs at Apollo. The format matches [anthropics/skills](https://github.com/anthropics/skills), so their template and docs apply here too.

## Adding a new skill

1. **Copy the template**  
   Copy `template/SKILL.md` into your plugin’s skills folder:
   ```
   plugins/<plugin-name>/skills/<skill-name>/SKILL.md
   ```
   Example: `plugins/apollo-eng-pack/skills/my-skill/SKILL.md`.

2. **Set frontmatter**  
   In the YAML at the top of `SKILL.md`:
   - **name**: Lowercase, hyphenated (e.g. `my-skill`). This is the skill name users invoke.
   - **description**: One line describing *what* the skill does and *when* Claude should use it (include trigger terms so the agent can discover it).

3. **Write the body**  
   Replace the placeholder with real instructions. You can add optional supporting files (e.g. `reference.md`, scripts) in the same skill directory.

4. **If the skill lives in a new plugin**  
   - Add a new folder under `plugins/` with the same structure as an existing plugin (see “Adding a new skill pack” below).
   - Register the plugin in `.claude-plugin/marketplace.json` under `plugins` (name, source path, description).

## Adding a new skill pack (plugin)

If you need a new plugin (e.g. a separate pack for product or infra):

1. **Copy the plugin template**  
   Copy the `template-plugin/` folder to `plugins/<pack-name>/` (e.g. `plugins/apollo-product-pack/`).

2. **Edit the plugin manifest**  
   In `plugins/<pack-name>/.claude-plugin/plugin.json`, set `name`, `description`, and `version`.

3. **Register in the marketplace**  
   In `.claude-plugin/marketplace.json`, add an entry to the `plugins` array:
   ```json
   {
     "name": "<pack-name>",
     "source": "./plugins/<pack-name>",
     "description": "Short description of the pack"
   }
   ```

4. **Add skills**  
   Use the steps in “Adding a new skill” above, with `<plugin-name>` = your new pack name.
