# Contributing / working conventions

## Branching

Trunk-based, short-lived branches — no `develop`/`release` branches.

- `main` is always deployable and protected (the `gitleaks` check must pass before merge; force-push and delete are blocked).
- Branch off `main` using one of:
  - `feat/<slug>` — new functionality
  - `fix/<slug>` — bug fix
  - `chore/<slug>` — tooling, deps, non-functional cleanup
- Open a PR back into `main`, merge, then delete the branch.
- Tag releases directly on `main` (`vX.Y.Z`) instead of maintaining a release branch.
