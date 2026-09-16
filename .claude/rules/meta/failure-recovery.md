# Failure recovery (always on)

- If a fix fails the same way twice, **stop**. Re-read the relevant section end to end, find
  where the mental model was wrong, and say so out loud before trying again.
- After fixing a bug, say why it happened and whether a rule, a test or a type could stop that
  whole category. `test_architecture.py` and the Konsist tests exist because of this habit.
- Never reach for a destructive shortcut to escape confusion: no `git reset --hard`, no
  `./gradlew clean` to chase a caching ghost, no deleting files in bulk. Diagnose first.
  For a stale Gradle state try `--rerun-tasks` before `clean`; `clean` costs a full rebuild.
- `terraform apply` and `terraform destroy` are denied in `settings.json` on purpose. The AWS
  account is borrowed and the infra is not meant to run. If a task seems to need them, stop and
  ask, do not look for a way around the deny rule.

## When you are the one who was wrong

- A benchmark whose numbers do not move when you change a parameter is not a result: it is a
  parameter that never reached the code. Check that the knob is connected before believing the
  table. This happened with the OR-Tools first-solution strategy and produced four identical rows.
- When you report your own work, give both readings: what a perfectionist would object to and
  what a pragmatist would ship. Let the user pick the trade.
