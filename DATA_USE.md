# Data use and privacy

## Public package

This repository does not distribute the original challenge workbook. The included files under `data/processed/` are aggregate outputs intended to make the analytical claims reviewable without exposing identifiers.

Excluded fields include:

- customer and account identifiers;
- NBA IDs and entry-event IDs;
- transaction and product identifiers;
- exact transaction and entry timestamps;
- distance-to-venue values;
- app-creation timestamps; and
- row-level product purchase histories.

## Source workbook

No data license or redistribution permission accompanied the supplied XLSX. Possession of the workbook was not be interpreted as permission to publish it. Anyone rebuilding the aggregates is responsible for confirming their authorization, storage controls, retention policy, and disclosure obligations.

The `.gitignore` file excludes `data/raw/*` by default.

## Analytical privacy boundary

The build script writes only aggregate CSVs. Tests check that direct identifier columns and representative identifier values are absent from public outputs. Aggregate data may still be commercially sensitive.

