# Workspace: infra

Terraform for AWS: VPC with public and private subnets, ECS Fargate behind an ALB, RDS Postgres,
S3 + CloudFront for the dashboard, SSM Parameter Store for secrets, CloudWatch and a budget alarm.

**This is never applied.** `terraform apply` and `terraform destroy` are denied in
`.claude/settings.json`. It is validated with no credentials, `fmt`, `validate`, `tflint`,
`checkov`, and CI runs all four on every push. Read the banner at the top of `README.md` before
writing anything that assumes a live stack.

The two tables in `README.md` are part of the artifact: *Decisiones* and *Qué NO se usó, y por
qué*. A change that makes either false is a defect, not a doc chore.

Rules: `.claude/rules/terraform/`. Validate with `/infra`.
