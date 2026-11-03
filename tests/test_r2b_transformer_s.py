"""R2b (PREREG_R2B Sec. 2 and 8): wp9's S on the three-dimensional FE-JEPA
transformer. Off (the baseline) the transformer's pack -- features and decode
scale -- is the Phase-2b transformer's bit for bit; on, both halves of S reach
the model, the decoded field carries the scale once, the prediction scales
with the loads, the AR loss scores exactly the inference field, a unit trains
to a state of the default's keys and shapes, and the two arms build the same
network from a seed (the configurations' own model blocks, at full size)."""

import json
from copy import deepcopy
from pathlib import Path

import numpy as np
import pytest

from fejepa.models.features import (FeatureSpec, battery_fscale, battery_l1,
                                    build_features_battery, decode_scale_value)

ROOT = Path(__file__).resolve().parents[1]
TRANSFORMER = {"dim": 16, "depth": 1, "heads": 2, "mask_frac": 0.2, "scale_decode": True,
               "features": {"load_summary": True, "geometry": True, "spatial_dim": 3}}
S = {"decode_scale": "l1", "decode_scale_factor": 2.0 ** -10}


def _s_cfg():
    return dict(TRANSFORMER, **S, features=dict(TRANSFORMER["features"], load_density=True))


def _cfg(name):
    return json.loads((ROOT / "configs" / f"{name}.json").read_text())


def _gmsh3d(g=0, lc=0.30):
    """A small instance of the 3D training family's geometry (box, cavities)."""
    pytest.importorskip("gmsh")
    from fejepa.fe.gmsh3d import gmsh3d_instance

    return gmsh3d_instance(np.random.default_rng(98000 + g), lc=lc, labelled=False)


def _model(cfg, seed=0):
    pytest.importorskip("torch")
    from fejepa.experiments.parallel import _build_model

    return _build_model({"kind": "fejepa", "model": cfg, "seed": seed})


def test_the_configurations_model_blocks_are_the_transformer_with_and_without_s():
    from fejepa.models.fejepa import FEJEPAConfig

    b = FEJEPAConfig.from_dict(_cfg("r2b_b")["model"])
    s = FEJEPAConfig.from_dict(_cfg("r2b_s")["model"])
    p2b = FEJEPAConfig.from_dict(_cfg("phase2b_v1")["model"])
    assert b.to_dict() == p2b.to_dict()
    assert (b.decode_scale, b.decode_scale_factor, b.features.load_density) == ("max", 1.0, False)
    assert (s.decode_scale, s.decode_scale_factor, s.features.load_density) == \
        ("l1", 2.0 ** -10, True)
    assert s.features.dim == b.features.dim and s.features.spatial_dim == 3
    assert {k: v for k, v in s.to_dict().items() if k not in ("decode_scale",
                                                              "decode_scale_factor", "features")} \
        == {k: v for k, v in b.to_dict().items() if k not in ("decode_scale",
                                                              "decode_scale_factor", "features")}


def test_both_arms_build_the_same_network_from_a_seed():
    """S changes the values of the input features, not their number: from the
    same seed the two arms' networks start from the same weights (the
    configurations' own model blocks, at full size)."""
    torch = pytest.importorskip("torch")
    for seed in (3, 5):
        a = _model(_cfg("r2b_b")["model"], seed).state_dict()
        b = _model(_cfg("r2b_s")["model"], seed).state_dict()
        assert list(a) == list(b)
        assert all(torch.equal(a[k], b[k]) for k in a)
    c = _model(_cfg("r2b_b")["model"], 4).state_dict()
    assert not all(torch.equal(a[k], c[k]) for k in a)           # the seed does matter


def test_default_pack_is_the_phase2b_transformers():
    torch = pytest.importorskip("torch")
    a = _gmsh3d(1)
    pack = _model(TRANSFORMER).prepare_instance(a, "cpu")
    assert float(pack["fscale"]) == float(np.float32(battery_fscale(a.F)))
    ref = build_features_battery(a, FeatureSpec(spatial_dim=3))
    assert torch.equal(pack["feats"], torch.as_tensor(ref))


def test_s_pack_carries_both_halves_of_s():
    torch = pytest.importorskip("torch")
    a = _gmsh3d(2)
    pack = _model(_s_cfg()).prepare_instance(a, "cpu")
    assert float(pack["fscale"]) == float(np.float32(2.0 ** -10 * battery_l1(a.F)))
    assert float(pack["fscale"]) == float(np.float32(decode_scale_value(a.F, "l1", 2.0 ** -10)))
    assert float(pack["fscale"]) != float(np.float32(battery_fscale(a.F)))
    want = build_features_battery(a, FeatureSpec(spatial_dim=3, load_density=True))
    assert torch.equal(pack["feats"], torch.as_tensor(want))
    assert not torch.equal(pack["feats"],
                           torch.as_tensor(build_features_battery(a, FeatureSpec(spatial_dim=3))))


def test_s_decode_applies_the_scale_once():
    """The decoded field is the field decoder's raw output, masked, times the
    pack's scale (2^-10 x sum|F|) once (hooked at the decoder)."""
    torch = pytest.importorskip("torch")
    a = _gmsh3d(6)
    m = _model(_s_cfg()).eval()
    pack = m.prepare_instance(a, "cpu")
    raw = {}
    hook = m.decoder.register_forward_hook(lambda mod, inp, out: raw.__setitem__("u", out.detach()))
    with torch.no_grad():
        u = m.forward_instance(pack)
    hook.remove()
    assert torch.equal(u, raw["u"].reshape(raw["u"].shape[0], -1) * pack["free"] * pack["fscale"])


def test_s_prediction_scales_with_the_loads():
    torch = pytest.importorskip("torch")
    m = _model(_s_cfg()).eval()
    a = _gmsh3d(4)
    outs = []
    for s in (1.0, 3.7, 0.01):
        b = deepcopy(a)
        b.F = a.F * s
        pack = m.prepare_instance(b, "cpu")
        if s == 1.0:
            base_feats, base_scale = pack["feats"], float(pack["fscale"])
        else:
            assert torch.allclose(pack["feats"], base_feats, atol=1e-6)
            assert np.isclose(float(pack["fscale"]), s * base_scale, rtol=1e-6)
        with torch.no_grad():
            outs.append((s, m.forward_instance(pack).numpy().astype(np.float64)))
    u1 = outs[0][1]
    for s, u in outs[1:]:
        assert np.allclose(u, s * u1, rtol=1e-4, atol=1e-7 * s * np.abs(u1).max())


def test_s_inputs_do_not_change_with_the_mesh():
    """One geometry and its loads meshed at two sizes: S's decode scale agrees
    (to the gravity load's discretisation of the cavities) and the default's
    shrinks with the element size, as on the bottleneck (fine3d)."""
    archs = [_gmsh3d(3, lc) for lc in (0.30, 0.16)]
    assert archs[1].n_nodes > 2 * archs[0].n_nodes
    s = [decode_scale_value(a.F, "l1", 2.0 ** -10) for a in archs]
    assert abs(s[1] / s[0] - 1) < 0.02
    assert battery_fscale(archs[1].F) / battery_fscale(archs[0].F) < 0.6


def test_s_ar_loss_scores_exactly_the_inference_field():
    torch = pytest.importorskip("torch")
    from fejepa.anchor.energy import AnchorCache
    from fejepa.train.losses import AR_CONFIG, compute_loss

    a = _gmsh3d(5)
    m = _model(_s_cfg())
    m.train()
    pack = m.prepare_instance(a, "cpu")
    anchor = AnchorCache(device="cpu").get(a)
    seen, real = {}, anchor.energies

    def spy(u):
        seen["u"] = u.detach().clone()
        return real(u)
    anchor.energies = spy
    compute_loss(m, pack, anchor, None, None, np.random.default_rng(0), AR_CONFIG)
    assert torch.equal(seen["u"], m.forward_instance(pack).detach())


def test_s_transformer_trains_through_the_unit_path(tmp_path):
    torch = pytest.importorskip("torch")
    from fejepa.data.archive import save_instance
    from fejepa.experiments.parallel import pretrain_unit

    files = []
    for g in range(3):
        f = tmp_path / f"i{g}.npz"
        save_instance(_gmsh3d(10 + g), f)
        files.append(str(f))
    out = pretrain_unit({"kind": "fejepa", "model": _s_cfg(), "seed": 3, "tf32": False,
                         "files": files, "loss": "ar",
                         "pre": {"epochs": 2, "lr": 1e-3, "device": "cpu", "log_every": -1},
                         "state_path": str(tmp_path / "s.pt"), "quiet": True})
    sd = torch.load(out["state_path"], map_location="cpu", weights_only=True)
    ref = _model(TRANSFORMER).state_dict()
    assert list(sd) == list(ref) and all(sd[k].shape == ref[k].shape for k in sd)
    assert all(torch.isfinite(v).all() for v in sd.values())
    assert not all(torch.equal(sd[k], _model(_s_cfg(), 3).state_dict()[k]) for k in sd)   # trained


def test_both_arms_visit_the_instances_in_the_same_order(tmp_path, monkeypatch):
    """The AR loss draws nothing from the seed's generator, so each epoch's
    order is the seed's alone: the two arms of a seed visit the instances in
    the same order (the unit path, two epochs, three instances)."""
    pytest.importorskip("torch")
    from fejepa.data.archive import save_instance
    from fejepa.experiments.parallel import pretrain_unit
    import fejepa.train.pretrain as P

    files = []
    for g in range(3):
        f = tmp_path / f"i{g}.npz"
        save_instance(_gmsh3d(20 + g), f)
        files.append(str(f))
    real, seen = P.compute_loss, []

    def spy(model, pack, *a, **k):
        seen.append(int(pack["arch"].n_nodes))
        return real(model, pack, *a, **k)
    monkeypatch.setattr(P, "compute_loss", spy)
    orders = {}
    for name, cfg in (("b", TRANSFORMER), ("s", _s_cfg())):
        seen.clear()
        pretrain_unit({"kind": "fejepa", "model": cfg, "seed": 4, "tf32": False, "files": files,
                       "loss": "ar", "pre": {"epochs": 2, "lr": 1e-3, "device": "cpu",
                                             "log_every": -1},
                       "state_path": str(tmp_path / f"{name}.pt"), "quiet": True})
        orders[name] = list(seen)
    assert len(orders["b"]) == 6 and orders["b"] == orders["s"]
    assert len(set(orders["b"])) == 3
