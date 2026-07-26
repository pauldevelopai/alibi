"""Learning that a pot plant is not a person — and, more importantly, NOT
learning to ignore the doorway it stands in."""

from alibi.learning.detections import DetectionRejections


def _store(tmp_path):
    return DetectionRejections(path=tmp_path / "rej.jsonl")


PLANT = [100, 200, 60, 90]          # the offending pot plant at the front gate


def test_same_object_is_suppressed(tmp_path):
    s = _store(tmp_path)
    assert not s.is_rejected("front-gate", PLANT)
    s.record("front-gate", PLANT, score=0.4, by="admin")
    assert s.is_rejected("front-gate", PLANT)
    # A near-identical box on a later frame is the same plant.
    assert s.is_rejected("front-gate", [103, 202, 58, 92])


def test_only_the_camera_it_was_learned_on(tmp_path):
    s = _store(tmp_path)
    s.record("front-gate", PLANT, by="admin")
    assert not s.is_rejected("driveway", PLANT)


def test_a_person_standing_there_still_gets_through(tmp_path):
    """The whole risk of this feature. A person in front of the plant is a
    taller, differently-proportioned box — they must NOT be suppressed."""
    s = _store(tmp_path)
    s.record("front-gate", PLANT, by="admin")
    person = [100, 120, 60, 220]        # same spot, much taller
    assert not s.is_rejected("front-gate", person)


def test_elsewhere_in_frame_is_untouched(tmp_path):
    s = _store(tmp_path)
    s.record("front-gate", PLANT, by="admin")
    assert not s.is_rejected("front-gate", [500, 200, 60, 90])


def test_restore_undoes_it(tmp_path):
    s = _store(tmp_path)
    s.record("front-gate", PLANT, by="admin")
    assert s.is_rejected("front-gate", PLANT)
    s.restore("front-gate", PLANT)
    assert not s.is_rejected("front-gate", PLANT)
    assert s.summary() == []


def test_filter_drops_only_the_rejected_person_box(tmp_path):
    s = _store(tmp_path)
    s.record("front-gate", PLANT, by="admin")
    dets = [
        {"class": "person", "bbox": PLANT},
        {"class": "person", "bbox": [500, 200, 60, 90]},
        {"class": "car", "bbox": PLANT},          # a different class is untouched
    ]
    kept = s.filter_detections("front-gate", dets)
    assert len(kept) == 2
    assert {tuple(k["bbox"]) for k in kept} == {(500, 200, 60, 90), tuple(PLANT)}


def test_summary_is_visible_and_reversible(tmp_path):
    s = _store(tmp_path)
    s.record("front-gate", PLANT, score=0.42, by="admin", note="pot plant")
    rows = s.summary()
    assert len(rows) == 1
    assert rows[0]["camera_id"] == "front-gate"
    assert rows[0]["note"] == "pot plant"
