#!/usr/bin/env node

import { pathToFileURL } from 'node:url';

const CANONICAL_REPOSITORY = 'jeremylongshore/tons-of-skills-marketplace';
const TRUSTED_APP_SLUG = 'github-actions';
const SUCCESS_CONCLUSION = 'success';

export const REQUIRED_CHECKS = Object.freeze([
  {
    context: 'ci-required',
    workflowName: 'Validate Plugins',
    workflowPath: '.github/workflows/validate-plugins.yml',
  },
  {
    context: 'gitleaks',
    workflowName: 'Secret Scan',
    workflowPath: '.github/workflows/secret-scan.yml',
  },
  {
    context: 'skill-conform',
    workflowName: 'Skill Conform',
    workflowPath: '.github/workflows/skill-conform.yml',
  },
]);

const PENDING_STATUSES = new Set(['queued', 'in_progress', 'waiting', 'requested', 'pending']);

function runIdFromUrl(url) {
  const match = String(url ?? '').match(/\/actions\/runs\/(\d+)/);
  return match ? Number(match[1]) : null;
}

function attemptKey(run, checkRun) {
  return [
    Number(run?.run_attempt ?? 0),
    Date.parse(run?.updated_at ?? run?.created_at ?? checkRun?.completed_at ?? '') || 0,
  ];
}

function compareKeys(a, b) {
  for (let i = 0; i < a.length; i += 1) {
    if (a[i] !== b[i]) return a[i] - b[i];
  }
  return 0;
}

function trustedWorkflowRun(run, requirement, repository, sha) {
  return (
    run?.name === requirement.workflowName &&
    run?.path === requirement.workflowPath &&
    run?.event === 'push' &&
    run?.head_branch === 'main' &&
    run?.head_sha === sha &&
    run?.repository?.full_name === repository
  );
}

function producer(run, checkRun, source = 'check-run') {
  return {
    source,
    app: checkRun?.app?.slug ?? null,
    workflowName: run?.name ?? null,
    workflowPath: run?.path ?? null,
    repository: run?.repository?.full_name ?? null,
    event: run?.event ?? null,
    branch: run?.head_branch ?? null,
    runId: run?.id ?? runIdFromUrl(checkRun?.details_url),
  };
}

function diagnostic(reason, context, candidates = [], extra = {}) {
  return {
    context,
    decision: 'refuse',
    reason,
    candidates,
    ...extra,
  };
}

function selectLatest(candidates) {
  if (candidates.length === 0) return { ambiguous: false, selected: null };
  const sorted = [...candidates].sort((a, b) =>
    compareKeys(attemptKey(a.workflowRun, a.checkRun), attemptKey(b.workflowRun, b.checkRun)),
  );
  const latest = sorted.at(-1);
  const latestKey = attemptKey(latest.workflowRun, latest.checkRun);
  const sameAttempt = sorted.filter(
    (candidate) =>
      compareKeys(attemptKey(candidate.workflowRun, candidate.checkRun), latestKey) === 0,
  );
  if (sameAttempt.length !== 1) return { ambiguous: true, sameAttempt };
  return { ambiguous: false, selected: latest };
}

function checkRunCandidates(requirement, checkRuns, workflowRuns, repository, sha) {
  const exactName = checkRuns.filter((checkRun) => checkRun.name === requirement.context);
  const candidates = [];
  const rejected = [];

  for (const checkRun of exactName) {
    const runId = runIdFromUrl(checkRun.details_url);
    const workflowRun = workflowRuns.find((run) => Number(run.id) === runId);
    const exactSha = checkRun.head_sha === sha;
    const trustedApp = checkRun.app?.slug === TRUSTED_APP_SLUG;
    const trustedWorkflow = trustedWorkflowRun(workflowRun, requirement, repository, sha);
    const item = { checkRun, workflowRun, producer: producer(workflowRun, checkRun) };
    if (exactSha && trustedApp && trustedWorkflow) candidates.push(item);
    else
      rejected.push({
        ...item.producer,
        checkRunId: checkRun.id ?? null,
        headSha: checkRun.head_sha ?? null,
        reason: !exactSha
          ? 'SHA_MISMATCH'
          : !trustedApp
            ? 'UNTRUSTED_PRODUCER'
            : 'UNTRUSTED_WORKFLOW',
      });
  }

  return { candidates, rejected, exactName };
}

function statusCandidates(requirement, statuses, workflowRuns, repository, sha) {
  return statuses
    .filter((status) => status.context === requirement.context)
    .map((status) => {
      const runId = runIdFromUrl(status.target_url);
      const workflowRun = workflowRuns.find((run) => Number(run.id) === runId);
      return {
        status,
        workflowRun,
        producer: producer(
          workflowRun,
          { app: { slug: status.creator?.login ?? null }, details_url: status.target_url },
          'commit-status',
        ),
        trusted:
          status.creator?.login === 'github-actions[bot]' &&
          trustedWorkflowRun(workflowRun, requirement, repository, sha),
      };
    });
}

export function evaluateCheckEvidence({
  repository,
  sha,
  checkRuns = [],
  workflowRuns = [],
  statuses = [],
}) {
  const contexts = [];
  for (const requirement of REQUIRED_CHECKS) {
    const { candidates, rejected, exactName } = checkRunCandidates(
      requirement,
      checkRuns,
      workflowRuns,
      repository,
      sha,
    );
    const selected = selectLatest(candidates);

    if (selected.ambiguous) {
      contexts.push(
        diagnostic(
          'AMBIGUOUS_DUPLICATE_TRUSTED_RESULTS',
          requirement.context,
          selected.sameAttempt.map((item) => ({
            checkRunId: item.checkRun.id ?? null,
            runId: item.workflowRun?.id ?? runIdFromUrl(item.checkRun.details_url),
            conclusion: item.checkRun.conclusion ?? null,
          })),
        ),
      );
      continue;
    }

    if (selected.selected) {
      const { checkRun, workflowRun, producer: producerIdentity } = selected.selected;
      if (checkRun.status !== 'completed' || workflowRun?.status !== 'completed') {
        contexts.push(
          diagnostic('PENDING', requirement.context, [
            {
              checkRunId: checkRun.id ?? null,
              runId: workflowRun?.id ?? null,
              status: checkRun.status ?? workflowRun?.status ?? null,
              conclusion: checkRun.conclusion ?? workflowRun?.conclusion ?? null,
              producer: producerIdentity,
            },
          ]),
        );
      } else if (
        checkRun.conclusion !== SUCCESS_CONCLUSION ||
        workflowRun.conclusion !== SUCCESS_CONCLUSION
      ) {
        contexts.push(
          diagnostic('FAILED_OR_NON_SUCCESS', requirement.context, [
            {
              checkRunId: checkRun.id ?? null,
              runId: workflowRun?.id ?? null,
              status: checkRun.status,
              conclusion: checkRun.conclusion ?? workflowRun?.conclusion,
              producer: producerIdentity,
            },
          ]),
        );
      } else {
        contexts.push({
          context: requirement.context,
          decision: 'allow',
          reason: 'SUCCESS',
          status: checkRun.status,
          conclusion: checkRun.conclusion,
          selectedRunId: workflowRun.id,
          checkRunId: checkRun.id ?? null,
          producer: producerIdentity,
        });
      }
      continue;
    }

    const fallbackStatuses =
      exactName.length === 0
        ? statusCandidates(requirement, statuses, workflowRuns, repository, sha).filter(
            (item) => item.trusted,
          )
        : [];
    if (fallbackStatuses.length === 1) {
      const item = fallbackStatuses[0];
      if (
        item.status.state === 'success' &&
        item.workflowRun?.status === 'completed' &&
        item.workflowRun.conclusion === 'success'
      ) {
        contexts.push({
          context: requirement.context,
          decision: 'allow',
          reason: 'SUCCESS_COMMIT_STATUS',
          status: item.status.state,
          conclusion: item.status.state,
          selectedRunId: item.workflowRun.id,
          producer: item.producer,
        });
      } else if (PENDING_STATUSES.has(item.status.state)) {
        contexts.push(
          diagnostic('PENDING', requirement.context, [
            {
              status: item.status.state,
              producer: item.producer,
            },
          ]),
        );
      } else {
        contexts.push(
          diagnostic('FAILED_OR_NON_SUCCESS', requirement.context, [
            {
              status: item.status.state,
              producer: item.producer,
            },
          ]),
        );
      }
      continue;
    }

    if (fallbackStatuses.length > 1) {
      contexts.push(
        diagnostic(
          'AMBIGUOUS_DUPLICATE_TRUSTED_RESULTS',
          requirement.context,
          fallbackStatuses.map((item) => ({
            status: item.status.state,
            producer: item.producer,
          })),
        ),
      );
    } else if (exactName.some((checkRun) => PENDING_STATUSES.has(checkRun.status))) {
      contexts.push(diagnostic('PENDING', requirement.context));
    } else if (rejected.some((item) => item.reason === 'SHA_MISMATCH')) {
      contexts.push(diagnostic('SHA_MISMATCH', requirement.context, rejected));
    } else if (
      rejected.some(
        (item) => item.reason === 'UNTRUSTED_PRODUCER' || item.reason === 'UNTRUSTED_WORKFLOW',
      )
    ) {
      contexts.push(diagnostic('UNTRUSTED_PRODUCER', requirement.context, rejected));
    } else {
      contexts.push(diagnostic('MISSING', requirement.context));
    }
  }

  return {
    allow: contexts.every((context) => context.decision === 'allow'),
    sha,
    repository,
    requiredContexts: contexts,
  };
}

async function githubJson(fetchImpl, apiBase, token, endpoint) {
  const response = await fetchImpl(`${apiBase}/${endpoint}`, {
    headers: {
      Accept: 'application/vnd.github+json',
      Authorization: `Bearer ${token}`,
      'X-GitHub-Api-Version': '2022-11-28',
    },
  });
  const body = await response.json();
  if (!response.ok) throw new Error(`GitHub API ${response.status} for ${endpoint}`);
  return body;
}

async function collectEvidence({
  repository,
  sha,
  token,
  fetchImpl = fetch,
  apiBase = 'https://api.github.com',
}) {
  const [repoInfo, mainCommit, compare, checkData, workflowData, statusData] = await Promise.all([
    githubJson(fetchImpl, apiBase, token, `repos/${repository}`),
    githubJson(fetchImpl, apiBase, token, `repos/${repository}/commits/main`),
    githubJson(fetchImpl, apiBase, token, `repos/${repository}/compare/${sha}...main`),
    githubJson(
      fetchImpl,
      apiBase,
      token,
      `repos/${repository}/commits/${sha}/check-runs?per_page=100`,
    ),
    githubJson(
      fetchImpl,
      apiBase,
      token,
      `repos/${repository}/actions/runs?head_sha=${sha}&per_page=100`,
    ),
    githubJson(fetchImpl, apiBase, token, `repos/${repository}/commits/${sha}/status`),
  ]);
  const checks = evaluateCheckEvidence({
    repository,
    sha,
    checkRuns: checkData.check_runs ?? [],
    workflowRuns: workflowData.workflow_runs ?? [],
    statuses: statusData.statuses ?? [],
  });
  return {
    ...checks,
    canonicalRepository: repoInfo.full_name === repository && repository === CANONICAL_REPOSITORY,
    currentMainSha: mainCommit.sha ?? null,
    reachableFromMain: compare.status === 'ahead' || compare.status === 'identical',
    currentMainMatches: mainCommit.sha === sha,
    compareStatus: compare.status ?? null,
    checkObservedAt: new Date().toISOString(),
  };
}

function parseArgs(argv) {
  const args = {};
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg.startsWith('--')) {
      const key = arg.slice(2).replaceAll('-', '_');
      const next = argv[index + 1];
      if (!next || next.startsWith('--')) args[key] = true;
      else {
        args[key] = next;
        index += 1;
      }
    }
  }
  return args;
}

export async function runPreflight({
  repository,
  sha,
  token,
  timeoutSeconds = 120,
  pollSeconds = 5,
  fetchImpl = fetch,
  apiBase = 'https://api.github.com',
  sleepImpl = (ms) => new Promise((resolve) => setTimeout(resolve, ms)),
}) {
  if (repository !== CANONICAL_REPOSITORY) {
    return {
      allow: false,
      sha,
      repository,
      reason: 'NON_CANONICAL_REPOSITORY',
      requiredContexts: [],
    };
  }
  if (!/^[0-9a-f]{40}$/i.test(sha ?? '')) {
    return {
      allow: false,
      sha: sha ?? null,
      repository,
      reason: 'INVALID_SHA',
      requiredContexts: [],
    };
  }
  const deadline = Date.now() + timeoutSeconds * 1000;
  let evidence;
  while (true) {
    evidence = await collectEvidence({ repository, sha, token, fetchImpl, apiBase });
    if (
      evidence.allow &&
      evidence.canonicalRepository &&
      evidence.reachableFromMain &&
      evidence.currentMainMatches
    ) {
      return { ...evidence, allow: true, decision: 'allow' };
    }
    const retryable = evidence.requiredContexts.some(
      (context) => context.reason === 'MISSING' || context.reason === 'PENDING',
    );
    if (!retryable || Date.now() >= deadline) {
      return {
        ...evidence,
        allow: false,
        decision: 'refuse',
        reason: !evidence.currentMainMatches
          ? 'STALE_OR_MOVED_MAIN'
          : !evidence.reachableFromMain
            ? 'SHA_NOT_REACHABLE_FROM_MAIN'
            : 'REQUIRED_CHECKS_NOT_GREEN',
      };
    }
    await sleepImpl(Math.min(pollSeconds * 1000, Math.max(0, deadline - Date.now())));
  }
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const result = await runPreflight({
    repository: args.repo,
    sha: args.sha,
    token: args.token ?? process.env.GH_TOKEN ?? process.env.GITHUB_TOKEN,
    timeoutSeconds: Number(args.timeout_seconds ?? 120),
    pollSeconds: Number(args.poll_seconds ?? 5),
  });
  const output = JSON.stringify(result, null, 2);
  if (args.json) console.log(output);
  else {
    console.log(output);
    console.log(result.allow ? 'PRECHECK_ALLOW' : 'PRECHECK_REFUSE');
  }
  if (!result.allow) process.exitCode = 1;
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) await main();
