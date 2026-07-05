"""ストアのロード健全性テスト。"""

from __future__ import annotations

from app.store import Store


def test_load_counts() -> None:
    store = Store.load()
    assert len(store.words) == 315
    assert len(store.idioms) == 65


def test_entry_no_sequence_no_gaps() -> None:
    store = Store.load()
    nums = sorted(int(no) for no in store.words)
    assert nums[0] == 1
    assert nums[-1] == 315
    assert nums == list(range(1, 316))  # 欠番・重複なし


def test_section_assignment() -> None:
    store = Store.load()
    assert store.get_word("001").section == "part1"
    assert store.get_word("164").section == "part2"
    assert store.get_word("290").section == "keigo"


def test_image_url_built() -> None:
    store = Store.load()
    assert store.get_word("001").image_url == "/assets/manga/part1/001.png"


def test_keigo_has_honorific() -> None:
    store = Store.load()
    hon = store.get_word("290").honorific
    assert hon is not None
    assert hon.type == "尊敬"
