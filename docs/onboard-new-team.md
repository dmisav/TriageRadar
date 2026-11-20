# Onboard a new team

1. Copy [examples/minimal.yaml](../examples/minimal.yaml) to a team-owned
   configuration file.
2. Set a stable `team_id` and increment `config_revision` for meaningful
   configuration changes.
3. Add source definitions and sections. Keep provider URLs, queries, and
   ownership rules in `settings`, never in Python code.
4. Use `$(ENV_NAME)` for environment-provided values. Missing variables fail
   validation rather than silently becoming empty strings.
5. Validate locally:

   ```bash
   uv run oncalldigest validate path/to/team.yaml
   ```

Secrets must be supplied by the deployment identity or secret store. Do not
commit tokens or credentials to YAML.
