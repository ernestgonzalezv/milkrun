# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned for 1.0.1

- Street distances from a routing engine, replacing the haversine detour factor
- Inter-route local search (relocate and swap) to close the saturated-fleet gap

## [1.0.0] - 2026-09-16

First public release. One API, three clients, and a vehicle routing solver written from scratch.

### Added

- **Vehicle routing solver** in pure Python with no dependencies. Clarke-Wright savings,
  consolidation, 2-opt and Or-opt local search, and cheapest insertion. Plans 400 stops across
  26 vehicles in 0.45 s.
- **Dispatcher dashboard**. React 19, TypeScript, MapLibre. Six operational metrics, route list,
  stop timeline, and a map that degrades to an offline basemap rather than going blank.
- **Driver app**. Kotlin and Compose, multi-module Clean Architecture, with an offline queue that
  syncs on reconnect and is safe to resend.
- **Public tracking**. An unauthenticated endpoint per shipment, rate limited by IP and with
  personal data trimmed.
- **Four seedable cities**. New York, Chicago, Los Angeles and Havana, with real neighbourhood
  coordinates and depots placed where freight actually stages.
- **Benchmark suite** against two manual baselines, against Google OR-Tools, and against the exact
  optimum computed by brute force for small instances.
- **Terraform for AWS**. VPC, ECS Fargate, RDS, S3 and CloudFront, SSM Parameter Store, CloudWatch.
  Validated in CI without credentials; never applied.
- 332 tests across the four surfaces, with CI on every push.

[Unreleased]: https://github.com/ernestgonzalezv/milkrun/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/ernestgonzalezv/milkrun/releases/tag/v1.0.0
