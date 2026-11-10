"""Numerical check of the identities and bounds used in the FWO proposal (27 and 28 October 2026).

(2) Adjoint correction for a linear quantity of interest J(u) = q^T u:
    J(U*) - [J(u) + z^T (F - K u)] = (Z* - z)^T K (U* - u),   K Z* = q, K U* = F,
    and |.| <= ||Z* - z||_K ||U* - u||_K = 2 sqrt(dPi(u) dPi*(z)),
    where dPi(u) = Pi(u) - Pi(U*) = 1/2 ||u - U*||_K^2 and likewise for the adjoint energy.
(3) Rayleigh quotient of the linear buckling problem (K + lambda K_G) phi = 0, phi^T K phi = 1:
    mu1 - phi^T (-K_G) phi = (phi - phi1)^T (mu1 K + K_G) (phi - phi1),  mu1 = max mu,
    with mu1 K + K_G positive semidefinite.
(4) Bound relative to the FE model from an equilibrated split of the residual (28 October 2026):
    K = sum_e K_e with each K_e positive semidefinite; r = F - K u = sum_e r_e with r_e in range(K_e). Then
    ||u - U*||_K^2 = r^T K^{-1} r <= sum_e r_e^T K_e^+ r_e, with equality for r_e = K_e K^{-1} r.
(5) Inertia check for the critical load factor (28 October 2026): for lam > 0,
    K + lam K_G is positive definite  <=>  lam < lambda_1 = 1 / mu1  (mu1 > 0).
"""
import numpy as np
from scipy.linalg import eigh

rng = np.random.default_rng(20261027)
n_trials, worst_adj, worst_ray, viol_bound, viol_psd = 200, 0.0, 0.0, 0, 0
for t in range(n_trials):
    n = int(rng.integers(5, 60))
    A = rng.standard_normal((n, n)); K = A @ A.T + n * np.eye(n)          # SPD stiffness
    F = rng.standard_normal(n); q = rng.standard_normal(n)
    U = np.linalg.solve(K, F); Z = np.linalg.solve(K, q)
    u = U + rng.standard_normal(n) * rng.uniform(0.01, 1.0)              # prediction
    z = Z + rng.standard_normal(n) * rng.uniform(0.01, 1.0)              # adjoint prediction
    Pi = lambda v: 0.5 * v @ K @ v - F @ v
    Pis = lambda v: 0.5 * v @ K @ v - q @ v
    lhs = q @ U - (q @ u + z @ (F - K @ u))
    rhs = (Z - z) @ K @ (U - u)
    worst_adj = max(worst_adj, abs(lhs - rhs) / max(abs(rhs), 1e-300))
    dPi, dPis = Pi(u) - Pi(U), Pis(z) - Pis(Z)
    bound = 2.0 * np.sqrt(dPi * dPis)
    if abs(lhs) > bound * (1 + 1e-12):
        viol_bound += 1
    B = rng.standard_normal((n, n)); KG = -(B @ B.T) + 0.3 * (B + B.T)   # symmetric geometric stiffness
    mu, V = eigh(-KG, K)                                                  # -K_G phi = mu K phi, V^T K V = I
    mu1, phi1 = mu[-1], V[:, -1]
    phi = phi1 + 0.3 * rng.standard_normal(n); phi = phi / np.sqrt(phi @ K @ phi)
    if phi @ K @ phi1 < 0:
        phi1 = -phi1
    lhs2 = mu1 - phi @ (-KG) @ phi
    rhs2 = (phi - phi1) @ (mu1 * K + KG) @ (phi - phi1)
    worst_ray = max(worst_ray, abs(lhs2 - rhs2) / max(abs(rhs2), 1e-300))
    if np.linalg.eigvalsh(mu1 * K + KG).min() < -1e-8 * abs(mu1) * np.linalg.norm(K, 2):
        viol_psd += 1
print(f"trials {n_trials}; adjoint identity max relative deviation {worst_adj:.1e}; "
      f"bound violations {viol_bound}; Rayleigh identity max relative deviation {worst_ray:.1e}; "
      f"PSD violations {viol_psd}")


# (4) equilibrated split bound
worst_id4, viol4, worst_eq4 = 0.0, 0, 0.0
for t in range(n_trials):
    n = int(rng.integers(8, 50))
    parts = []
    for e in range(int(rng.integers(3, 12))):                              # "elements" on random DOF subsets
        m = int(rng.integers(3, min(n, 12) + 1))
        idx = rng.choice(n, size=m, replace=False)
        C = rng.standard_normal((int(rng.integers(1, m)), m))              # rank < m: element has a null space
        Ke = np.zeros((n, n)); Ke[np.ix_(idx, idx)] = C.T @ C
        parts.append(Ke)
    S = np.diag(rng.uniform(0.5, 2.0, n))                                  # supports, keeps K positive definite
    parts.append(S)
    K = sum(parts)
    F = rng.standard_normal(n); U = np.linalg.solve(K, F)
    u = U + rng.standard_normal(n) * rng.uniform(0.01, 1.0)
    r = F - K @ u
    err2 = (u - U) @ K @ (u - U)
    worst_id4 = max(worst_id4, abs(err2 - r @ np.linalg.solve(K, r)) / err2)
    ws = [rng.standard_normal(n) for _ in parts]                           # arbitrary equilibrated split
    rs = [Ke @ w for Ke, w in zip(parts, ws)]
    rs[-1] = rs[-1] + (r - sum(rs))                                        # close the split through the supports
    assert np.allclose(sum(rs), r)
    bound = sum(re @ np.linalg.pinv(Ke) @ re for Ke, re in zip(parts, rs))
    if err2 > bound * (1 + 1e-10):
        viol4 += 1
    x = np.linalg.solve(K, r)                                              # optimal split
    best = sum((Ke @ x) @ np.linalg.pinv(Ke) @ (Ke @ x) for Ke in parts)
    worst_eq4 = max(worst_eq4, abs(best - err2) / err2)
print(f"(4) residual identity max relative deviation {worst_id4:.1e}; split-bound violations {viol4}; "
      f"optimal split max relative deviation from equality {worst_eq4:.1e}")

# (5) inertia check
mismatch5, tested5 = 0, 0
for t in range(n_trials):
    n = int(rng.integers(5, 60))
    A = rng.standard_normal((n, n)); K = A @ A.T + n * np.eye(n)
    B = rng.standard_normal((n, n)); KG = -(B @ B.T) + 0.3 * (B + B.T)
    mu1 = eigh(-KG, K, eigvals_only=True)[-1]
    if mu1 <= 0:
        continue
    lam1 = 1.0 / mu1
    for lam in rng.uniform(0.02, 2.0, 20) * lam1:
        if abs(lam / lam1 - 1.0) < 1e-6:
            continue
        try:
            np.linalg.cholesky(K + lam * KG); pd = True
        except np.linalg.LinAlgError:
            pd = False
        tested5 += 1
        if pd != (lam < lam1):
            mismatch5 += 1
print(f"(5) inertia check: {tested5} load factors tested, mismatches {mismatch5}")
