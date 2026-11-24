# Offline evaluation

| Strategy | Mean NDCG@10 | 95% interval | Users |
|---|---:|---:|---:|
| chronological | 0.693426 | [0.693426, 0.693426] | 1 |
| popularity | 0.580279 | [0.580279, 0.580279] | 1 |
| for_you | 0.543771 | [0.543771, 0.543771] | 1 |
| learned | 0.817530 | [0.817530, 0.817530] | 1 |

## Learned minus best baseline

| Slice | Difference | 95% interval | Verdict |
|---|---:|---:|---|
| all (chronological) | 0.124103 | [0.124103, 0.124103] | wins |
| new (chronological) | 0.124103 | [0.124103, 0.124103] | wins |

## Run metadata

- Cut-off: `2026-09-24T04:48:00Z`
- Seed: `42`
- Users: `1`
- Database fingerprint: `dfb75ff01d63a2f979da7ec4bfa24b3b4da3f0357c622111675203245befe0d9`
- Git commit: `065e3b4967fd80601a71532dd0c9ddc14e41ad74`
