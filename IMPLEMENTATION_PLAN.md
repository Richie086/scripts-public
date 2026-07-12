STATUS: not-started

# Plan

Harden one tool per session until every script/web app meets `PROMPT.md`.

## Inventory (pick next unchecked item)

### Root / wrapper
- [x] `bash/ai-devbox-init.sh`
- [x] `scripts/apply-cursor-credit-savings.sh`
- [ ] `deploy-mailserver-debian.sh`

### Nested `scripts-public/` bash
- [ ] `scripts-public/bash/apache-proxy-wizard/apache-proxy-wizard.sh`
- [ ] `scripts-public/bash/apt-get-tui.sh`
- [ ] `scripts-public/bash/openssl-certtool/openssl-certtool.sh`
- [ ] `scripts-public/bash/remove_user/remove_user.sh`
- [ ] `scripts-public/bash/script-public-merge/script-public-merge.sh`
- [ ] `scripts-public/bash/setup_ssh_key.sh`
- [ ] `scripts-public/bash/user_manager/user_manager.sh`

### Nested `scripts-public/` projects
- [ ] `scripts-public/projects/deploy-mailserver-debian.sh`
- [ ] `scripts-public/projects/kvm-provisioning/provision_vms.sh`
- [ ] `scripts-public/projects/stftp/` (client/server)
- [ ] `scripts-public/projects/openssl-output-generator/` (if runnable)

### Nested `scripts-public/` python — SKIP
Do **not** run, harden, or test anything under `scripts-public/python/`. Out of scope for this loop.

### Web
- [ ] `scripts-public/web/apache-reverse-proxy/` (local/remote interactivity + docs)

## Session template (repeat)

1. Pick the next unchecked tool.
2. Audit flags/entrypoints; add `--help` if missing.
3. Add unit + flag tests (dry-run/fixtures for destructive tools).
4. Align README/help with reality.
5. Run tests + `/verify`; commit on green.
6. Check the box; update **Done / Next / Open issues** below.
7. When inventory is empty: set line 1 to `STATUS: done`.

## Done

- `bash/ai-devbox-init.sh` — fixed help script name; flag/help tests in `bash/test-ai-devbox-init-flags.sh` (14 green); README documents flags + test command.
- `scripts/apply-cursor-credit-savings.sh` — added `--help`, `--dry-run`, and `--database` options; flag and logic tests in `scripts/test-apply-cursor-credit-savings.sh` (16 green); updated documentation in `reduce-cursor-credits.md` and `blog-reduce-cursor-credits.md`.

## Next

`deploy-mailserver-debian.sh` — next hardening pass.

## Open issues

- Nested `scripts-public/` is its own git checkout; decide per session whether commits land in the outer workspace, the inner repo, or both.
- Some tools need privileged/network side effects; require dry-run or mocks before claiming done.
- `scripts-public/python/` is explicitly excluded — never pick it as Next.
- `ai-devbox-init.sh` `--dry-run` / `--run` still require interactive `gum`; full dry-run E2E not automated (flag gate covered).
