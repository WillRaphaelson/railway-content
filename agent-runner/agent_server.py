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
    if payload.get("action") != "opened":
        log.info("ignoring webhook (action=%s)", payload.get("action"))
        return {"status": "ignored"}

    issue_number = payload["issue"]["number"]
    full_name = payload["repository"]["full_name"]
    log.info("accepted issue #%s in %s", issue_number, full_name)
    asyncio.create_task(run_pipeline(issue_number, full_name))
    return {"status": "ok"}


async def run_pipeline(issue_number, full_name):
    work_dir = tempfile.mkdtemp(prefix=f"claude-{issue_number}-")
    try:
        prompt_file = os.path.join(work_dir, ".claude-prompt.txt")
        with open(prompt_file, "w") as f:
            f.write(build_prompt(issue_number, full_name))

        log.info("issue #%s: handing off to claude in %s", issue_number, work_dir)
        subprocess.run(
            'claude --print --dangerously-skip-permissions '
            '--allowedTools "Bash,Read,Edit,Write" '
            '-p "$(cat .claude-prompt.txt)"',
            shell=True,
            cwd=work_dir,
            env={**os.environ, "GH_TOKEN": os.environ["GITHUB_TOKEN"]},
            check=True,
        )
        log.info("issue #%s: claude run complete", issue_number)
    except Exception:
        log.exception("issue #%s: pipeline failed", issue_number)
        raise
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


def build_prompt(issue_number, full_name):
    return f"""
You are handling GitHub issue #{issue_number} in {full_name}.

You are running in an empty working directory. The `gh` CLI is authenticated via $GH_TOKEN.

Do the following, end to end:
1. Run `gh auth setup-git` so git can authenticate via gh.
2. Run `gh issue view {issue_number} --repo {full_name}` to read the issue.
3. Clone the repo: `gh repo clone {full_name} repo`, then work inside `repo/`.
4. Configure git inside the repo:
   `git config user.email "claude-runner@railway.app"`
   `git config user.name "Claude"`
5. Create and check out a branch named `claude/issue-{issue_number}`.
6. Implement what the issue describes. Follow CLAUDE.md conventions if present.
7. Commit with a clear conventional commit message derived from the actual diff.
8. Push the branch: `git push origin claude/issue-{issue_number}`.
9. Open a PR with `gh pr create` against the repo's default branch — write a real title and body that summarize the change. Include `Closes #{issue_number}` in the body.
10. Comment on the issue: `gh issue comment {issue_number} --repo {full_name} --body "I've opened a PR for this: <pr-url>"`.

Notes:
- You are operating autonomously. There is no human available to answer questions.
- Make a decision for every ambiguity. Never leave a task partially complete.
- Record assumptions in CLAUDE_NOTES.md inside the repo and move on.
- Do not stop until the PR is open and the issue has been commented on.
""".strip()
