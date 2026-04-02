# Deployment

## Pre-deployment checklist

Complete every item before deploying to any environment:

- [ ] All tests pass on the target branch (`uv run pytest`)
- [ ] Linting passes with no errors (`uv run ruff check`)
- [ ] Documentation builds without warnings
- [ ] Version number bumped in `pyproject.toml` (follow [Semantic Versioning](https://semver.org/))
- [ ] [Changelog](./changelog.md) updated with release notes
- [ ] Dependency lock file is up to date (`uv lock`)

## Environments

| Environment | Purpose | URL | Branch | Approval required |
| ----------- | ------- | --- | ------ | ----------------- |
| Development | Integration testing | `<!-- TODO: set dev URL -->` | `develop` | No |
| Staging | Pre-production validation | `<!-- TODO: set staging URL -->` | `release/*` | Team lead |
| Production | Live environment | `<!-- TODO: set production URL -->` | `main` | 2 maintainers |

### Environment-specific configuration

- Use environment variables (never hard-coded secrets) for all credentials.
- Configuration differences between environments should be documented in a `.env.example` file.
- Feature flags control progressive rollout of new functionality.

## CI/CD pipeline

The deployment pipeline runs automatically on push to protected branches.

### Pipeline stages

1. **Lint** — Static analysis with `ruff` and type checking.
2. **Test** — Full test suite with coverage reporting.
3. **Build** — Package the application and build documentation.
4. **Deploy** — Push to the target environment (see [Environments](#environments)).
5. **Verify** — Post-deployment smoke tests and health checks.

### Triggers

- Push to `develop` → deploy to Development.
- Push to `release/*` → deploy to Staging (requires approval).
- Push to `main` → deploy to Production (requires 2 approvals).

## Rollback procedures

### When to rollback

- Health check failures after deployment.
- Error rate exceeds the defined threshold (e.g., >1% 5xx responses).
- Critical functionality is broken as reported by smoke tests.

### Rollback steps

1. Revert the merge commit on the target branch: `git revert <merge-sha>`.
2. Push the revert to trigger the CI/CD pipeline.
3. Verify the rollback deployment via health checks and smoke tests.
4. Open a post-incident issue documenting the failure and root cause.

### Verification

- Confirm the previous stable version is serving traffic.
- Check application logs for error resolution.
- Notify the team in the appropriate communication channel.
