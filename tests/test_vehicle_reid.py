"""Vehicle appearance matching: a strict bar and multi-view galleries.

The failure this guards against is the expensive one — two DIFFERENT cars, in
different places, collapsing into a single "My Toyota" that the owner cannot
untangle. Splitting one car across clusters is recoverable (name them the same);
merging two cars is not.
"""

import numpy as np

from alibi.cameras.cross_camera import (CrossCameraTracker, MATCH_THRESHOLDS,
                                        DEFAULT_MATCH_THRESHOLD,
                                        MAX_GALLERY_VIEWS, _as_views)


def _tracker(tmp_path):
    return CrossCameraTracker(storage_path=str(tmp_path / "sightings.jsonl"),
                              gallery_path=str(tmp_path / "galleries.jsonl"))


def _vec(seed, dim=64):
    rng = np.random.default_rng(seed)
    v = rng.normal(size=dim).astype(np.float32)
    return v / np.linalg.norm(v)


def _at_cosine(a, cos, seed):
    """A unit vector whose cosine to `a` is exactly `cos`.

    Mixing two random vectors does NOT give the cosine you asked for — in 64
    dimensions they are already near-orthogonal, so the blend stays glued to
    `a`. Project the noise off `a` first, then rotate by the angle we want.
    """
    n = _vec(seed)
    orth = n - np.dot(n, a) * a
    orth = orth / np.linalg.norm(orth)
    v = cos * a + np.sqrt(1.0 - cos ** 2) * orth
    return (v / np.linalg.norm(v)).astype(np.float32)


def test_vehicles_use_a_stricter_bar_than_the_default():
    """0.6 let different vehicle clusters (measured 0.74-0.81 apart) merge."""
    assert MATCH_THRESHOLDS["vehicle"] > DEFAULT_MATCH_THRESHOLD
    assert MATCH_THRESHOLDS["vehicle"] >= 0.82


def test_two_similar_but_different_cars_do_not_merge(tmp_path):
    t = _tracker(tmp_path)
    a = _vec(1)
    # A different car that still looks fairly similar — the 0.74-0.81 band that
    # used to be merged by the old 0.6 threshold.
    b = _at_cosine(a, 0.78, seed=2)
    assert 0.6 < float(np.dot(a, b)) < MATCH_THRESHOLDS["vehicle"]

    id_a, _ = t.record_appearance_sighting("cam1", "vehicle", a, "2026-07-25T10:00:00")
    id_b, _ = t.record_appearance_sighting("cam1", "vehicle", b, "2026-07-25T10:05:00")
    assert id_a != id_b, "two different cars must not become one entity"


def test_the_same_car_still_matches_itself(tmp_path):
    t = _tracker(tmp_path)
    a = _vec(3)
    nearly = _at_cosine(a, 0.93, seed=4)      # same car, slightly different look
    id1, _ = t.record_appearance_sighting("cam1", "vehicle", a, "2026-07-25T10:00:00")
    id2, _ = t.record_appearance_sighting("cam2", "vehicle", nearly, "2026-07-25T10:01:00")
    assert id1 == id2


def test_gallery_keeps_several_views_not_one_average(tmp_path):
    """A running mean drifts toward whatever it absorbs; separate views can't."""
    t = _tracker(tmp_path)
    base = _vec(5)
    eid, _ = t.record_appearance_sighting("cam1", "vehicle", base, "2026-07-25T10:00:00")
    for i in range(4):
        view = _at_cosine(base, 0.90, seed=100 + i)   # same car, new angle
        t.record_appearance_sighting("cam1", "vehicle", view, f"2026-07-25T10:0{i+1}:00")
    views = _as_views(t._galleries["vehicle"][eid])
    assert views.ndim == 2 and views.shape[0] > 1, "should hold multiple views"
    # The first view is preserved exactly — not averaged away.
    assert np.max(views @ base) > 0.99


def test_views_are_capped(tmp_path):
    t = _tracker(tmp_path)
    base = _vec(6)
    eid, _ = t.record_appearance_sighting("cam1", "vehicle", base, "2026-07-25T10:00:00")
    for i in range(MAX_GALLERY_VIEWS * 3):
        v = _at_cosine(base, 0.90, seed=500 + i)
        t.record_appearance_sighting("cam1", "vehicle", v, f"2026-07-25T11:{i:02d}:00")
    assert _as_views(t._galleries["vehicle"][eid]).shape[0] <= MAX_GALLERY_VIEWS


def test_old_single_vector_galleries_still_load():
    """An install written before multi-view must keep working."""
    flat = [0.1, 0.2, 0.3, 0.4]
    views = _as_views(flat)
    assert views.shape == (1, 4)


def test_faces_keep_the_original_threshold(tmp_path):
    """Only vehicles get the stricter bar — faces separate well already."""
    t = _tracker(tmp_path)
    a = _vec(7)
    b = _at_cosine(a, 0.70, seed=8)
    id1, _ = t.record_appearance_sighting("cam1", "unknown_face", a, "2026-07-25T10:00:00")
    id2, _ = t.record_appearance_sighting("cam1", "unknown_face", b, "2026-07-25T10:01:00")
    # At ~0.7 similarity a face is still the same person under the 0.6 default.
    assert id1 == id2
