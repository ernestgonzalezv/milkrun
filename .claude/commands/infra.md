---
description: Validate the Terraform under infra/ without touching AWS
---

Validate `infra/` end to end. This never needs credentials and never costs money.

```bash
cd infra
terraform fmt -check -recursive -diff
terraform init -backend=false -input=false
terraform validate
tflint --init && tflint --format compact
checkov -d . --framework terraform --quiet
```

If a tool is missing, say so and skip that stage — do not silently pass. `brew install terraform
tflint` and `pip install checkov`.

**`terraform apply` and `terraform destroy` are denied in `settings.json`.** The stack is written
to be read, not run. If a task appears to need a real plan, stop and ask.

## When a check fires

- A `checkov` finding gets fixed or **justified in `infra/README.md`**. Adding it to `skip_check`
  in the CI workflow without a written reason is not allowed.
- A `tflint` finding about an instance type or an attribute is almost always a real error:
  `validate` does not know the AWS catalogue, `tflint` does.
- After any change, check the two decision tables in `infra/README.md` still tell the truth:
  *Decisiones* and *Qué NO se usó, y por qué*.
