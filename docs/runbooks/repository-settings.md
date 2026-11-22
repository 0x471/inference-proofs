# Repository settings

These settings live on the hosting platform rather than in tracked files. Apply them manually, and document any change in a pull request updating this file ([RFC-0013 §CI workflow structure](../../rfcs/0013-validation-and-ci.md#ci-workflow-structure)).

## Branch protection on `main`

- Require a pull request before merging.
- Requiring the jobs in `.github/workflows/ci.yml` to pass is optional.
- Block force pushes to `main` and prevent branch deletion.

## Actions

- Restrict workflow permissions to read-only access on repository contents.
- Do not expose secrets to pull requests from forks (no workflow uses a secret today).
- Pin every action to a full commit hash.

## Security

- Enable private vulnerability reporting once the repository is public ([SECURITY.md](../../SECURITY.md)).
