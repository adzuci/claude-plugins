const assert = require('assert/strict');
const { execFileSync } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');
const test = require('node:test');

const scriptPath = path.join(__dirname, 'update-devteams.js');
const {
  staleKnownSignals,
  assertValidYaml,
  normalizeNotionRows,
  reconcileTeamsWithNotion,
  renderNotionReconcile,
  renderNotionDiscovery,
} = require(scriptPath);

function makeFixture() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'update-devteams-'));
  const teamsPath = path.join(root, 'apollo-dev-teams.yml');
  fs.writeFileSync(
    teamsPath,
    `teams:
  - name: 'inbound'
    okta_team: 'Inbound'
    description: 'Inbound team'
    github_team: '@apolloio/inbound'
    team_slack: '#xfn-team-inbound'
    alerts_slack: '#warm-outbound-alerts'
    on_call_usergroup_name: 'oncall-warm-outbound'
    pagerduty:
      pagerduty_high_priority:
        service_name: 'inbound'
      pagerduty_low_priority:
        service_name: 'inbound'
    members:
      - github: ''
        name: ''
        email: ''
      - github: '@good'
        name: 'Good User'
        email: 'good@apollo.io'
  - name: 'componentization'
    okta_team: '<missing>'
    description: 'Old componentization team'
    github_team: '@apolloio/componentization'
    team_slack: '#xfn-team-componentization'
    on_call_usergroup_name: ''
    excluded_from_analysis: true
    pagerduty:
      pagerduty_high_priority:
        service_name: 'componentization'
      pagerduty_low_priority:
        service_name: 'componentization'
    members: []
    files_owned:
      - 'package.yml'
  - name: 'zenleads'
    okta_team: '<missing>'
    description: 'Legacy'
    github_team: 'zenleads'
    team_slack: ''
    on_call_usergroup_name: ''
    excluded_from_analysis: true
    pagerduty:
      pagerduty_high_priority:
        service_name: 'zenleads'
      pagerduty_low_priority:
        service_name: 'zenleads'
    members: []
  - name: 'ops-lite'
    okta_team: 'Ops Lite'
    description: 'Active team without on-call'
    github_team: '@apolloio/ops-lite'
    team_slack: '#ops-lite'
    on_call_usergroup_name: ''
    pagerduty:
      pagerduty_high_priority:
        service_name: ''
      pagerduty_low_priority:
        service_name: ''
    members:
      - github: '@ops'
        name: 'Ops User'
        email: 'ops@apollo.io'
`,
  );
  fs.mkdirSync(path.join(root, 'scripts'), { recursive: true });
  fs.writeFileSync(
    path.join(root, 'scripts', 'plays-fe.ts'),
    "export const owner = 'oncall-plays-fe';\nexport const team = '@apolloio/plays-fe';\n",
  );
  return { root, teamsPath };
}

function run(args, cwd) {
  return execFileSync('node', [scriptPath, ...args], { cwd, encoding: 'utf8', timeout: 30_000 });
}

test('report mode finds known reorg cleanup buckets', () => {
  const { root, teamsPath } = makeFixture();
  const output = run(['report', '--repo-root', root, '--teams', teamsPath], root);

  assert.match(output, /Scanned 4 YAML teams/);
  assert.match(output, /Rename cleanup: inbound/);
  assert.match(output, /ACTION: componentization/);
  assert.match(output, /ACTION: zenleads/);
  assert.doesNotMatch(output, /Confidence/);
  assert.match(output, /Outside reference drift: on_call_usergroup_not_in_yaml=1/);
  assert.match(output, /ACTION: plays-fe \/ workflows/);
  assert.match(output, /Teams to Coordinate With/);
});

test('report mode can write an html report', () => {
  const { root, teamsPath } = makeFixture();
  const htmlPath = path.join(root, 'report.html');
  const output = run(['report', '--repo-root', root, '--teams', teamsPath, '--html', htmlPath], root);
  const html = fs.readFileSync(htmlPath, 'utf8');

  assert.match(output, /Wrote HTML report/);
  assert.match(html, /<title>Dev Teams Report<\/title>/);
  assert.match(html, /<h1>Dev Teams Report<\/h1>/);
  assert.match(html, /href="file:\/\/[^"]+apollo-dev-teams\.yml"/);
  assert.match(html, /href="file:\/\/[^"]+scripts\/plays-fe\.ts"/);
  assert.match(html, /Nudge Focus/);
  assert.match(html, /10-Day Activity/);
  assert.match(html, /Teams by Org/);
  assert.match(html, /need action/);
  assert.match(html, /days left/);
  assert.match(html, /not red/);
  assert.match(html, /100% non-red/);
  assert.match(html, /Try update mode:/);
  assert.match(html, /--replace-text oncall-plays-fe=oncall-confirmed-owner --write/);
  assert.match(html, /class="action"/);
  assert.match(html, /class="warning"/);
  assert.match(html, /Confirm PD/);
  assert.match(html, /Metadata refs:/);
  const openActions = html.slice(html.indexOf('<h2>Teams by Org</h2>'));
  assert.ok(openActions.indexOf('class="action"') < openActions.indexOf('class="warning"'));
  assert.doesNotMatch(html, /Appendix: Metadata Reference Counts/);
  assert.doesNotMatch(html, /Marcin Review Ask/);
  assert.doesNotMatch(html, /Two-Week Delivery Plan/);
  assert.doesNotMatch(html, /Risk Hedge/);
  assert.doesNotMatch(html, /Confidence/);
  assert.match(html, /oncall-plays-fe/);
});

test('update mode is dry-run by default', () => {
  const { root, teamsPath } = makeFixture();
  const before = fs.readFileSync(teamsPath, 'utf8');
  const output = run(['update', '--teams', teamsPath, '--set', 'inbound.alerts_slack=#inbound-alerts'], root);

  assert.match(output, /Dry run only/);
  assert.equal(fs.readFileSync(teamsPath, 'utf8'), before);
});

test('update mode applies explicit YAML and text updates with --write', () => {
  const { root, teamsPath } = makeFixture();
  const playsPath = path.join(root, 'scripts', 'plays-fe.ts');
  const output = run(
    [
      'update',
      '--teams',
      teamsPath,
      '--set',
      'inbound.alerts_slack=#inbound-alerts',
      '--file',
      playsPath,
      '--replace-text',
      'oncall-plays-fe=oncall-workflows',
      '--write',
    ],
    root,
  );

  assert.match(output, /Applied updates/);
  assert.match(fs.readFileSync(teamsPath, 'utf8'), /alerts_slack: '#inbound-alerts'/);
  assert.match(fs.readFileSync(playsPath, 'utf8'), /oncall-workflows/);
});

test('remove-empty-members removes only blank placeholder member records', () => {
  const { root, teamsPath } = makeFixture();
  run(['update', '--teams', teamsPath, '--team', 'inbound', '--remove-empty-members', '--write'], root);
  const output = fs.readFileSync(teamsPath, 'utf8');

  assert.doesNotMatch(output, /github: ''\n\s+name: ''\n\s+email: ''/);
  assert.match(output, /github: '@good'/);
});

test('nested --set paths are rejected, not silently misapplied', () => {
  const { root, teamsPath } = makeFixture();
  assert.throws(
    () => run(['update', '--teams', teamsPath, '--set', 'inbound.pagerduty.high=x', '--write'], root),
    /Nested --set paths are not supported/,
  );
});

test('assertValidYaml accepts good YAML and rejects corrupt YAML', () => {
  assert.doesNotThrow(() => assertValidYaml("teams:\n  - name: 'inbound'\n"));
  // Unclosed flow sequence is not valid YAML.
  assert.throws(() => assertValidYaml('teams: [unbalanced\n  - name: x'), /invalid YAML/);
});

function writeNotionFixture(root) {
  // Shape mirrors a Notion API query response (results[].properties[].type).
  const notionPath = path.join(root, 'notion-teams.json');
  fs.writeFileSync(
    notionPath,
    JSON.stringify({
      results: [
        {
          id: 'page-inbound',
          url: 'https://notion.so/inbound',
          properties: {
            Team: { type: 'title', title: [{ plain_text: 'Inbound' }] },
            'Slack Channel': { type: 'rich_text', rich_text: [{ plain_text: '#inbound' }] },
          },
        },
        {
          id: 'page-ghost',
          url: 'https://notion.so/ghost',
          properties: {
            Team: { type: 'title', title: [{ plain_text: 'ghost-team' }] },
            'Slack Channel': { type: 'rich_text', rich_text: [{ plain_text: '#ghost' }] },
          },
        },
      ],
    }),
  );
  return notionPath;
}

test('normalizeNotionRows flattens API property types to strings', () => {
  const rows = normalizeNotionRows({
    results: [
      {
        id: 'p1',
        url: 'https://n/p1',
        properties: {
          Team: { type: 'title', title: [{ plain_text: 'Inbound' }] },
          Active: { type: 'checkbox', checkbox: true },
          Tags: { type: 'multi_select', multi_select: [{ name: 'a' }, { name: 'b' }] },
        },
      },
    ],
  });
  assert.equal(rows.length, 1);
  assert.equal(rows[0].props.Team, 'Inbound');
  assert.equal(rows[0].props.Active, 'true');
  assert.equal(rows[0].props.Tags, 'a, b');
});

test('reconcileTeamsWithNotion matches case-insensitively without guessing', () => {
  const teams = [
    { name: 'inbound', team_slack: '#xfn-team-inbound' },
    { name: 'ops-lite', team_slack: '#ops-lite' },
  ];
  const notionRows = normalizeNotionRows({
    results: [
      { id: 'a', properties: { Team: { type: 'title', title: [{ plain_text: 'Inbound' }] }, Slack: { type: 'rich_text', rich_text: [{ plain_text: '#inbound' }] } } },
      { id: 'b', properties: { Team: { type: 'title', title: [{ plain_text: 'ghost' }] }, Slack: { type: 'rich_text', rich_text: [{ plain_text: '#ghost' }] } } },
    ],
  });
  const result = reconcileTeamsWithNotion(teams, notionRows, {
    keyYaml: 'name',
    keyNotion: 'Team',
    maps: [{ yaml: 'team_slack', notion: 'Slack' }],
    exact: false,
  });
  assert.equal(result.matched.length, 1);
  assert.equal(result.matched[0].diffs.length, 1);
  assert.equal(result.matched[0].diffs[0].yaml, '#xfn-team-inbound');
  assert.equal(result.matched[0].diffs[0].notion, '#inbound');
  assert.deepEqual(result.yamlOnly.map((e) => e.key), ['ops-lite']);
  assert.deepEqual(result.notionOnly.map((e) => e.key), ['ghost']);
});

test('renderNotionReconcile marks output as read-only draft and surfaces drift', () => {
  const teams = [{ name: 'inbound', team_slack: '#xfn-team-inbound' }];
  const notionRows = normalizeNotionRows({
    results: [
      { id: 'a', url: 'https://n/a', properties: { Team: { type: 'title', title: [{ plain_text: 'Inbound' }] }, Slack: { type: 'rich_text', rich_text: [{ plain_text: '#inbound' }] } } },
      { id: 'b', url: 'https://n/b', properties: { Team: { type: 'title', title: [{ plain_text: 'ghost' }] }, Slack: { type: 'rich_text', rich_text: [{ plain_text: '#ghost' }] } } },
    ],
  });
  const maps = [{ yaml: 'team_slack', notion: 'Slack' }];
  const result = reconcileTeamsWithNotion(teams, notionRows, { keyYaml: 'name', keyNotion: 'Team', maps, exact: false });
  const output = renderNotionReconcile(result, { keyYaml: 'name', keyNotion: 'Team', maps, exact: false, notionProps: ['Slack', 'Team'] });

  assert.match(output, /Draft — Read Only/);
  assert.match(output, /team_slack: YAML="#xfn-team-inbound" vs Notion\[Slack\]="#inbound"/);
  assert.match(output, /ghost \(https:\/\/n\/b\)/);
  assert.match(output, /No files or Notion pages were changed/);
});

test('renderNotionDiscovery explains it will not guess mappings', () => {
  const teams = [{ name: 'inbound', team_slack: '#xfn-team-inbound' }];
  const notionRows = normalizeNotionRows({ results: [{ id: 'a', properties: { Team: { type: 'title', title: [{ plain_text: 'Inbound' }] } } }] });
  const output = renderNotionDiscovery(teams, notionRows, ['Team'], 'name');
  assert.match(output, /Setup Needed/);
  assert.match(output, /does not guess/);
  assert.match(output, /--key-notion/);
});

test('notion mode requires an export before touching the YAML', () => {
  const { root, teamsPath } = makeFixture();
  assert.throws(() => run(['notion', '--teams', teamsPath], root), /requires --notion-json/);
});

test('notion mode stops for setup when no key is given', () => {
  const { root, teamsPath } = makeFixture();
  const notionPath = writeNotionFixture(root);
  const setup = run(['notion', '--repo-root', root, '--teams', teamsPath, '--notion-json', notionPath], root);
  assert.match(setup, /Setup Needed/);
  assert.match(setup, /Notion Properties Detected/);
  assert.match(setup, /- Slack Channel/);
  assert.match(setup, /- Team/);
});

test('notion mode reports drift as a read-only draft', () => {
  const { root, teamsPath } = makeFixture();
  const notionPath = writeNotionFixture(root);
  const output = run(
    [
      'notion',
      '--repo-root',
      root,
      '--teams',
      teamsPath,
      '--notion-json',
      notionPath,
      '--key-notion',
      'Team',
      '--map',
      'team_slack=Slack Channel',
    ],
    root,
  );

  assert.match(output, /Reconciliation \(Draft — Read Only\)/);
  // inbound matches (case-insensitive) and its team_slack differs from Notion.
  assert.match(output, /team_slack: YAML="#xfn-team-inbound" vs Notion\[Slack Channel\]="#inbound"/);
  // ghost-team exists only in Notion; componentization/zenleads/ops-lite only in YAML.
  assert.match(output, /In Notion, Not Found in YAML/);
  assert.match(output, /ghost-team/);
  assert.match(output, /Confirm Before Applying/);
});

test('notion mode rejects an unknown key property', () => {
  const { root, teamsPath } = makeFixture();
  const notionPath = writeNotionFixture(root);
  assert.throws(
    () => run(['notion', '--repo-root', root, '--teams', teamsPath, '--notion-json', notionPath, '--key-notion', 'Nope'], root),
    /not found in export/,
  );
});

test('staleKnownSignals flags entries older than the threshold', () => {
  // All built-in signals are reviewed 2026-06-10; nothing is stale a week later.
  assert.equal(staleKnownSignals('2026-06-17', 90).length, 0);
  // ~1 year later, every signal is past the 90-day window.
  const stale = staleKnownSignals('2027-06-10', 90);
  assert.ok(stale.length > 0);
  assert.ok(stale.every((s) => s.ageDays > 90 && s.label && s.reviewed));
});
