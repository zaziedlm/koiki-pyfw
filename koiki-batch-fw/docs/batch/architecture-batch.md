# Batch Architecture

## Module Topology

- `components/libkoiki-batch`: reusable framework layer
- `components/koiki_ref_batch_app`: reference implementation using the framework
- `apps/*`: customer-specific batch applications

## Processing Topology

Each job should be implemented with explicit Spring Batch responsibilities:

- Job configuration (flow, transitions, restart policy)
- Step configuration (chunk/tasklet, commit interval, transaction boundary)
- Reader / Processor / Writer composition
- Domain service for business rules
- Infrastructure adapters (DB, file, external API)

## Operations

- Scheduler integration: JP1 via `ops/jp1/scripts/run-job.sh`
- Exit code convention: 0 / 10 / 20 / 30
- Rerun and recovery: `ops/jp1/runbook/rerun-procedure.md`
