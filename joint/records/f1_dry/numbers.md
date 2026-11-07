# G-F1-dry: numbers

**Verdict: PASS**

| Criterion | Specimen | Test | Tolerance | Frictionless | No-slip | Holds |
|---|---|---|---|---|---|---|
| C1 | B-19 | 137.719 | 6.963 | 78.624 (ok) | 146.960 (ok) | True |
| C2 | T-19 | 1.143 | 0.053 | 1.818 (ok) | 0.745 (ok) | True |
| C3 | B-19 | 19.527 | 1.526 | 34.357 (ok) | 17.649 (ok) | True |

## Reported, not part of the verdict

| Item | Specimen | Test | Tolerance | Frictionless | No-slip | Within |
|---|---|---|---|---|---|---|
| C1 elastic | B-19 | 137.719 | 6.963 | 78.628 | 146.963 | True |
| C1 measured preload | B-19 | 137.719 | 6.963 | 78.089 | 145.992 | True |
| C3 elastic | B-19 | 19.527 | 1.526 | 34.592 | 17.649 | True |
| C3 measured preload | B-19 | 19.527 | 1.526 | 35.912 | 18.726 | True |
| C1 at Theta_D = 0.0005 | B-19 | 111.106 | 16.145 | 44.197 | 83.261 | False |
| C1 at Theta_D = 0.0005 elastic | B-19 | 111.106 | 16.145 | 44.197 | 83.261 | False |
| C2 elastic | T-19 | 1.143 | 0.053 | 1.631 | 0.745 | True |

| Mesh flag | Coarse | Medium | Ratio | Flagged |
|---|---|---|---|---|
| B-19 frictionless C1 | 78.628 | 78.496 | 0.9983 | False |
| B-19 frictionless C3 | 34.592 | 35.812 | 1.0353 | True |
| B-19 no-slip C1 | 146.963 | 146.322 | 0.9956 | False |
| B-19 no-slip C3 | 17.649 | 18.283 | 1.0359 | True |
| T-19 frictionless C2 | 1.631 | 1.637 | 1.0040 | False |
| T-19 no-slip C2 | 0.745 | 0.749 | 1.0060 | False |
