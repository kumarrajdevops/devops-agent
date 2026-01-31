/**
 * devops-agent (Phase 2)
 * Read-only CI/CD observer for GitHub Actions that posts a sticky PR comment.
 *
 * Trust constraints:
 * - No credential storage (uses GITHUB_TOKEN only)
 * - No mutations except PR comment
 * - No external network calls besides GitHub API
 */

const fs = require("fs");
const path = require("path");

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

function readOptionalConfigYaml(repoRoot) {
  // Minimal YAML reader for Phase 2 schema only.
  // Supported keys:
  // version: 1
  // github_actions:
  //   pr_comment:
  //     enabled: true|false
  //     mode: sticky
  //     post_on: failure|always
  const configPath = path.join(repoRoot, ".devops-agent.yml");
  if (!fs.existsSync(configPath)) return null;

  const raw = fs.readFileSync(configPath, "utf8");
  const lines = raw
    .split(/\r?\n/)
    .map((l) => l.replace(/\t/g, "  "))
    .filter((l) => l.trim() !== "" && !l.trim().startsWith("#"));

  // Extremely small “parser”: track indentation + key path, only scalar values.
  const root = {};
  const stack = [{ indent: -1, obj: root }];

  for (const line of lines) {
    const indent = line.match(/^ */)[0].length;
    const trimmed = line.trim();
    const m = trimmed.match(/^([A-Za-z0-9_]+):(?:\s+(.*))?$/);
    if (!m) continue;

    const key = m[1];
    let value = m[2];

    while (stack.length > 1 && indent <= stack[stack.length - 1].indent) {
      stack.pop();
    }
    const cur = stack[stack.length - 1].obj;

    if (value === undefined) {
      cur[key] = {};
      stack.push({ indent, obj: cur[key] });
      continue;
    }

    value = value.trim();
    if (value === "true") cur[key] = true;
    else if (value === "false") cur[key] = false;
    else if (/^\d+$/.test(value)) cur[key] = Number(value);
    else cur[key] = value;
  }

  return root;
}

function getConfig(repoRoot) {
  const defaults = {
    version: 1,
    github_actions: {
      pr_comment: {
        enabled: true,
        mode: "sticky",
        post_on: "failure", // failure|always
      },
    },
  };

  const cfg = readOptionalConfigYaml(repoRoot);
  if (!cfg) return defaults;

  // Shallow merge for the fields we care about.
  const out = JSON.parse(JSON.stringify(defaults));
  if (typeof cfg.version === "number") out.version = cfg.version;
  if (cfg.github_actions?.pr_comment) {
    const pc = cfg.github_actions.pr_comment;
    if (typeof pc.enabled === "boolean") out.github_actions.pr_comment.enabled = pc.enabled;
    if (typeof pc.mode === "string") out.github_actions.pr_comment.mode = pc.mode;
    if (typeof pc.post_on === "string") out.github_actions.pr_comment.post_on = pc.post_on;
  }
  return out;
}

function classifyFailure(stepName = "", jobName = "") {
  const hay = `${jobName}\n${stepName}`.toLowerCase();
  if (hay.includes("lint") || hay.includes("eslint") || hay.includes("flake8") || hay.includes("ruff")) {
    return { category: "lint", next: "Run the linter locally and fix the first reported violation." };
  }
  if (hay.includes("test") || hay.includes("pytest") || hay.includes("jest") || hay.includes("go test")) {
    return { category: "tests", next: "Re-run the failing test locally; check recent changes and any snapshots/fixtures." };
  }
  if (hay.includes("build") || hay.includes("compile") || hay.includes("tsc")) {
    return { category: "build", next: "Check the first compilation error; verify toolchain versions and missing dependencies." };
  }
  if (hay.includes("install") || hay.includes("dependency") || hay.includes("npm ci") || hay.includes("pip install")) {
    return { category: "dependencies", next: "Check dependency resolution/network errors; verify lockfiles and registry access." };
  }
  return { category: "unknown", next: "Open the failed job logs and start from the first error line." };
}

function buildComment({ run, jobs, findings }) {
  const marker = "<!-- devops-agent:sticky -->";
  const runUrl = run.html_url || "";
  const workflowName = run.name || run.workflow_name || "workflow";
  const conclusion = run.conclusion || "unknown";

  const failedJobs = jobs.filter((j) => j.conclusion === "failure");
  const cancelledJobs = jobs.filter((j) => j.conclusion === "cancelled");

  const lines = [];
  lines.push(marker);
  lines.push("## devops-agent — CI observation (read-only)");
  lines.push("");
  lines.push(`- **Workflow**: ${workflowName}`);
  if (runUrl) lines.push(`- **Run**: ${runUrl}`);
  lines.push(`- **Conclusion**: \`${conclusion}\``);
  lines.push("");

  if (failedJobs.length === 0 && cancelledJobs.length === 0) {
    lines.push("✅ No failed or cancelled jobs detected for this run.");
    return lines.join("\n");
  }

  if (failedJobs.length > 0) {
    lines.push("### Failures");
    for (const f of findings) {
      const jobLine = f.jobUrl ? `- **Job**: [${f.jobName}](${f.jobUrl})` : `- **Job**: ${f.jobName}`;
      lines.push(jobLine);
      if (f.stepName) lines.push(`  - **First failed step**: ${f.stepName}`);
      if (f.category) lines.push(`  - **Category**: \`${f.category}\``);
      if (f.next) lines.push(`  - **Next step**: ${f.next}`);
    }
    lines.push("");
  }

  if (cancelledJobs.length > 0) {
    lines.push("### Cancelled");
    for (const j of cancelledJobs) {
      lines.push(j.html_url ? `- [${j.name}](${j.html_url})` : `- ${j.name}`);
    }
    lines.push("");
  }

  lines.push("_This agent is read-only: it does not deploy, restart, scale, or store credentials._");
  return lines.join("\n");
}

async function main() {
  const repoRoot = process.env.GITHUB_WORKSPACE || process.cwd();
  const config = getConfig(repoRoot);

  if (!config.github_actions.pr_comment.enabled) {
    console.log("PR comment disabled by config.");
    return;
  }

  const eventPath = process.env.GITHUB_EVENT_PATH;
  if (!eventPath) throw new Error("Missing GITHUB_EVENT_PATH");
  const event = readJson(eventPath);

  // Works for pull_request-triggered workflows.
  const pr = event.pull_request;
  if (!pr?.number) {
    console.log("No pull_request found in event payload; skipping.");
    return;
  }

  const token = process.env.GITHUB_TOKEN;
  if (!token) throw new Error("Missing GITHUB_TOKEN");

  const [owner, repo] = (process.env.GITHUB_REPOSITORY || "").split("/");
  if (!owner || !repo) throw new Error("Missing GITHUB_REPOSITORY");

  const runId = process.env.GITHUB_RUN_ID;
  if (!runId) throw new Error("Missing GITHUB_RUN_ID");

  const api = async (method, url, body) => {
    const res = await fetch(`https://api.github.com${url}`, {
      method,
      headers: {
        Authorization: `Bearer ${token}`,
        Accept: "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "devops-agent",
        ...(body ? { "Content-Type": "application/json" } : {}),
      },
      body: body ? JSON.stringify(body) : undefined,
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`${method} ${url} failed: ${res.status} ${res.statusText}\n${text}`);
    }
    return res.json();
  };

  const run = await api("GET", `/repos/${owner}/${repo}/actions/runs/${runId}`);
  const jobsResp = await api(
    "GET",
    `/repos/${owner}/${repo}/actions/runs/${runId}/jobs?per_page=100`
  );
  const jobs = jobsResp.jobs || [];

  const failedJobs = jobs.filter((j) => j.conclusion === "failure");
  const findings = failedJobs.map((j) => {
    const steps = Array.isArray(j.steps) ? j.steps : [];
    const failedStep = steps.find((s) => s.conclusion === "failure");
    const classification = classifyFailure(failedStep?.name, j.name);
    return {
      jobName: j.name,
      jobUrl: j.html_url,
      stepName: failedStep?.name || null,
      category: classification.category,
      next: classification.next,
    };
  });

  const shouldPost =
    config.github_actions.pr_comment.post_on === "always" ||
    (config.github_actions.pr_comment.post_on === "failure" && (failedJobs.length > 0 || run.conclusion === "failure"));

  if (!shouldPost) {
    console.log("Configured to post on failure only, and no failures detected; skipping.");
    return;
  }

  const body = buildComment({ run, jobs, findings });

  // Sticky comment: find existing comment with marker, update it; otherwise create.
  const marker = "<!-- devops-agent:sticky -->";
  const comments = await api(
    "GET",
    `/repos/${owner}/${repo}/issues/${pr.number}/comments?per_page=100`
  );
  const existing = (comments || []).find((c) => typeof c.body === "string" && c.body.includes(marker));

  if (existing?.id) {
    await api("PATCH", `/repos/${owner}/${repo}/issues/comments/${existing.id}`, { body });
    console.log(`Updated sticky PR comment: ${existing.id}`);
  } else {
    await api("POST", `/repos/${owner}/${repo}/issues/${pr.number}/comments`, { body });
    console.log("Created sticky PR comment.");
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});

