# G-F1: numbers

**Verdict: FAIL**

| Criterion | Specimen | Test | Tolerance | Frictionless | No-slip | Holds |
|---|---|---|---|---|---|---|
| C1 | B-13 | 74.996 | 4.814 | 41.681 (ok) | 82.474 (ok) | True |
| C2 | T-13 | 0.934 | 0.051 | 2.074 (ok) | 0.811 (ok) | True |
| C3 | B-13 | 55.572 | 3.478 | 49.590 (ok) | 34.786 (ok) | False |

## Reported, not part of the verdict

| Item | Specimen | Test | Tolerance | Frictionless | No-slip | Within |
|---|---|---|---|---|---|---|
| C1 elastic | B-13 | 74.996 | 4.814 | 41.702 | 82.494 | True |
| C1 measured preload | B-13 | 74.996 | 4.814 | 41.013 | 80.897 | True |
| C3 elastic | B-13 | 55.572 | 3.478 | 59.787 | 35.241 | True |
| C3 measured preload | B-13 | 55.572 | 3.478 | 57.605 | 40.683 | True |
| C1 at Theta_D = 0.0005 | B-13 | 59.499 | 7.358 | 22.554 | 45.306 | False |
| C1 at Theta_D = 0.0005 elastic | B-13 | 59.499 | 7.358 | 22.554 | 45.306 | False |
| C2 elastic | T-13 | 0.934 | 0.051 | 1.784 | 0.807 | True |

| Mesh flag | Coarse | Medium | Ratio | Flagged |
|---|---|---|---|---|
| B-13 frictionless C1 | 41.702 | 41.614 | 0.9979 | False |
| B-13 frictionless C3 | 59.787 | 60.845 | 1.0177 | False |
| B-13 no-slip C1 | 82.494 | 82.765 | 1.0033 | False |
| B-13 no-slip C3 | 35.241 | 36.398 | 1.0328 | True |
| T-13 frictionless C2 | 1.784 | 1.797 | 1.0073 | False |
| T-13 no-slip C2 | 0.807 | 0.806 | 0.9990 | False |
