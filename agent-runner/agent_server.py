import asyncio
import hashlib
import hmac
import logging
import os
import shutil
import subprocess
import tempfile

from fastapi import FastAPI, HTTPException, Request

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("agent-runner")

app = FastAPI()


@app.post("/webhook")
async def webhook(request: Request):
    body = await request.body()
    sig = request.headers.get("x-hub-signature-256", "")
    secret = os.environ["GITHUB_WEBHOOK_SECRET"].encode()
    expected = "sha256=" + hmac.new(secret, body, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(sig, expected):
        raise HTTPException(status_code=401, detail="Unauthorized")

    payload = await request.json()
    action = payload.get("action")
    label = payload.get("label", {}).get("name")
    issue = payload.get("issue")
    repository = payload.get("repository")

    if action != "labeled" or label != "claude":
        log.info("ignoring webhook (action=%s label=%s)", action, label)
        return {"status": "ignored"}

    log.info("accepted issue #%s in %s", issue["number"], repository["full_name"])
    asyncio.create_task(run_pipeline(issue, repository))
    return {"status": "ok"}


async def run_pipeline(issue, repository):
    issue_number = issue["number"]
    issue_title = issue["title"]
    issue_body = issue.get("body") or ""
    branch = f"claude/issue-{issue_number}"
    default_branch = repository["default_branch"]
    full_name = repository["full_name"]
    token = os.environ["GITHUB_TOKEN"]
    repo_url = f"https://x-access-token:{token}@github.com/{full_name}.git"

    work_dir = tempfile.mkdtemp(prefix=f"claude-{issue_number}-")
    log.info("issue #%s: cloning %s into %s", issue_number, full_name, work_dir)

    try:
        run(f"git clone {repo_url} {work_dir}")
        run(f"git checkout -b {branch}", cwd=work_dir)
        run('git config user.email "claude-runner@railway.app"', cwd=work_dir)
        run('git config user.name "Claude"', cwd=work_dir)

        prompt_file = os.path.join(work_dir, ".claude-prompt.txt")
        with open(prompt_file, "w") as f:
            f.write(build_prompt(issue_number, issue_title, issue_body))

        log.info("issue #%s: running claude", issue_number)
        run(
            'claude --print --dangerously-skip-permissions '
            '--allowedTools "Bash,Read,Edit,Write" '
            '-p "$(cat .claude-prompt.txt)"',
            cwd=work_dir,
        )

        log.info("issue #%s: pushing branch %s", issue_number, branch)
        run("git add -A", cwd=work_dir)
        run(f'git commit -m "feat: implement issue #{issue_number}"', cwd=work_dir)
        run(f"git push origin {branch}", cwd=work_dir)

        pr_url = run(
            f'gh pr create '
            f'--title "feat: {issue_title} (closes #{issue_number})" '
            f'--body "Closes #{issue_number}" '
            f'--base {default_branch} '
            f'--head {branch} '
            f'--repo {full_name}',
            cwd=work_dir,
            capture=True,
        ).strip()
        log.info("issue #%s: opened PR %s", issue_number, pr_url)

        run(
            f'gh issue comment {issue_number} '
            f'--body "I\'ve opened a PR for this: {pr_url}" '
            f'--repo {full_name}',
            cwd=work_dir,
        )
        log.info("issue #%s: done", issue_number)

    except Exception:
        log.exception("issue #%s: pipeline failed", issue_number)
        raise
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


def build_prompt(issue_number, issue_title, issue_body):
    return f"""
You are working on GitHub issue #{issue_number}: "{issue_title}"

Issue description:
{issue_body}

Instructions:
- Implement what the issue describes
- Follow all conventions in CLAUDE.md
- Do not commit or push — that will be handled separately
- You are operating autonomously. There is no human available to answer questions.
- Make a decision for every ambiguity you encounter. Never leave a task partially complete.
- Record all assumptions in CLAUDE_NOTES.md and move on.
""".strip()


def run(cmd, cwd=None, capture=False):
    result = subprocess.run(
        cmd,
        shell=True,
        cwd=cwd,
        env={**os.environ, "GH_TOKEN": os.environ["GITHUB_TOKEN"]},
        capture_output=capture,
        text=True,
        check=True,
    )
    return result.stdout if capture else None
