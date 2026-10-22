# Evals

`evals.json` holds the three prompts used to compare Claude with and without the
skill, plus the assertions each output must satisfy. `grade.py` scores a run
directory produced by the skill-creator workflow:

```
<workspace>/iteration-N/eval-<id>-<name>/{with_skill,without_skill}/run-1/outputs/
```

```bash
python3 evals/grade.py <workspace>/iteration-N
```

Iteration 1 (2026-10-21): with skill 28/28 checks, without 21/26.

Iteration 3 (2026-10-22), with-skill only, harder cases: 25-component platform,
flowchart with diamonds/ellipses/note, layers plus a request flow: 33/33 checks.
Tokens 102k / 51k / 50k; rounds 3 / 2 / 2.
