from __future__ import annotations

import json

from signalroom.adapters.statsbomb import SOURCE_REVISION, StatsBombOpenDataAdapter


class _Response:
    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, bool]:
        return {"fresh": True}


class _Session:
    def __init__(self) -> None:
        self.calls = 0

    def get(self, url: str, timeout: int) -> _Response:
        self.calls += 1
        return _Response()


def test_corrupt_cache_entry_is_reacquired_atomically(tmp_path):
    adapter = StatsBombOpenDataAdapter(cache_dir=tmp_path)
    adapter.session = _Session()
    target = tmp_path / SOURCE_REVISION[:12] / "broken.json"
    target.parent.mkdir(parents=True)
    target.write_text("not-json", encoding="utf-8")

    assert adapter._get_json("broken.json") == {"fresh": True}
    assert adapter.session.calls == 1
    assert json.loads(target.read_text(encoding="utf-8")) == {"fresh": True}
    assert not list(target.parent.glob("*.tmp"))
