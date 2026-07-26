"""
Learning that something is NOT a person.

The detector reads a pot plant, a bin, a patch of shadow at the front gate as a
person — over and over, because the thing never moves. Every one of those was
shown to the operator as "Person · no face captured", and telling the system it
was wrong changed nothing, so it kept happening.

This is where that correction lives. The key fact about a false positive on
scenery is that it is STATIC: the same object, on the same camera, in almost
exactly the same box, every time. So a rejection is recorded as a REGION on a
camera, and a later detection that lands in that same region is suppressed.

Deliberate limits, because suppressing a real person is far worse than showing a
pot plant:

  * matched by IoU at a high bar (0.6) AND similar box shape, so a person
    standing in front of the plant — a taller, differently-proportioned box —
    still gets through;
  * only ever applied to the camera it was learned on;
  * append-only and fully reversible, and the API can list what is being
    suppressed, so this never becomes an invisible blind spot.

The recorded confidence is kept too: it is the raw material for a per-camera
confidence floor later, the same way face_feedback learns a face threshold.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from alibi.encryption import get_encrypted_writer

STORE = Path("alibi/data/detection_rejections.jsonl")

# A box has to overlap a rejected region this much to be treated as the same
# thing. High on purpose — see the module note.
IOU_BAR = 0.6
# ...and be roughly the same shape. A person in front of the plant is taller.
SHAPE_TOLERANCE = 0.45


def _iou(a: Sequence[float], b: Sequence[float]) -> float:
    """Intersection-over-union for [x, y, w, h] boxes."""
    try:
        ax, ay, aw, ah = [float(v) for v in a]
        bx, by, bw, bh = [float(v) for v in b]
    except (TypeError, ValueError):
        return 0.0
    if aw <= 0 or ah <= 0 or bw <= 0 or bh <= 0:
        return 0.0
    x1, y1 = max(ax, bx), max(ay, by)
    x2, y2 = min(ax + aw, bx + bw), min(ay + ah, by + bh)
    if x2 <= x1 or y2 <= y1:
        return 0.0
    inter = (x2 - x1) * (y2 - y1)
    union = aw * ah + bw * bh - inter
    return inter / union if union > 0 else 0.0


def _similar_shape(a: Sequence[float], b: Sequence[float]) -> bool:
    """Roughly the same proportions — guards against suppressing a person who
    happens to stand where the scenery is."""
    try:
        _, _, aw, ah = [float(v) for v in a]
        _, _, bw, bh = [float(v) for v in b]
    except (TypeError, ValueError):
        return False
    if min(aw, ah, bw, bh) <= 0:
        return False
    ar, br = aw / ah, bw / bh
    hi, lo = max(ar, br), min(ar, br)
    return (hi - lo) / hi <= SHAPE_TOLERANCE


class DetectionRejections:
    def __init__(self, path: Path = STORE):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._crypto = get_encrypted_writer()
        self._cache: Optional[List[dict]] = None
        self._sig: Optional[tuple] = None

    # ── writing ──────────────────────────────────────────────────────────
    def record(self, camera_id: str, bbox: Sequence[float], *,
               kind: str = "person", score: Optional[float] = None,
               frame_url: Optional[str] = None, by: str = "system",
               note: Optional[str] = None, active: bool = True) -> None:
        """"That isn't a person." Kept against the camera and the box."""
        if not camera_id or len(list(bbox or [])) != 4:
            return
        self._crypto.write_line(self.path, {
            "camera_id": str(camera_id), "bbox": [float(v) for v in bbox],
            "kind": kind, "score": score, "frame_url": frame_url,
            "by": by, "note": (note or "")[:300], "active": bool(active),
            "ts": datetime.utcnow().isoformat(),
        })
        self._cache = None

    def restore(self, camera_id: str, bbox: Sequence[float]) -> None:
        """Undo — stop suppressing this region (append-only, last wins)."""
        self.record(camera_id, bbox, by="restore", active=False,
                    note="restored by operator")

    # ── reading ──────────────────────────────────────────────────────────
    def _rows(self) -> List[dict]:
        try:
            st = self.path.stat()
            sig = (st.st_mtime_ns, st.st_size)
        except OSError:
            sig = (0, 0)
        if self._cache is not None and self._sig == sig:
            return self._cache
        rows: List[dict] = []
        try:
            for r in self._crypto.read_lines(self.path):
                if r.get("camera_id") and len(r.get("bbox") or []) == 4:
                    rows.append(r)
        except Exception as e:
            print(f"[detections] could not read rejections: {e}", flush=True)
        self._cache, self._sig = rows, sig
        return rows

    def regions(self, camera_id: Optional[str] = None) -> List[dict]:
        """The regions currently suppressed. Later rows win, so a restore
        cancels an earlier rejection of the same spot."""
        state: List[dict] = []
        for r in self._rows():
            if camera_id and r["camera_id"] != camera_id:
                continue
            hit = next((s for s in state
                        if s["camera_id"] == r["camera_id"]
                        and _iou(s["bbox"], r["bbox"]) >= IOU_BAR), None)
            if hit is None:
                state.append(dict(r))
            else:
                hit.update(r)                     # last word on this region
        return [s for s in state if s.get("active", True)]

    def is_rejected(self, camera_id: str, bbox: Sequence[float]) -> bool:
        """Has the operator told us this camera's box is not a person?"""
        if not camera_id or len(list(bbox or [])) != 4:
            return False
        for r in self.regions(camera_id):
            if _iou(r["bbox"], bbox) >= IOU_BAR and _similar_shape(r["bbox"], bbox):
                return True
        return False

    def filter_detections(self, camera_id: str, detections: List[dict]) -> List[dict]:
        """Drop detections that land on something already ruled out."""
        if not detections:
            return detections
        keep = []
        for d in detections:
            box = d.get("bbox") or []
            if d.get("class") == "person" and self.is_rejected(camera_id, box):
                continue
            keep.append(d)
        return keep

    def summary(self) -> List[Dict[str, Any]]:
        """What is being suppressed, for an honest, reversible surface."""
        out = []
        for r in self.regions():
            out.append({"camera_id": r["camera_id"], "bbox": r["bbox"],
                        "score": r.get("score"), "frame_url": r.get("frame_url"),
                        "by": r.get("by"), "note": r.get("note"),
                        "ts": r.get("ts")})
        out.sort(key=lambda r: str(r.get("ts") or ""), reverse=True)
        return out


_STORE: Optional[DetectionRejections] = None


def get_detection_rejections() -> DetectionRejections:
    global _STORE
    if _STORE is None:
        _STORE = DetectionRejections()
    return _STORE
