# Pilot: label-free primal and adjoint networks on a family of notched plates

Status: exploratory pilot for the FWO proposal. The plan below is fixed, and its SHA-256 recorded, before any network is trained. Deviations, if any, are listed at the end of the results file with their reasons.

## Question
On geometries the networks have not seen, does the adjoint correction J(u) + z^T (F - K u), with both networks trained on energies only (no solved examples), estimate the local notch stress much better than the plug-in value J(u), and how tight is the bound 2 sqrt(dPi dPi*)?

## Family and FE model
- Plane stress, E = 1, nu = 0.3. Plate x in [0, 1], y in [-1, 1]; bottom edge y = -1 clamped; top edge y = 1 loaded.
- U-shaped edge notch on x = 0, centred at y = y_c: depth d, root radius rho; flanks at y = y_c +/- rho from x = 0 to x = d - rho, semicircular root centred at (d - rho, y_c).
- Parameters drawn uniformly: d in [0.15, 0.35], rho in [0.03, 0.10] (with d >= rho + 0.03), y_c in [-0.3, 0.3].
- Mesh: Triangle (constrained Delaunay, minimum angle 30 degrees), element size from rho / 6 at the notch root to 0.08 at distance 0.6 and beyond; quadratic six-node triangles (P2); about 8,000 to 13,000 degrees of freedom per geometry.
- Loads on the top edge (unit cases): tension t_y = 1; in-plane bending t_y = (x - 0.5) / 0.5. A load case is a_t times tension plus a_b times bending, with a_t in [0.5, 1.5], a_b in [-0.5, 0.5].
- Quantity of interest J(u) = q^T u: mean sigma_yy over the elements whose centroids lie within 0.03 of the notch root point (d, y_c).

## Networks
- Inputs at each node location (11): x, y; d, rho, y_c (scaled to about unit range); with r the distance to the root point (d, y_c), the notch-scaled coordinates xi = (x - d) / rho and eta = (y - y_c) / rho in the bounded form xi / (1 + r / rho), eta / (1 + r / rho), and exp(-r / rho); the same three features with rho replaced by the radius of the region of interest, 0.03.
- Multilayer perceptron, tanh, 4 hidden layers of width 64.
- Primal network: outputs the responses to unit tension and unit bending (two fields); the prediction for a load case is a_t u_t + a_b u_b, linear in the load by construction.
- Adjoint network: outputs z for the quantity of interest (one field).
- Both outputs multiplied by (y + 1) / 2, so the clamped edge is satisfied exactly.
- Each predicted unit field v (u_t, u_b and z) is rescaled, per geometry, by the closed-form label-free factor c* = f^T v / (v^T K v) (f = F_t, F_b or q), which minimises the energy along v; this is used in training and in evaluation.

## Training (no solved examples)
- 24 training geometries. Primal loss: mean over instances of Pi_t(u_t) + Pi_b(u_b), with Pi(v) = 1/2 v^T K v - F^T v. Adjoint loss: mean of Pi*(z) = 1/2 z^T K z - q^T z.
- Adam, learning rate 1e-3 with cosine decay to 1e-5, 6,000 full-batch steps for each network, double precision. Three seeds (0, 1, 2), changing network initialisation only. The geometries are fixed by a separate data seed (2026).
- FE reference solutions are computed only for evaluation; the training code never reads them.

## Evaluation
- 16 held-out geometries (data seed 2027), 4 load cases each: 64 cases per seed.
- For each case: J* = q^T U*; plug-in J(u); corrected J(u) + z^T (F - K u); relative errors |J - J*| / |J*|; energy-norm relative errors of u and z; bound B = 2 sqrt(dPi dPi*), with dPi and dPi* evaluated with the reference solutions (an oracle check of the identity; computable bounds are task T1.1); effectivity B / |J* - corrected J|.
- Reported per seed: median and 90th percentile of each relative error; the median ratio of plug-in to corrected error; the share of cases with |J* - corrected J| <= B; the median effectivity.

## Reading fixed in advance
- Positive: in each of the three seeds, the median relative error of the corrected estimate is at most one fifth of the plug-in median, and the bound holds in every case.
- Negative otherwise. The result is reported either way.
- The bound holding is a property of the identity (Cauchy-Schwarz); a failure would indicate a coding error, not a scientific finding.
