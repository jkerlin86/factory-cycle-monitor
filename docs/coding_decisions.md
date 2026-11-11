# Coding decisions

Stage A: ingestion follows the C4 project conventions (src layout,
pinned dependencies, gitignored data and .env, manifest with SHA-256
per raw file). Decisions specific to the analysis stage are recorded
here as they are made.

Stage B (analysis) decisions:

1. Divergence definition. The materials-to-finished divergence uses
   (MI - FI) / TI as the primary measure (level plus its 12-month
   change), not the difference of the 12-month changes in the
   early-stage and finished shares. Reason: the stages sum to total
   inventories exactly in the staged data, so that difference is
   identically twice the change in the early-stage share and adds no
   information. Recorded in src/factory_cycle/signals.py and
   docs/methods.md and applied consistently.
2. realtime dates stay strings. ALFRED realtime_end includes the
   sentinel 9999-12-31, which pandas Timestamps cannot hold. All
   interval logic compares ISO date strings (which order correctly)
   and never parses realtime_end as a timestamp.
3. Vintage horizon cap. ALFRED records only value-change intervals,
   so an observation month whose value stopped changing has a final
   interval that starts early and runs to the sentinel. The horizon
   lookup therefore caps target dates at the last vintage date of
   the whole series record, not at the observation month's own last
   interval start. An earlier version used the per-observation cap
   and silently emptied every horizon cell for observation months
   from 2025 onward; the fix is covered by the triangle coverage
   counts in results.json (plus 3 months: 185 of 189 rows).
4. Vintage regression sample. Genuine first releases only: the first
   vintage for both AMTMUO and AMTMVS must be strictly after the
   opening vintage of the record (2011-06-24). The first observation
   month meeting the rule is 2011-05. The sample and its definition
   are recorded in results.json and are identical across the first
   published and final runs.
5. Newey-West lag length equals the regression horizon (6 or 12),
   covering the MA(h - 1) overlap of the overlapping outcome.
6. Best cross-correlation lag means the largest absolute correlation
   in minus 12 to plus 12, with the signed correlation reported
   alongside.
7. data/processed holds pipeline outputs (signals panel, vintage
   matrices) that the figures, notebooks, and archive scripts read;
   it is gitignored on the same basis as data/raw and data/staged.
