---
applyTo: "**"
---

# General Commit Instructions

## Conventional Commits

- Use [Conventional Commits](https://www.conventionalcommits.org/) for all commit messages.
- Use the [VSCode Conventional Commits](https://github.com/vivaxy/vscode-conventional-commits) emoji, respectively, gitmoji type style for commit messages:

| Type     |            Emoji             | Description                         |
| -------- | :--------------------------: | ----------------------------------- |
| feat     |      `:sparkles:` (✨)       | A new feature                       |
| fix      |         `:bug:` (🐛)         | A bug fix                           |
| docs     |        `:memo:` (📝)         | Documentation only changes          |
| style    |      `:lipstick:` (💄)       | Changes that do not affect meaning  |
| refactor |       `:recycle:` (♻️)       | Code change that is not a fix/feat  |
| perf     |         `:zap:` (⚡)         | Performance improvement             |
| test     |  `:white_check_mark:` (✅)   | Adding or correcting tests          |
| build    | `:construction_worker:` (👷) | Build system or dependencies        |
| ci       |       `:wrench:` (🔧)        | CI/CD configuration                 |
| chore    |       `:hammer:` (🔨)        | Other changes that don't modify src |
| revert   |       `:rewind:` (⏪)        | Reverts a previous commit           |

**Example commit messages:**

```text
feat: ✨ add new peak fitting method
fix: 🐛 handle NaN values in solver
docs: 📝 update usage documentation
test: ✅ add regression test for optimizer
refactor: ♻️ merge dictionary assignments in report generation
chore: 🔨 update dependencies
```

## Branching Rules (Trunk-Based Development)

- All changes should branch from `main`.
- Use short-lived feature branches named with the pattern:
  `type/short-description`
  Examples:
  - `feat/peak-fitting`
  - `fix/nan-handling`
  - `docs/usage-update`
- Merge to `main` via pull request after review and passing CI.
- Rebase frequently to keep branches up to date with `main`.
- Delete feature branches after merge.
