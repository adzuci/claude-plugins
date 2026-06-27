#!/usr/bin/env node

const fs = require('fs');
const os = require('os');
const path = require('path');
const { execFileSync } = require('child_process');
const { pathToFileURL } = require('url');

const DEFAULT_PROJECT_DAYS = 14;

// Curated, reorg-specific cleanup signals. These are hardcoded by necessity:
// they encode point-in-time org knowledge that no system of record exposes.
// To keep them from rotting silently, each carries a `reviewed` date. The report
// flags any signal older than KNOWN_SIGNALS_STALE_AFTER_DAYS so a human re-verifies
// it. When you confirm a signal still applies (or update its tokens), bump `reviewed`.
const KNOWN_SIGNALS_STALE_AFTER_DAYS = 90;

const KNOWN_SIGNALS = [
  {
    team: 'inbound',
    kind: 'rename',
    tokens: ['warm-outbound', 'Warm Outbound', 'oncall-warm-outbound', '#warm-outbound-alerts'],
    note: 'Inbound still contains Warm Outbound-era metadata.',
    reviewed: '2026-06-10',
  },
  {
    team: 'componentization',
    kind: 'ghost',
    tokens: ['componentization', '@apolloio/componentization', '#xfn-team-componentization'],
    note: 'Componentization appears dissolved or transitional; do not delete while ownership references remain.',
    reviewed: '2026-06-10',
  },
  {
    team: 'zenleads',
    kind: 'legacy',
    tokens: ['zenleads', '#zenleads'],
    note: 'ZenLeads is a pre-rebrand artifact; confirm remaining runtime or historical references.',
    reviewed: '2026-06-10',
  },
  {
    external: 'oncall-plays-fe',
    kind: 'stale-owner-metadata',
    tokens: ['oncall-plays-fe'],
    note: 'oncall-plays-fe appears outside apollo-dev-teams.yml and needs confirmed replacement metadata.',
    reviewed: '2026-06-10',
  },
  {
    team: 'search-platform',
    kind: 'ghost',
    tokens: ['search-platform', '@apolloio/search-platform', 'oncall-search-platform'],
    note: 'search-platform was disbanded — work split across customer-data-platform and native-data.',
    reviewed: '2026-06-10',
  },
  {
    team: 'integrations',
    kind: 'ghost',
    tokens: ['integrations', '@apolloio/integrations', 'oncall-integrations'],
    note: 'integrations was disbanded — absorbed into customer-data-platform.',
    reviewed: '2026-06-10',
  },
];

// Eng reorg history for the report appendix.
// Source: https://docs.google.com/spreadsheets/d/1dT_uHxkFGecfc-err5-CowSW6PyFXlJs3e5WnbGj_pg/edit?gid=1420614656#gid=1420614656
const DISBANDED_TEAMS = [
  { team: 'workflows', successor: 'Split across ai-studio, cdp, rep-experience, rep-controls, headless, deliverability-and-dialer', note: 'Fully disbanded.' },
  { team: 'discovery', successor: 'customer-data-platform', note: 'Fully absorbed into CDP.' },
  { team: 'ai-applications', successor: 'agent-core, ai-infra', note: 'Split into Agent Platform and AI Infra.' },
  { team: 'integrations', successor: 'customer-data-platform', note: 'Still in YAML — absorbed into CDP.' },
  { team: 'conversation-intelligence', successor: 'Transitioned to KTLO under Griffin Brodman', note: 'No active product investment.' },
  { team: 'growth-engineering', successor: 'growth-conversion, growth-expansion, growth-pricing-and-packaging-be/fe, growth-activation-be/fe', note: 'Split into focused growth squads.' },
  { team: 'prospecting-and-engagement', successor: 'rep-experience', note: 'Prospecting scope merged into Rep Experience.' },
  { team: 'search-platform', successor: 'customer-data-platform, native-data', note: 'Still in YAML — split across CDP and Native Data.' },
];

const DISBANDED_TEAMS_SOURCE = 'https://docs.google.com/spreadsheets/d/1dT_uHxkFGecfc-err5-CowSW6PyFXlJs3e5WnbGj_pg/edit?gid=1420614656#gid=1420614656';

const DEFAULT_IGNORE_DIRS = new Set([
  '.git',
  'node_modules',
  'tmp',
  'log',
  'coverage',
  'build',
  'dist',
  '.cache',
  '.repowise',
  '.ai',
  '.claude',
  '.cursor',
]);

const VALUE_FIELDS = [
  'name',
  'okta_team',
  'description',
  'github_team',
  'team_slack',
  'alerts_slack',
  'pr_review_channel',
  'on_call_usergroup_name',
  'engineer_slack_usergroup_name',
  'jira_impacted_team',
  'sentry_team_slug',
];

// Known stale sentry_team_slug values and the note to surface when found.
// Add entries here for slugs that are in the process of being renamed but haven't landed yet.
const SENTRY_SLUG_RENAMES = [];

// Teams that intentionally have no Sentry team slug and should not be flagged for it.
const SENTRY_EXEMPT = [
  {
    team: 'call-commander',
    reason: 'Cross-functional incident response rotation, not a product team. Members are on-call leads from across eng; there is no Sentry project scoped to call-commander. Incident management owner: Himanshu Gahlot.',
  },
  {
    team: 'db-migrations',
    reason: 'Infrastructure guild coordinated by Ray Li, not a product team with its own services. DB migration work runs under the devops Sentry project scope.',
  },
  {
    team: 'fraud',
    reason: 'Security team — incidents follow a dedicated security escalation path, not Sentry error monitoring. No product Sentry project is scoped to fraud.',
  },
];

// Teams that intentionally have no on-call rotation or PagerDuty service and should not be flagged for it.
const ONCALL_EXEMPT = [
  {
    team: 'componentization',
    reason: 'Guild, not a product team — point of contact is Ray Li (be-platform). Owns Packwerk boundary enforcement tooling only; incidents escalate through be-platform on-call rather than a dedicated rotation.',
  },
  {
    team: 'db-migrations',
    reason: 'Infrastructure guild coordinated by Ray Li. Not a product team with its own PagerDuty service; incidents route through the devops on-call rotation.',
  },
  {
    team: 'appsec',
    reason: 'Security team — follows a dedicated security-specific escalation path rather than a PagerDuty product rotation.',
  },
  {
    team: 'fraud',
    reason: 'Security team — follows a dedicated security-specific escalation path rather than a PagerDuty product rotation.',
  },
  {
    team: 'internationalization',
    reason: 'No dedicated on-call rotation; i18n work is coordinated across teams without a separate PD service.',
  },
  {
    team: 'zenleads',
    reason: 'Pre-rebrand/legacy artifact kept for Sentry and Okta mapping. No operational on-call rotation.',
  },
];

// Teams that should not be flagged in the dissolved/ghost bucket — their legacy status is known and accepted.
const GHOST_EXEMPT = [
  { team: 'zenleads', reason: 'Pre-rebrand artifact; legacy status is expected and intentional.' },
  { team: 'componentization', reason: 'Active guild with real ownership references; not disbanded.' },
];

// Teams whose member records should not trigger member-cleanup issues (e.g. pre-rebrand or intentional skeletons).
const MEMBERS_EXEMPT = [
  { team: 'zenleads', reason: 'Pre-rebrand artifact; stale member records are expected and not actionable.' },
];

// Maps YAML team slug → display name of Himanshu's direct report (Eng Lead level).
// Used to group teams at the correct org level rather than relying on reporting_chain[1],
// which often resolves to Sr EMs instead of the top-level Eng Lead.
const ORG_HEAD_OVERRIDES = {
  // Aniruddha Laud area (Sr EMs: Anshul Pahwa, Utsav Kesharwani, Ahmed Hamdy)
  'agent-core': 'Aniruddha Laud',
  'agent-core-be': 'Aniruddha Laud',
  'agent-core-fe': 'Aniruddha Laud',
  'agentic-engineering': 'Aniruddha Laud',
  'ai-caps': 'Aniruddha Laud',
  'ai-caps-be': 'Aniruddha Laud',
  'ai-caps-fe': 'Aniruddha Laud',
  'ai-infra': 'Aniruddha Laud',
  'customer-data-platform': 'Aniruddha Laud',
  'data-platform': 'Aniruddha Laud',
  'headless': 'Aniruddha Laud',
  // Matt Palermo area (Sr EMs: Griffin Brodman, Mohamed Djadoun)
  'call-commander': 'Matt Palermo',
  'dialer': 'Matt Palermo',
  'rep-controls': 'Matt Palermo',
  'rep-experience-be': 'Matt Palermo',
  'rep-experience-fe': 'Matt Palermo',
  'sales-engagement': 'Matt Palermo',
  'search-platform': 'Matt Palermo',
  'warm-outbound': 'Matt Palermo',
  // Ray Li area (appsec/fraud reporting chain was pointing to Ralph Pyne, a CISO-access-only entry)
  'appsec': 'Ray Li',
  'fraud': 'Ray Li',
};

const ACTION_LABELS = {
  rename: 'Rename',
  slack: 'Slack',
  confirmPd: 'Confirm PD',
  onCall: 'On-call',
  sentry: 'Sentry',
  dissolvedActive: 'Dissolved (active owner)',
  dissolved: 'Dissolved',
  members: 'Members',
};

function parseArgs(argv) {
  const args = { _: [] };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (!arg.startsWith('--')) {
      args._.push(arg);
      continue;
    }

    const withoutPrefix = arg.slice(2);
    const eqIndex = withoutPrefix.indexOf('=');
    let key;
    let value;
    if (eqIndex >= 0) {
      key = withoutPrefix.slice(0, eqIndex);
      value = withoutPrefix.slice(eqIndex + 1);
    } else {
      key = withoutPrefix;
      const next = argv[i + 1];
      if (next && !next.startsWith('--')) {
        value = next;
        i += 1;
      } else {
        value = true;
      }
    }

    if (args[key] === undefined) {
      args[key] = value;
    } else if (Array.isArray(args[key])) {
      args[key].push(value);
    } else {
      args[key] = [args[key], value];
    }
  }
  return args;
}

function asArray(value) {
  if (value === undefined) return [];
  return Array.isArray(value) ? value : [value];
}

function readTeams(teamsPath) {
  const source = fs.readFileSync(teamsPath, 'utf8');
  const ruby = [
    "require 'yaml'",
    "require 'json'",
    "require 'date'",
    "data = YAML.safe_load(File.read(ARGV[0]), aliases: true, permitted_classes: [Date, Time, Symbol])",
    'puts JSON.generate(data)',
  ].join('; ');
  const data = JSON.parse(execFileSync('ruby', ['-e', ruby, teamsPath], { encoding: 'utf8' }));
  const teams = Array.isArray(data?.teams) ? data.teams : [];
  return { source, data, teams };
}

// Confirms an edited YAML source still parses. We edit apollo-dev-teams.yml with
// line-based regex replacements (not a parse/dump round-trip) on purpose: a full
// YAML library would reformat the whole file — reordering keys, dropping comments,
// rewrapping strings — and destroy the small, reviewable diffs this skill depends on.
// The trade-off is that a malformed edit could produce invalid YAML, so we re-parse
// the result here before writing and abort if it no longer loads.
function assertValidYaml(source) {
  const ruby = [
    "require 'yaml'",
    "require 'date'",
    'YAML.safe_load(STDIN.read, aliases: true, permitted_classes: [Date, Time, Symbol])',
  ].join('; ');
  try {
    execFileSync('ruby', ['-e', ruby], { input: source, encoding: 'utf8', stdio: ['pipe', 'ignore', 'pipe'] });
  } catch (error) {
    const detail = (error.stderr || error.message || '').toString().trim();
    throw new Error(`Edit produced invalid YAML; aborting before write.\n${detail}`);
  }
}

function normalizedBlank(value) {
  return value === undefined || value === null || String(value).trim() === '' || String(value).trim() === '<missing>';
}

function teamValueBlob(team) {
  const values = [];
  for (const field of VALUE_FIELDS) {
    if (team[field] !== undefined && team[field] !== null) values.push(String(team[field]));
  }

  if (team.pagerduty && typeof team.pagerduty === 'object') {
    collectStrings(team.pagerduty, values);
  }
  return values.join('\n');
}

function collectStrings(value, out) {
  if (typeof value === 'string') {
    out.push(value);
  } else if (Array.isArray(value)) {
    value.forEach((item) => collectStrings(item, out));
  } else if (value && typeof value === 'object') {
    Object.values(value).forEach((item) => collectStrings(item, out));
  }
}

function teamHasOwnership(team) {
  return ['packs_owned', 'files_owned', 'routes_owned', 'controller_action_override'].some((key) => {
    const value = team[key];
    return Array.isArray(value) ? value.length > 0 : Boolean(value);
  });
}

function assessTeams(teams, channelStatus, usergroupStatus) {
  const report = {
    totalTeams: teams.length,
    healthy: [],
    renameCleanup: [],
    slackIssues: [],
    onCallIssues: [],
    sentryIssues: [],
    ghostTeams: [],
    memberIssues: [],
  };

  for (const team of teams) {
    const issuesBefore = issueCount(report);
    const blob = teamValueBlob(team);
    const teamSignals = KNOWN_SIGNALS.filter((signal) => signal.team === team.name);

    for (const signal of teamSignals) {
      const matchingTokens = signal.tokens.filter((token) => blob.includes(token));
      if (signal.kind === 'rename' && matchingTokens.length > 0) {
        report.renameCleanup.push({
          team: team.name,
          tokens: matchingTokens,
          note: signal.note,
        });
      }

      const ghostExempt = GHOST_EXEMPT.some((e) => e.team === team.name);
      if (!ghostExempt && (signal.kind === 'ghost' || signal.kind === 'legacy') && (team.excluded_from_analysis || matchingTokens.length > 0)) {
        report.ghostTeams.push({
          team: team.name,
          reason: signal.note,
          activeOwnership: teamHasOwnership(team),
          excludedFromAnalysis: Boolean(team.excluded_from_analysis),
        });
      }
    }

    const ghostExempt = GHOST_EXEMPT.some((e) => e.team === team.name);
    if (!ghostExempt && team.excluded_from_analysis && !teamHasOwnership(team)) {
      report.ghostTeams.push({
        team: team.name,
        reason: 'excluded_from_analysis with no pack/file/route ownership',
        activeOwnership: false,
        excludedFromAnalysis: true,
      });
    }

    const slackFields = ['team_slack', 'alerts_slack', 'pr_review_channel'];
    for (const field of slackFields) {
      const value = team[field];
      if (normalizedBlank(value) && field === 'team_slack') {
        report.slackIssues.push({ team: team.name, field, value: value || '', status: 'missing' });
      } else if (value && channelStatus[value] && channelStatus[value] !== 'active') {
        report.slackIssues.push({ team: team.name, field, value, status: channelStatus[value] });
      }
    }

    const onCall = team.on_call_usergroup_name;
    const onCallExempt = ONCALL_EXEMPT.find((e) => e.team === team.name);
    if (normalizedBlank(onCall) && !onCallExempt) {
      report.onCallIssues.push({ team: team.name, field: 'on_call_usergroup_name', value: onCall || '', status: 'missing', severity: 'warning' });
    } else if (!onCallExempt && usergroupStatus[onCall] && usergroupStatus[onCall] !== 'active') {
      report.onCallIssues.push({ team: team.name, field: 'on_call_usergroup_name', value: onCall, status: usergroupStatus[onCall], severity: 'action' });
    }

    const sentrySlug = team.sentry_team_slug;
    const sentryExempt = SENTRY_EXEMPT.find((e) => e.team === team.name);
    if (normalizedBlank(sentrySlug) && !sentryExempt) {
      report.sentryIssues.push({ team: team.name, field: 'sentry_team_slug', value: sentrySlug || '', status: 'missing', severity: 'warning' });
    } else if (!normalizedBlank(sentrySlug)) {
      let foundStale = false;
      for (const rename of SENTRY_SLUG_RENAMES) {
        if (sentrySlug === rename.slug || team.github_team === rename.slug) {
          report.sentryIssues.push({ team: team.name, field: 'sentry_team_slug', value: sentrySlug, status: 'stale', note: rename.note, severity: 'action' });
          foundStale = true;
          break;
        }
      }
      if (!foundStale) {
        const slugWithoutHash = sentrySlug.replace(/^#/, '');
        if (slugWithoutHash !== team.name) {
          report.sentryIssues.push({
            team: team.name,
            field: 'sentry_team_slug',
            value: sentrySlug,
            status: 'name_mismatch',
            note: `sentry_team_slug '${sentrySlug}' does not match team name '${team.name}' — intentional rename or stale slug?`,
            severity: 'warning',
          });
        }
      }
    }

    const membersExempt = MEMBERS_EXEMPT.some((e) => e.team === team.name);
    if (!team.excluded_from_analysis && !membersExempt) {
      const members = Array.isArray(team.members) ? team.members : [];
      members.forEach((member, index) => {
        const missing = ['name', 'email', 'github'].filter((field) => normalizedBlank(member?.[field]));
        if (missing.length > 0) {
          report.memberIssues.push({
            team: team.name,
            memberIndex: index,
            missing,
            email: member?.email || '',
            github: member?.github || '',
          });
        }
      });
    }

    if (issueCount(report) === issuesBefore) {
      report.healthy.push(team.name);
    }
  }

  return report;
}

function issueCount(report) {
  return (
    report.renameCleanup.length +
    report.slackIssues.length +
    report.onCallIssues.length +
    report.sentryIssues.length +
    report.ghostTeams.length +
    report.memberIssues.length
  );
}

function readStatusJson(jsonPath) {
  if (!jsonPath || !fs.existsSync(jsonPath)) return {};
  return JSON.parse(fs.readFileSync(jsonPath, 'utf8'));
}

function readJsonIfPresent(jsonPath, fallback) {
  if (!jsonPath || !fs.existsSync(jsonPath)) return fallback;
  return JSON.parse(fs.readFileSync(jsonPath, 'utf8'));
}

function walkFiles(root, callback) {
  const entries = fs.readdirSync(root, { withFileTypes: true });
  for (const entry of entries) {
    const fullPath = path.join(root, entry.name);
    if (entry.isDirectory()) {
      if (!DEFAULT_IGNORE_DIRS.has(entry.name)) walkFiles(fullPath, callback);
      continue;
    }

    if (entry.isFile()) callback(fullPath);
  }
}

function isLikelyOwnershipFile(relPath) {
  const base = path.basename(relPath);
  return (
    base === 'CODEOWNERS' ||
    base === 'teams.yml' ||
    base === 'surface-owners.yml' ||
    base === 'RouteOwners.json' ||
    base === 'RouteOwnersOverrides.json' ||
    base === 'unused_files_by_owners.json' ||
    base === 'whitelist_unused_files_by_owners.json' ||
    relPath.includes('codeowners') ||
    relPath.includes('ownership') ||
    relPath.includes('/performance-notification/') ||
    relPath.includes('/sentry-performance-report')
  );
}

function scanOutsideReferences(repoRoot, teamsPath, teams) {
  const yamlPath = path.resolve(teamsPath);
  const knownGithubTeams = new Set(teams.map((team) => team.github_team).filter(Boolean));
  const knownUsergroups = new Set(teams.map((team) => team.on_call_usergroup_name).filter(Boolean));
  const findings = [];
  const oldTokens = KNOWN_SIGNALS.flatMap((signal) => signal.tokens.map((token) => ({ token, signal })));
  const knownStaleUsergroups = new Set(oldTokens.map(({ token }) => token).filter((token) => token.startsWith('oncall-')));

  walkFiles(repoRoot, (filePath) => {
    if (path.resolve(filePath) === yamlPath) return;
    let content;
    try {
      content = fs.readFileSync(filePath, 'utf8');
    } catch {
      return;
    }
    if (content.includes('\u0000')) return;

    const rel = path.relative(repoRoot, filePath);
    const ownershipFile = isLikelyOwnershipFile(rel);

    if (ownershipFile) {
      const githubRefs = content.match(/@apolloio\/[a-z0-9-]+/g) || [];
      for (const ref of new Set(githubRefs)) {
        if (!knownGithubTeams.has(ref)) {
          findings.push({ file: rel, token: ref, type: 'github_team_not_in_yaml' });
        }
      }
    }

    const usergroupRefs = content.match(/\boncall-[a-z0-9-]+\b/g) || [];
    for (const ref of new Set(usergroupRefs)) {
      if (!knownUsergroups.has(ref) && (ownershipFile || knownStaleUsergroups.has(ref))) {
        findings.push({ file: rel, token: ref, type: 'on_call_usergroup_not_in_yaml' });
      }
    }

    if (ownershipFile) {
      for (const { token, signal } of oldTokens) {
        // Negative lookbehind prevents matching tokens that appear as part of a file path
        // (e.g. "config/experiments/search-platform.yml" must not match the token "search-platform")
        const safeToken = token.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        const tokenRe = new RegExp(`(?<![/\\w.])${safeToken}(?![/\\w.])`, '');
        if (tokenRe.test(content)) {
          findings.push({ file: rel, token, type: signal.kind, note: signal.note });
        }
      }
    }
  });

  return dedupeFindings(findings).sort((a, b) => `${a.file}:${a.token}`.localeCompare(`${b.file}:${b.token}`));
}

function dedupeFindings(findings) {
  const seen = new Set();
  return findings.filter((finding) => {
    const key = `${finding.file}\0${finding.token}\0${finding.type}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function teamList(items) {
  return Array.from(new Set(items.map((item) => item.team).filter(Boolean))).sort();
}

function countByType(outsideReferences) {
  return outsideReferences.reduce((acc, item) => {
    acc[item.type] = (acc[item.type] || 0) + 1;
    return acc;
  }, {});
}

function buildChangePlan(report, outsideReferences) {
  const outsideTypes = countByType(outsideReferences);
  const coordination = [];
  const renameTeams = teamList(report.renameCleanup);

  if (renameTeams.includes('inbound')) {
    coordination.push({
      area: 'Inbound',
      reason: 'Warm Outbound-era Slack alert and on-call metadata still exists.',
      action: 'Confirm canonical alert channel and on-call usergroup before any update PR.',
    });
  }



  if (outsideReferences.some((item) => item.token === 'oncall-plays-fe')) {
    coordination.push({
      area: 'Workflows / Plays FE owner metadata',
      reason: '`oncall-plays-fe` appears outside the YAML and no longer matches team metadata.',
      action: 'Confirm canonical Workflows owner/on-call handle, then replace only the duplicated metadata.',
    });
  }

  return {
    coordination,
    outsideTypes,
    prOrder: [
      'Verified string metadata replacements only (Slack channels, on-call handles, generated route owner constants).',
      'Placeholder member cleanup where records are clearly empty or incomplete.',
      'Duplicate owner metadata sync in nearby config files once canonical owners are confirmed.',
      'Dissolved-team removal or ownership transfer only after explicit owner confirmation.',
    ],
  };
}

function normalizeKey(value) {
  return String(value || '')
    .toLowerCase()
    .replace(/&/g, 'and')
    .replace(/@apolloio\//g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

function yamlEms(team) {
  return (team.members || [])
    .filter((member) => member && member.is_em && !member.excluded_from_analysis)
    .map((member) => member.name || member.email || member.github)
    .filter(Boolean);
}

function buildEmailToName(teams) {
  const map = {};
  for (const team of teams) {
    for (const member of team.members || []) {
      if (member.email && member.name && !map[member.email]) {
        map[member.email] = member.name;
      }
    }
  }
  return map;
}

function orgHeadLabel(team, emailToName) {
  if (ORG_HEAD_OVERRIDES[team.name]) return ORG_HEAD_OVERRIDES[team.name];
  const chain = team.reporting_chain || [];
  const headEmail = chain.length > 1 ? chain[1] : null;
  if (!headEmail) return null;
  if (emailToName[headEmail]) return emailToName[headEmail];
  // Fallback: derive display name from email (e.g. "matt.palermo@apollo.io" → "Matt Palermo")
  return headEmail
    .split('@')[0]
    .split('.')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

function issueGroupsByTeam(report) {
  const groups = new Map();
  const add = (team, label) => {
    if (!team) return;
    if (!groups.has(team)) groups.set(team, []);
    groups.get(team).push(label);
  };

  for (const item of report.renameCleanup) add(item.team, ACTION_LABELS.rename);
  for (const item of report.slackIssues) add(item.team, ACTION_LABELS.slack);
  for (const item of report.onCallIssues) add(item.team, item.severity === 'warning' ? ACTION_LABELS.confirmPd : ACTION_LABELS.onCall);
  for (const item of report.sentryIssues) add(item.team, ACTION_LABELS.sentry);
  for (const item of report.ghostTeams) add(item.team, item.activeOwnership ? ACTION_LABELS.dissolvedActive : ACTION_LABELS.dissolved);
  for (const item of report.memberIssues) add(item.team, ACTION_LABELS.members);
  return groups;
}

function severityByTeam(report) {
  const severities = new Map();
  const set = (team, severity) => {
    if (!team) return;
    if (severity === 'action' || !severities.has(team)) severities.set(team, severity);
  };

  for (const item of report.renameCleanup) set(item.team, 'action');
  for (const item of report.slackIssues) set(item.team, 'action');
  for (const item of report.onCallIssues) set(item.team, item.severity || 'action');
  for (const item of report.sentryIssues) set(item.team, item.severity || 'action');
  for (const item of report.ghostTeams) set(item.team, 'action');
  for (const item of report.memberIssues) set(item.team, 'action');
  return severities;
}

function externalActionRows(outsideReferences) {
  const rows = [];
  if (outsideReferences.some((item) => item.token === 'oncall-plays-fe' || item.token === '@apolloio/plays-fe')) {
    rows.push({
      name: 'plays-fe / workflows',
      em: 'Keshav Garg (prev. Plays-FE), Aniruddha Laud (Workflows)',
      status: 'stale_external_reference',
      needsAction: true,
      severity: 'action',
      action: 'Confirm canonical Workflows/Plays owner metadata before replacing stale references.',
      confidence: 'medium',
    });
  }
  return rows;
}

function buildTeamRows(teams, report, outsideReferences) {
  const issues = issueGroupsByTeam(report);
  const severities = severityByTeam(report);
  const emailToName = buildEmailToName(teams);
  const rows = teams.map((team) => {
    const teamIssues = Array.from(new Set(issues.get(team.name) || []));
    const ems = yamlEms(team);
    const status = team.excluded_from_analysis ? 'excluded_from_analysis' : 'active';
    const needsAction = teamIssues.length > 0;
    const severity = severities.get(team.name) || 'ok';

    return {
      name: team.name,
      em: ems.join(', ') || '-',
      orgHead: orgHeadLabel(team, emailToName),
      status,
      needsAction,
      severity,
      action: needsAction ? teamIssues.join('; ') : 'No action from this scan',
      confidence: ems.length > 0 ? 'medium' : 'low',
    };
  });

  return rows.concat(externalActionRows(outsideReferences));
}

function progressFromRows(teamRows, totalTeams) {
  const yamlRows = teamRows.filter((row) => row.name !== 'plays-fe / workflows');
  const redRows = yamlRows.filter((row) => row.needsAction && row.severity === 'action');
  const yellowRows = yamlRows.filter((row) => row.needsAction && row.severity === 'warning');
  const notRedTeams = Math.max(totalTeams - redRows.length, 0);
  return {
    totalTeams,
    completeTeams: notRedTeams,
    actionTeams: redRows.length,
    warningTeams: yellowRows.length,
    completionPct: totalTeams === 0 ? 100 : Math.round((notRedTeams / totalTeams) * 1000) / 10,
    externalActionItems: teamRows.length - yamlRows.length,
  };
}

function daysBetween(startDate, endDate) {
  const start = new Date(`${startDate}T00:00:00.000Z`);
  const end = new Date(`${endDate}T00:00:00.000Z`);
  return Math.max(0, Math.round((end - start) / 86400000));
}

// Returns KNOWN_SIGNALS entries whose `reviewed` date is older than `maxDays`
// relative to `asOfIso`, so the report can prompt a human to re-verify them.
function staleKnownSignals(asOfIso, maxDays = KNOWN_SIGNALS_STALE_AFTER_DAYS, signals = KNOWN_SIGNALS) {
  const asOf = asOfIso || todayIsoDate();
  return signals
    .filter((signal) => signal.reviewed && daysBetween(signal.reviewed, asOf) > maxDays)
    .map((signal) => ({
      label: signal.team || signal.external,
      reviewed: signal.reviewed,
      ageDays: daysBetween(signal.reviewed, asOf),
    }));
}

function managerLabel(row) {
  if (row.em && row.em !== '-') return row.em;
  return `${row.name} (no EM in YAML)`;
}

function groupActionRowsByManager(actionRows) {
  const groups = new Map();
  for (const row of actionRows) {
    const label = managerLabel(row);
    if (!groups.has(label)) groups.set(label, []);
    groups.get(label).push(row);
  }

  return Array.from(groups.entries())
    .map(([manager, rows]) => ({
      manager,
      teams: rows.map((row) => row.name).sort(),
      severity: rows.some((row) => row.severity === 'action') ? 'action' : 'warning',
      actions: Array.from(new Set(rows.flatMap((row) => row.action.split(';').map((item) => item.trim())))).sort(),
    }))
    .sort((a, b) => {
      const severityDiff = severityRank(a.severity) - severityRank(b.severity);
      if (severityDiff !== 0) return severityDiff;
      if (a.manager === 'Needs owner confirmation') return 1;
      if (b.manager === 'Needs owner confirmation') return -1;
      return a.manager.localeCompare(b.manager);
    });
}

function severityRank(severity) {
  if (severity === 'action') return 0;
  if (severity === 'warning') return 1;
  return 2;
}

function compareRowsBySeverityThenName(a, b) {
  const severityDiff = severityRank(a.severity) - severityRank(b.severity);
  if (severityDiff !== 0) return severityDiff;
  return a.name.localeCompare(b.name);
}

function groupRowsByOrgHead(teamRows) {
  const groups = new Map();
  for (const row of teamRows) {
    const key = row.orgHead || null;
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(row);
  }
  return Array.from(groups.entries())
    .sort(([a], [b]) => {
      if (a === null) return 1;
      if (b === null) return -1;
      return a.localeCompare(b);
    })
    .map(([orgHead, rows]) => ({
      orgHead: orgHead || 'No reporting chain',
      rows: rows.slice().sort(compareRowsBySeverityThenName),
      hasAction: rows.some((r) => r.needsAction),
    }));
}

function referenceCandidatesForTeam(teamName) {
  const normalized = normalizeKey(teamName);
  const pieces = String(teamName || '').split(/[^\w-]+/).map(normalizeKey);
  return Array.from(new Set([normalized, ...pieces]))
    .filter((candidate) => candidate.length >= 4 && !['team', 'owner', 'workflows'].includes(candidate));
}

function referencesForTeams(outsideReferences, teamNames) {
  const candidates = teamNames.flatMap(referenceCandidatesForTeam);
  if (candidates.length === 0) return [];

  return outsideReferences.filter((item) => {
    const haystack = [
      item.file,
      item.token,
      item.type,
      normalizeKey(item.file),
      normalizeKey(item.token),
    ].join(' ').toLowerCase();
    return candidates.some((candidate) => haystack.includes(candidate));
  });
}

function renderFileLink(label, filePath, code = false) {
  if (!filePath) return escapeHtml(label);
  const href = pathToFileURL(filePath).href;
  const content = code ? `<code>${escapeHtml(label)}</code>` : escapeHtml(label);
  return `<a href="${escapeHtml(href)}">${content}</a>`;
}

function renderRepoFileLink(repoRoot, relPath, githubBaseUrl) {
  if (!repoRoot || !relPath) return escapeHtml(relPath || '');
  if (githubBaseUrl) {
    const encoded = relPath.split('/').map(encodeURIComponent).join('/');
    return `<a href="${escapeHtml(githubBaseUrl + '/blob/master/' + encoded)}">${escapeHtml(relPath)}</a>`;
  }
  return renderFileLink(relPath, path.join(repoRoot, relPath));
}

function renderReferenceDetails(references, repoRoot, githubBaseUrl, expanded = false) {
  if (references.length === 0) {
    return '';
  }

  const counts = countByType(references);
  const countText = Object.entries(counts).map(([type, count]) => `${type}: ${count}`).join(', ');
  const openAttr = expanded ? ' open' : '';
  return `<details class="ref-details"${openAttr}><summary>Metadata refs: ${escapeHtml(countText)}</summary>${renderList(references, (item) => `${renderRepoFileLink(repoRoot, item.file, githubBaseUrl)}: <code>${escapeHtml(item.token)}</code>`)}</details>`;
}

function defaultCachePath(repoRoot) {
  return path.join(os.tmpdir(), `update-devteams-progress-history-${normalizeKey(repoRoot) || 'repo'}.json`);
}

function todayIsoDate() {
  return new Date().toISOString().slice(0, 10);
}

function goalDateFrom(startDate, days) {
  const date = new Date(`${startDate}T00:00:00.000Z`);
  date.setUTCDate(date.getUTCDate() + days);
  return date.toISOString().slice(0, 10);
}

function updateProgressCache(cachePath, snapshot) {
  const history = readJsonIfPresent(cachePath, []);
  const nextHistory = Array.isArray(history) ? history.filter((item) => item.date !== snapshot.date) : [];
  nextHistory.push(snapshot);
  nextHistory.sort((a, b) => String(a.date).localeCompare(String(b.date)));
  fs.mkdirSync(path.dirname(cachePath), { recursive: true });
  fs.writeFileSync(cachePath, `${JSON.stringify(nextHistory, null, 2)}\n`);
  return nextHistory;
}

function dateRangeEnding(endDate, days) {
  const end = new Date(`${endDate}T00:00:00.000Z`);
  const dates = [];
  for (let offset = days - 1; offset >= 0; offset -= 1) {
    const date = new Date(end);
    date.setUTCDate(end.getUTCDate() - offset);
    dates.push(date.toISOString().slice(0, 10));
  }
  return dates;
}

function commitHistoryLastDays(repoRoot, endDate, days) {
  const dates = dateRangeEnding(endDate, days);
  const counts = new Map(dates.map((date) => [date, 0]));
  if (!fs.existsSync(path.join(repoRoot, '.git'))) {
    return dates.map((date) => ({ date, commits: 0 }));
  }
  try {
    const since = dates[0];
    const output = execFileSync(
      'git',
      ['log', `--since=${since}T00:00:00Z`, '--date=short', '--pretty=format:%ad', '--', 'apollo-dev-teams.yml'],
      { cwd: repoRoot, encoding: 'utf8' },
    );
    for (const line of output.split('\n').map((item) => item.trim()).filter(Boolean)) {
      if (counts.has(line)) counts.set(line, counts.get(line) + 1);
    }
  } catch {
    // Keep zero-count dates when git history is unavailable, such as isolated test fixtures.
  }
  return dates.map((date) => ({ date, commits: counts.get(date) || 0 }));
}

function detectGithubBaseUrl(repoRoot) {
  try {
    const remote = execFileSync('git', ['remote', 'get-url', 'origin'], { cwd: repoRoot, encoding: 'utf8' }).trim();
    const ssh = remote.match(/git@github\.com:(.+?)(?:\.git)?$/);
    if (ssh) return `https://github.com/${ssh[1]}`;
    const https = remote.match(/(https:\/\/github\.com\/.+?)(?:\.git)?$/);
    if (https) return https[1];
  } catch {}
  return null;
}

function renderCommitHistorySvg(history) {
  const width = 720;
  const height = 190;
  const padding = 34;
  const maxCommits = Math.max(1, ...history.map((item) => item.commits));
  const barWidth = (width - padding * 2) / Math.max(history.length, 1) - 8;
  const bars = history.map((item, index) => {
    const x = padding + index * ((width - padding * 2) / Math.max(history.length, 1)) + 4;
    const barHeight = (item.commits / maxCommits) * (height - padding * 2);
    const y = height - padding - barHeight;
    return `<rect x="${x.toFixed(1)}" y="${y.toFixed(1)}" width="${Math.max(barWidth, 6).toFixed(1)}" height="${barHeight.toFixed(1)}"><title>${escapeHtml(item.date)}: ${item.commits} commit(s)</title></rect>
      <text x="${(x + Math.max(barWidth, 6) / 2).toFixed(1)}" y="${height - 8}" text-anchor="middle">${escapeHtml(item.date.slice(5))}</text>
      <text x="${(x + Math.max(barWidth, 6) / 2).toFixed(1)}" y="${Math.max(y - 6, 12).toFixed(1)}" text-anchor="middle">${item.commits}</text>`;
  }).join('');

  return `<svg class="chart" viewBox="0 0 ${width} ${height}" role="img" aria-label="Last 10 days of apollo-dev-teams.yml commit history">
    <line x1="${padding}" y1="${padding}" x2="${padding}" y2="${height - padding}" />
    <line x1="${padding}" y1="${height - padding}" x2="${width - padding}" y2="${height - padding}" />
    ${bars}
  </svg>`;
}

function renderReport(report, outsideReferences, options = {}) {
  const plan = buildChangePlan(report, outsideReferences);
  const teamRows = options.teamRows || [];
  const progress = options.progress || { completionPct: 0, completeTeams: 0, totalTeams: report.totalTeams, actionTeams: 0, warningTeams: 0 };
  const goalDate = options.goalDate || goalDateFrom(todayIsoDate(), DEFAULT_PROJECT_DAYS);
  const lines = [
    '# Dev Teams Report',
    '',
    `Goal: get Apollo engineering team metadata to 100% non-red by ${goalDate}.`,
    '',
    '## Executive Summary',
    '',
    `- Progress: ${progress.completionPct}% (${progress.completeTeams}/${progress.totalTeams} teams have no red known-drift item from this scan).`,
    `- Scanned ${report.totalTeams} YAML teams; ${report.healthy.length} look healthy/current.`,
    `- Found ${report.renameCleanup.length} rename-cleanup bucket, ${report.ghostTeams.length} dissolved-team bucket(s), and ${outsideReferences.length} outside metadata references to review.`,
    '- Recommended change-management path: start with verified metadata-only PRs, then handle ownership transfers separately.',
    '- Do not delete or rename teams with active ownership until the replacement owner is confirmed.',
    '',
  ];

  const staleSignals = staleKnownSignals(options.snapshotDate);
  if (staleSignals.length) {
    lines.push(
      `> ⚠️ ${staleSignals.length} curated cleanup signal(s) are over ${KNOWN_SIGNALS_STALE_AFTER_DAYS} days old and may be stale — re-verify and bump \`reviewed\`: ${staleSignals.map((s) => `${s.label} (${s.ageDays}d)`).join(', ')}.`,
      '',
    );
  }

  lines.push(
    '## Teams to Coordinate With',
    '',
    ...(plan.coordination.length
      ? plan.coordination.map((item) => `- ${item.area}: ${item.action}`)
      : ['- None. No team-specific coordination was detected.']),
    '',
    '## Work Buckets',
    '',
    `- Rename cleanup: ${teamList(report.renameCleanup).join(', ') || 'none'}`,
    `- Slack verification: ${report.slackIssues.length} field(s)`,
    `- On-call verification: ${report.onCallIssues.length} handle(s)`,
    `- Ghost/dissolved triage: ${teamList(report.ghostTeams).join(', ') || 'none'}`,
    `- Member metadata cleanup: ${teamList(report.memberIssues).join(', ') || 'none'}`,
    `- Outside reference drift: ${Object.entries(plan.outsideTypes).map(([type, count]) => `${type}=${count}`).join(', ') || 'none'}`,
    '',
  );

  lines.push(
    '## Team Action Table',
    '',
    '| Team | EM | Status | Action |',
    '| --- | --- | --- | --- |',
    ...teamRows.map((row) => `| ${row.needsAction ? 'ACTION: ' : ''}${row.name} | ${row.em} | ${row.status} | ${row.action} |`),
    '',
  );

  lines.push(
    '## Appendix: Engineering Org Changes',
    '',
    `Source: ${DISBANDED_TEAMS_SOURCE}`,
    '',
    '| Former Team | Successor / Destination | Notes |',
    '| --- | --- | --- |',
    ...DISBANDED_TEAMS.map((d) => `| ${d.team} | ${d.successor} | ${d.note} |`),
    '',
  );

  return `${lines.join('\n')}\n`;
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function renderList(items, renderItem) {
  if (items.length === 0) return '<p class="muted">None</p>';
  return `<ul>${items.map((item) => `<li>${renderItem(item)}</li>`).join('')}</ul>`;
}

function renderReportHtml(report, outsideReferences, options = {}) {
  const teamRows = options.teamRows || [];
  const actionRows = teamRows.filter((row) => row.needsAction).sort(compareRowsBySeverityThenName);
  const healthyRows = teamRows.filter((row) => !row.needsAction);
  const actionByManager = groupActionRowsByManager(actionRows);
  const progress = options.progress || { completionPct: 0, completeTeams: 0, totalTeams: report.totalTeams, actionTeams: 0, warningTeams: 0 };
  const commitHistory = options.commitHistory || [];
  const goalDate = options.goalDate || goalDateFrom(todayIsoDate(), DEFAULT_PROJECT_DAYS);
  const snapshotDate = options.snapshotDate || todayIsoDate();
  const remainingDays = daysBetween(snapshotDate, goalDate);
  const repoRoot = options.repoRoot || '';
  const teamsPath = options.teamsPath || '';
  const githubBaseUrl = options.githubBaseUrl || null;
  const primaryActionGroups = actionByManager.slice(0, 6);
  const remainingActionGroups = Math.max(actionByManager.length - primaryActionGroups.length, 0);
  const orgGroups = groupRowsByOrgHead(teamRows);

  const bucketFilters = [
    { key: 'rename', label: `rename: ${teamList(report.renameCleanup).length}` },
    { key: 'legacy', label: `dissolved: ${teamList(report.ghostTeams).length}` },
    { key: 'members', label: `members: ${teamList(report.memberIssues).length}` },
    { key: 'oncall', label: `slack/on-call: ${report.slackIssues.length + report.onCallIssues.length}` },
    { key: 'sentry', label: `sentry: ${report.sentryIssues.length}` },
    { key: 'refs', label: `outside refs: ${outsideReferences.length}` },
  ];

  function rowBuckets(teamName) {
    const b = [];
    if (report.renameCleanup.some((i) => i.team === teamName)) b.push('rename');
    if (report.ghostTeams.some((i) => i.team === teamName)) b.push('legacy');
    if (report.memberIssues.some((i) => i.team === teamName)) b.push('members');
    if (report.slackIssues.some((i) => i.team === teamName) || report.onCallIssues.some((i) => i.team === teamName)) b.push('oncall');
    if (report.sentryIssues.some((i) => i.team === teamName)) b.push('sentry');
    if (referencesForTeams(outsideReferences, [teamName]).length > 0) b.push('refs');
    return b;
  }

  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Dev Teams Report</title>
  <style>
    body { color: #17202a; font: 14px/1.36 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 0; background: #f7f8fa; }
    main { max-width: 1120px; margin: 0 auto; padding: 18px 20px 36px; }
    h1, h2, h3 { line-height: 1.2; margin: 0 0 12px; }
    h1 { font-size: 28px; }
    h2 { font-size: 18px; margin-top: 0; }
    h3 { font-size: 15px; margin-top: 18px; }
    .nudge-card { background: #fff; border: 1px solid #d7dde5; border-radius: 8px; box-shadow: 0 10px 28px rgba(16, 24, 40, 0.08); margin: 0 auto 14px; max-width: 1040px; min-height: 640px; padding: 22px 26px; }
    .nudge-head { display: flex; justify-content: space-between; gap: 20px; align-items: flex-start; border-bottom: 1px solid #e8ebef; padding-bottom: 14px; }
    .nudge-head p { margin: 0; }
    .score { text-align: right; min-width: 160px; }
    .score strong { display: block; font-size: 46px; line-height: 1; }
    .grid { display: grid; gap: 10px; grid-template-columns: repeat(4, 1fr); margin: 14px 0; }
    .metric { border-left: 3px solid #2454d6; padding: 6px 10px; }
    .metric strong { display: block; font-size: 22px; }
    .nudge-layout { display: grid; gap: 18px; grid-template-columns: 1.15fr 0.85fr; align-items: start; }
    .nudge-list { display: grid; gap: 7px; grid-template-columns: repeat(2, minmax(0, 1fr)); margin: 0; padding: 0; }
    .nudge-item { border-radius: 8px; list-style: none; min-height: 44px; padding: 8px 9px; }
    .nudge-item.action { background: #fff7f6; border: 1px solid #f0c1bd; }
    .nudge-item.warning { background: #fff8e6; border: 1px solid #f3d27a; }
    .nudge-item strong { display: block; }
    .bucket-row { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px; }
    .section { background: #fff; border: 1px solid #dfe3e8; border-radius: 8px; margin-top: 14px; padding: 16px; }
    .muted { color: #667085; }
    .pill { display: inline-block; border: 1px solid #cfd6dd; border-radius: 999px; padding: 3px 8px; white-space: nowrap; font-size: 12px; }
    .pill-btn { background: #f7f8fa; border: 1px solid #cfd6dd; border-radius: 999px; cursor: pointer; font: 12px/1 inherit; padding: 3px 8px; white-space: nowrap; }
    .pill-btn:hover { background: #e8ebef; }
    .pill-btn.active { background: #2454d6; border-color: #2454d6; color: #fff; }
    .pill-btn[data-severity="action"].active { background: #c0392b; border-color: #c0392b; }
    .pill-btn[data-severity="warning"].active { background: #c97d10; border-color: #c97d10; }
    .pill-btn[data-severity="ok"].active { background: #1e7e34; border-color: #1e7e34; }
    .filter-label { color: #667085; font-size: 11px; align-self: center; margin-right: 2px; }
    tr.hidden { display: none; }
    .thanks { background: #eefaf1; border: 1px solid #b7e2c2; border-radius: 8px; margin-top: 14px; padding: 10px 12px; }
    .skill-line { background: #f8fafc; border: 1px solid #dfe3e8; border-radius: 8px; margin: 10px 0 0; padding: 9px 11px; }
    details { border-top: 1px solid #e8ebef; padding-top: 12px; margin-top: 12px; }
    .ref-details { border-top: 0; margin-top: 7px; padding-top: 0; }
    .ref-details summary { color: #475467; font-size: 12px; font-weight: 500; }
    a { color: #2454d6; text-decoration: none; }
    a:hover { text-decoration: underline; }
    summary { cursor: pointer; font-weight: 600; }
    code { background: #f1f3f5; border-radius: 4px; padding: 1px 4px; }
    ul, ol { padding-left: 22px; }
    table { border-collapse: collapse; width: 100%; }
    th, td { border-bottom: 1px solid #e8ebef; padding: 7px 8px; text-align: left; vertical-align: top; }
    th { background: #f8fafc; font-size: 12px; text-transform: uppercase; color: #475467; }
    tr.action { background: #fff1f0; }
    tr.warning { background: #fff8e6; }
    tr.ok { background: #fbfdfb; }
    .callout { background: #eefaf1; border: 1px solid #b7e2c2; border-radius: 8px; padding: 12px; }
    .chart { width: 100%; max-width: 760px; height: auto; margin-top: 8px; }
    .chart line { stroke: #c8d0d9; stroke-width: 1; }
    .chart rect { fill: #2454d6; rx: 3; }
    .chart text { fill: #667085; font-size: 11px; }
    @media (max-width: 760px) {
      .nudge-head, .nudge-layout { display: block; }
      .score { text-align: left; margin-top: 14px; }
      .grid { grid-template-columns: repeat(2, 1fr); }
    }
  </style>
</head>
<body>
  <main>
    <section class="nudge-card">
      <div class="nudge-head">
        <div>
          <h1>Dev Teams Report</h1>
          <p class="muted">${githubBaseUrl ? `<a href="${escapeHtml(githubBaseUrl + '/blob/master/apollo-dev-teams.yml')}"><code>apollo-dev-teams.yml</code></a>` : renderFileLink('apollo-dev-teams.yml', teamsPath, true)} health snapshot for dashboards, ownership, on-call, and routing metadata.</p>
        </div>
        <div class="score">
          <strong>${progress.completionPct}%</strong>
          <span>not red</span>
        </div>
      </div>

      <div class="grid">
        <div class="metric"><strong>${progress.completeTeams}/${progress.totalTeams}</strong><span>not red</span></div>
        <div class="metric"><strong>${progress.actionTeams}</strong><span>red</span></div>
        <div class="metric"><strong>${progress.warningTeams || 0}</strong><span>yellow</span></div>
        <div class="metric"><strong>${outsideReferences.length}</strong><span>outside refs</span></div>
      </div>

      <div class="nudge-layout">
        <div>
          <h2>Nudge Focus</h2>
          <ul class="nudge-list">
            ${primaryActionGroups.map((group) => `<li class="nudge-item ${escapeHtml(group.severity)}">
              <strong>${escapeHtml(group.manager)}</strong>
              <span>${escapeHtml(group.teams.join(', '))}</span>
            </li>`).join('')}
          </ul>
          ${remainingActionGroups ? `<p class="muted">+ ${remainingActionGroups} more owner group(s) in details.</p>` : ''}
          <div class="thanks">${healthyRows.length} teams need no nudge. Thanks for keeping metadata current.</div>
        </div>
        <div>
          <h2>Open Buckets</h2>
          <div class="bucket-row" id="severity-filters">
            <span class="filter-label">Status:</span>
            <button class="pill-btn" data-severity="action">🔴 Red</button>
            <button class="pill-btn" data-severity="warning">🟡 Yellow</button>
            <button class="pill-btn" data-severity="ok">✅ No action</button>
          </div>
          <div class="bucket-row" id="bucket-filters"><span class="filter-label">Bucket:</span>${bucketFilters.map((b) => `<button class="pill-btn" data-filter="${escapeHtml(b.key)}">${escapeHtml(b.label)}</button>`).join('')}</div>
          <h2 style="margin-top: 18px;">10-Day Activity</h2>
          ${renderCommitHistorySvg(commitHistory)}
        </div>
      </div>
      <p class="muted">Target: 100% non-red by ${escapeHtml(goalDate)} (${remainingDays} days left).</p>
      <p class="skill-line"><strong>Try update mode:</strong> <code>/apollo-eng-leadership:update-devteams update --file scripts/performance-notification/metrics/plays-fe.ts --replace-text oncall-plays-fe=oncall-confirmed-owner --write</code></p>
    </section>

    <section class="section">
      <h2>Teams by Org</h2>
      ${orgGroups.map(({orgHead, rows, hasAction}) => {
        const actionCount = rows.filter((r) => r.needsAction).length;
        const healthyCount = rows.length - actionCount;
        const label = actionCount > 0
          ? `${escapeHtml(orgHead)} — ${actionCount} need${actionCount === 1 ? 's' : ''} action, ${healthyCount} healthy`
          : `${escapeHtml(orgHead)} — all ${healthyCount} healthy`;
        return `<details${hasAction ? ' open' : ''}>
        <summary>${label}</summary>
        <table>
          <thead><tr><th>Team</th><th>EM</th><th>Action</th></tr></thead>
          <tbody>
            ${rows.map((row) => {
              const rb = rowBuckets(row.name);
              const actionCell = row.needsAction
                ? escapeHtml(row.action) + renderReferenceDetails(referencesForTeams(outsideReferences, [row.name]), repoRoot, githubBaseUrl, row.severity === 'action')
                : '<span class="muted">No action needed</span>';
              return `<tr class="${escapeHtml(row.severity)}" data-buckets="${escapeHtml(rb.join(' '))}">
                <td><strong>${escapeHtml(row.name)}</strong></td>
                <td>${escapeHtml(row.em)}</td>
                <td>${actionCell}</td>
              </tr>`;
            }).join('')}
          </tbody>
        </table>
      </details>`;
      }).join('')}
    </section>
  ${renderDisbandedTeamsAppendix()}
  </main>
  <script>
    (function () {
      var activeBuckets = new Set();
      var activeSeverities = new Set();
      var tables = document.querySelectorAll('table');

      function applyFilter() {
        var anyFilter = activeBuckets.size > 0 || activeSeverities.size > 0;
        tables.forEach(function (tbl) {
          tbl.querySelectorAll('tbody tr').forEach(function (tr) {
            if (!anyFilter) { tr.classList.remove('hidden'); return; }
            var bucketMatch = activeBuckets.size === 0 || (function () {
              var buckets = (tr.getAttribute('data-buckets') || '').split(' ');
              return Array.from(activeBuckets).some(function (f) { return buckets.includes(f); });
            })();
            var severityMatch = activeSeverities.size === 0 || activeSeverities.has(tr.className.split(' ')[0]);
            tr.classList.toggle('hidden', !(bucketMatch && severityMatch));
          });
        });
        document.querySelectorAll('details').forEach(function (d) {
          if (anyFilter) d.open = true;
        });
      }

      document.querySelectorAll('#bucket-filters .pill-btn').forEach(function (btn) {
        btn.addEventListener('click', function () {
          var key = btn.getAttribute('data-filter');
          if (activeBuckets.has(key)) { activeBuckets.delete(key); btn.classList.remove('active'); }
          else { activeBuckets.add(key); btn.classList.add('active'); }
          applyFilter();
        });
      });

      document.querySelectorAll('#severity-filters .pill-btn').forEach(function (btn) {
        btn.addEventListener('click', function () {
          var key = btn.getAttribute('data-severity');
          if (activeSeverities.has(key)) { activeSeverities.delete(key); btn.classList.remove('active'); }
          else { activeSeverities.add(key); btn.classList.add('active'); }
          applyFilter();
        });
      });
    })();
  </script>
</body>
</html>
`;
}

function renderDisbandedTeamsAppendix() {
  const rows = DISBANDED_TEAMS.map((d) => `<tr>
    <td><strong>${escapeHtml(d.team)}</strong></td>
    <td>${escapeHtml(d.successor)}</td>
    <td class="muted">${escapeHtml(d.note)}</td>
  </tr>`).join('');
  return `
    <section class="section">
      <details>
        <summary>Appendix: Engineering Org Changes</summary>
        <p class="muted">Teams that have been disbanded or merged since the reorg. Source: <a href="${escapeHtml(DISBANDED_TEAMS_SOURCE)}" target="_blank" rel="noopener">R&amp;D Org History spreadsheet</a>.</p>
        <table>
          <thead><tr><th>Former Team</th><th>Successor / Destination</th><th>Notes</th></tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </details>
    </section>`;
}

function parseSetExpression(expression) {
  const eqIndex = expression.indexOf('=');
  if (eqIndex < 0) throw new Error(`Invalid --set expression "${expression}". Use TEAM.field=value.`);
  const left = expression.slice(0, eqIndex);
  const value = expression.slice(eqIndex + 1);
  const dotIndex = left.indexOf('.');
  if (dotIndex < 0) throw new Error(`Invalid --set target "${left}". Use TEAM.field=value.`);
  const team = left.slice(0, dotIndex);
  const fieldPath = left.slice(dotIndex + 1).split('.');
  if (!team || fieldPath.some((part) => !part)) throw new Error(`Invalid --set target "${left}".`);
  return { team, fieldPath, value };
}

function yamlSingleQuoted(value) {
  return `'${String(value).replace(/'/g, "''")}'`;
}

function findTeamBlock(source, teamName) {
  const lines = source.split('\n');
  const teamPattern = new RegExp(`^  - name: ['"]?${teamName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}['"]?\\s*$`);
  const start = lines.findIndex((line) => teamPattern.test(line));
  if (start < 0) return null;
  let end = lines.length;
  for (let index = start + 1; index < lines.length; index += 1) {
    if (/^  - name: /.test(lines[index])) {
      end = index;
      break;
    }
  }
  return { lines, start, end };
}

function setYamlValueInSource(source, expression) {
  const { team, fieldPath, value } = parseSetExpression(expression);
  if (fieldPath.length !== 1) {
    throw new Error(`Nested --set paths are not supported by the shared helper: ${team}.${fieldPath.join('.')}`);
  }
  const block = findTeamBlock(source, team);
  if (!block) throw new Error(`Team "${team}" not found in apollo-dev-teams.yml`);
  const { lines, start, end } = block;
  const field = fieldPath[0];
  const fieldPattern = new RegExp(`^(    ${field.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}: ).*$`);
  for (let index = start + 1; index < end; index += 1) {
    if (fieldPattern.test(lines[index])) {
      lines[index] = lines[index].replace(fieldPattern, `$1${yamlSingleQuoted(value)}`);
      return { source: lines.join('\n'), summary: `set ${team}.${field}=${value}` };
    }
  }
  lines.splice(start + 1, 0, `    ${field}: ${yamlSingleQuoted(value)}`);
  return { source: lines.join('\n'), summary: `set ${team}.${field}=${value}` };
}

function removeEmptyMembersFromSource(source, teamFilter) {
  const removed = [];
  let lines = source.split('\n');
  const teamStarts = lines
    .map((line, index) => (/^  - name: /.test(line) ? index : -1))
    .filter((index) => index >= 0);
  for (let teamIndex = teamStarts.length - 1; teamIndex >= 0; teamIndex -= 1) {
    const start = teamStarts[teamIndex];
    const end = teamIndex + 1 < teamStarts.length ? teamStarts[teamIndex + 1] : lines.length;
    const match = lines[start].match(/^  - name: ['"]?([^'"]+)['"]?\s*$/);
    const teamName = match?.[1];
    if (!teamName || (teamFilter && teamName !== teamFilter)) continue;

    for (let index = end - 1; index > start; index -= 1) {
      if (!/^      - /.test(lines[index])) continue;
      let itemEnd = end;
      for (let next = index + 1; next < end; next += 1) {
        if (/^      - /.test(lines[next])) {
          itemEnd = next;
          break;
        }
      }
      const block = lines.slice(index, itemEnd);
      const joined = block.join('\n');
      const blankGithub = /^      - github: ['"]{0,2}\s*$/m.test(joined);
      const blankName = /^        name: ['"]{0,2}\s*$/m.test(joined);
      const blankEmail = /^        email: ['"]{0,2}\s*$/m.test(joined);
      const allowed = block.every((line, lineIndex) => {
        if (lineIndex === 0) return /^      - github:/.test(line);
        return /^        (name|email):/.test(line) || /^\s*$/.test(line);
      });
      if (blankGithub && blankName && blankEmail && allowed) {
        lines.splice(index, itemEnd - index);
        removed.push(`removed empty member ${teamName}.members`);
      }
    }
  }

  return { source: lines.join('\n'), removed };
}

function replaceText(filePath, expression) {
  const eqIndex = expression.indexOf('=');
  if (eqIndex < 0) throw new Error(`Invalid --replace-text expression "${expression}". Use OLD=NEW.`);
  const oldValue = expression.slice(0, eqIndex);
  const newValue = expression.slice(eqIndex + 1);
  if (!oldValue || !newValue) throw new Error('--replace-text requires non-empty OLD and NEW values.');
  const source = fs.readFileSync(filePath, 'utf8');
  const count = source.split(oldValue).length - 1;
  if (count === 0) return { changed: false, output: source, summary: `${filePath}: no occurrences of ${oldValue}` };
  return {
    changed: true,
    output: source.split(oldValue).join(newValue),
    summary: `${filePath}: replaced ${count} occurrence(s) of ${oldValue} with ${newValue}`,
  };
}

function commandReport(args) {
  const repoRoot = path.resolve(args['repo-root'] || process.cwd());
  const teamsPath = path.resolve(repoRoot, args.teams || 'apollo-dev-teams.yml');
  const { teams } = readTeams(teamsPath);
  const channelStatus = readStatusJson(args['slack-channel-status-json']);
  const usergroupStatus = readStatusJson(args['usergroup-status-json']);
  const report = assessTeams(teams, channelStatus, usergroupStatus);
  const outsideReferences = scanOutsideReferences(repoRoot, teamsPath, teams);
  const teamRows = buildTeamRows(teams, report, outsideReferences);
  const progress = progressFromRows(teamRows, report.totalTeams);
  const snapshotDate = args.date || todayIsoDate();
  const goalDate = args['goal-date'] || goalDateFrom(snapshotDate, Number(args['goal-days'] || DEFAULT_PROJECT_DAYS));
  const cachePath = args.cache === false ? null : (args.cache || defaultCachePath(repoRoot));
  const snapshot = {
    date: snapshotDate,
    totalTeams: progress.totalTeams,
    completeTeams: progress.completeTeams,
    actionTeams: progress.actionTeams,
    warningTeams: progress.warningTeams,
    completionPct: progress.completionPct,
    outsideReferences: outsideReferences.length,
  };
  const history = cachePath && !args['no-cache'] ? updateProgressCache(cachePath, snapshot) : [snapshot];
  const commitHistory = commitHistoryLastDays(repoRoot, snapshotDate, 10);
  const githubBaseUrl = args['github-base-url'] || detectGithubBaseUrl(repoRoot);
  const renderOptions = {
    teamRows,
    progress,
    history,
    commitHistory,
    cachePath: cachePath || 'cache disabled',
    goalDate,
    snapshotDate,
    repoRoot,
    teamsPath: path.resolve(teamsPath),
    githubBaseUrl,
  };
  if (args.html) {
    const html = renderReportHtml(report, outsideReferences, renderOptions);
    if (args.html === true) {
      process.stdout.write(html);
    } else {
      fs.writeFileSync(args.html, html);
      process.stdout.write(`Wrote HTML report to ${args.html}\n`);
    }
    return;
  }
  process.stdout.write(renderReport(report, outsideReferences, renderOptions));
}

function commandUpdate(args) {
  const write = Boolean(args.write);
  const summaries = [];
  let yamlChanged = false;

  if (args.teams && (args.set || args['remove-empty-members'])) {
    const source = fs.readFileSync(args.teams, 'utf8');
    let output = source;
    for (const expression of asArray(args.set)) {
      const result = setYamlValueInSource(output, expression);
      output = result.source;
      summaries.push(result.summary);
      yamlChanged = true;
    }
    if (args['remove-empty-members']) {
      const result = removeEmptyMembersFromSource(output, args.team);
      output = result.source;
      const removed = result.removed;
      summaries.push(...removed);
      yamlChanged = yamlChanged || removed.length > 0;
    }
    if (yamlChanged) {
      assertValidYaml(output);
      if (write) fs.writeFileSync(args.teams, output);
      summaries.push(`${write ? 'wrote' : 'dry-run'} ${args.teams} (${source.length} -> ${output.length} bytes)`);
    }
  }

  const files = asArray(args.file);
  const replacements = asArray(args['replace-text']);
  if (replacements.length > 0 && files.length === 0) {
    throw new Error('--replace-text requires at least one --file path.');
  }
  for (const file of files) {
    for (const expression of replacements) {
      const result = replaceText(file, expression);
      summaries.push(result.summary);
      if (result.changed && write) fs.writeFileSync(file, result.output);
    }
  }

  if (summaries.length === 0) {
    throw new Error('No update operation requested. Use --set, --replace-text, or --remove-empty-members.');
  }

  process.stdout.write(`${write ? 'Applied updates' : 'Dry run only; pass --write to modify files'}\n`);
  for (const summary of summaries) process.stdout.write(`- ${summary}\n`);
}

function main() {
  const [command, ...rest] = process.argv.slice(2);
  const args = parseArgs(rest);

  try {
    if (command === 'report') {
      commandReport(args);
    } else if (command === 'update') {
      commandUpdate(args);
    } else {
      process.stderr.write('Usage: update-devteams.js <report|update> [options]\n');
      process.exitCode = 2;
    }
  } catch (error) {
    process.stderr.write(`ERROR: ${error.message}\n`);
    process.exitCode = 1;
  }
}

if (require.main === module) {
  main();
}

module.exports = {
  assertValidYaml,
  assessTeams,
  parseArgs,
  renderReport,
  renderReportHtml,
  scanOutsideReferences,
  staleKnownSignals,
};
