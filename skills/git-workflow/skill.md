# Skill: Git Workflow — Official Best Practices
# Source: git-scm.com/book/en/v2, github.com/git/git

## Branch Strategy
- `main` — always deployable. No direct pushes.
- `dev` — integration branch. Merge to main via PR + review.
- Feature branches: `feat/short-desc`, Fixes: `fix/issue-desc`, Hotfixes: `hotfix/desc`.
- Delete branches after merge. Keep branch list clean.

## Commit Discipline
```
<type>(<scope>): <summary under 72 chars>

<body — optional, explain WHY not what>

<footer: Co-Authored-By, Fixes #123>
```
Types: `feat fix refactor perf docs test chore ci`

- Atomic commits — one logical change per commit.
- Present tense, imperative: "add feature" not "added feature".
- Reference issues: `Fixes #123`, `Relates-to #456`.

## Essential Commands
```bash
git log --oneline --graph --all          # visual branch history
git rebase -i HEAD~N                     # squash/reword N commits (local only)
git stash push -m "wip: feature X"       # save work in progress
git bisect start; git bisect bad; git bisect good <sha>   # binary search for regression
git cherry-pick <sha>                    # apply single commit to current branch
git reflog                               # recover "lost" commits
```

## PR / Code Review Rules
- PR title ≤ 70 chars. Body explains WHY, not WHAT.
- One logical change per PR. Large PRs → stale reviews → bugs.
- Squash merge for features (clean main history). Merge commit for release branches.
- Never force-push to `main` or `dev`. Rebase feature branches only.

## .gitignore Essentials
```
__pycache__/  *.pyc  .env  .env.*
*.log  workspace/  .DS_Store  node_modules/
dist/  build/  *.egg-info/
```
