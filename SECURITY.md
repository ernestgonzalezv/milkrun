# Security policy

## Reporting a vulnerability

Please **do not open a public issue**. Use GitHub's
[private vulnerability reporting](https://github.com/ernestgonzalezv/milkrun/security/advisories/new),
or email the address on [@ernestgonzalezv](https://github.com/ernestgonzalezv).

Expect a first reply within 72 hours.

## Scope

This is a portfolio project and is **not deployed anywhere**. There is no production instance, no
user data, and the Terraform under `infra/` has never been applied to a real AWS account. A report
here is about the code, not about a live system.

## Known and accepted weaknesses

These are documented in the README rather than fixed, because the trade is deliberate. Reporting
them is not necessary:

- The dashboard stores its JWT in `localStorage`, so an XSS would steal it. An `httpOnly` cookie is
  the right answer for a browser-only client; this backend also serves a mobile app, where cookies
  do not apply.
- The Android app stores tokens in DataStore without encryption. Production would use the Keystore.
- `seed_demo` creates users with a well-known password. It is a development command and refuses
  nothing — never run it against a real database.

## Out of scope

Anything requiring physical access, social engineering, or a self-inflicted configuration
(for example running with `DJANGO_DEBUG=1` on a public host, which `settings.py` already refuses to
do without an explicit `DJANGO_SECRET_KEY`).
