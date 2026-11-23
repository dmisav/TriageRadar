# Onboard a new team

1. Copy [examples/minimal.yaml](../examples/minimal.yaml) to a team-owned
   configuration file.
2. Set a stable `team_id` and increment `config_revision` for meaningful
   configuration changes.
3. Add source definitions and sections. Keep provider URLs, queries, and
   ownership rules in `settings`, never in Python code.
4. Use `$(ENV_NAME)` for environment-provided values. Missing variables fail
   validation rather than silently becoming empty strings. `${ENV_NAME:-value}`
   supplies a non-secret default.
5. Validate locally:

   ```bash
   uv run triageradar validate path/to/team.yaml
   ```

6. Copy [.env.example](../.env.example) to `.env` for local-only values and
   update the placeholders. `.env` is ignored by Git. Production must inject
   values through the runtime environment or secret references; never put the
   file in the container image.

Validation lists missing variable names without printing values. Prefer
`DefaultAzureCredential` and workload identity for Azure services; use token
or connection-string variables only as explicit fallbacks.
