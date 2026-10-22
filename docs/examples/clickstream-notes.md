# Replicating `source-clickstream.png`

Worked example for `references/reading-a-diagram.md`. Source: a vendor-style
"Clickstream Analytics Pipeline" picture (dark theme, gradient boxes, drop shadows,
curved arrows, subtitles squeezed into labels). Rebuild: `assets/examples/clickstream.*`.

## Extraction

1. **Title / purpose.** Clickstream analytics pipeline: events from apps into an AWS
   ingest path, then a serving side for queries, dashboards and alerts.
2. **Containers.** `INGEST (AWS us-east-1)` and `SERVING`, side by side, dashed
   borders. Apps sit outside both.
3. **Components (label → subtitle).** Web & Mobile Apps → JS SDK · iOS · Android;
   API Gateway → REST, 50k rps; Kinesis Data Streams → 24h retention; Lambda Enricher
   → geo-ip, device parse; S3 Data Lake → parquet, hourly partitions; Glue Catalog →
   schemas; Redshift → warehouse; QuickSight → dashboards; Athena → ad-hoc SQL;
   Analysts → notebooks; PagerDuty → alerts on lag.
4. **Connections.** apps → gateway `events`; gateway → kinesis; kinesis → s3
   `stream`; s3 → lambda `read raw`; lambda → glue; s3 → glue; s3 → redshift `COPY`
   (curved); s3 → athena `load`; redshift → quicksight; athena → analysts; kinesis →
   pagerduty `lag alarm` (dashed, curved).
5. **Colour key.** None drawn. Colours look decorative (one gradient per box), not
   semantic: blue for both API Gateway and Lambda, pink for Redshift and Athena, but
   nothing consistent beyond that. Treated as no key.
6. **Reading direction.** Left → right; the data lake is central.
7. **Implied, not drawn.** Where does the Lambda enricher write its output? Nothing
   leaves it except the Glue arrow. Why does Kinesis alert PagerDuty directly? Likely
   a CloudWatch alarm on iterator age, abbreviated.

## Mapping decisions

- Zones → tinted regions: ingest (blue tint, subtitle `aws us-east-1`), serving (teal).
- Roles: apps grey; API Gateway green (gateway); Lambda and Athena blue (compute);
  Kinesis, S3, Glue, Redshift red (stores and streams); QuickSight cyan (interface);
  Analysts grey (users); PagerDuty purple (alerting).
- Logos fetched with `icons.py` for API Gateway, Lambda, S3, Redshift, PagerDuty.
  Kinesis, Glue, Athena and QuickSight have no Simple Icons entry, so no icon rather
  than a wrong one.
- Curved arrows → elbowed; `COPY` and `lag alarm` keep their labels; the alarm stays
  dashed and is red because it is an alerting path.
- Subtitles → bracketed second lines, lowercased.

## Changes from the original

- Unlabelled arrows `lambda → glue` and `s3 → glue` were given labels
  (`registers schema`, `partitions`) from the subtitle `schemas`; confirm.
- The source's colours were replaced by role colours (see key under the diagram).
- Nothing was dropped or merged. Two open questions are listed under "implied".
