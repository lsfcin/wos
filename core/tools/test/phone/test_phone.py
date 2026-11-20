# T1 phone/adb: a prefs edit changes only the named values, scrolling ends when the page stops, and a sheet holds every shot. No phone, no adb.
import importlib.machinery
import importlib.util
import pathlib

import pytest

_ADB = pathlib.Path(__file__).resolve().parents[2] / 'phone' / 'adb'

PREFS = """<?xml version='1.0' encoding='utf-8' standalone='yes' ?>
<map>
    <string name="flutter.overlay_style">pill</string>
    <long name="flutter.overlay_size" value="2" />
    <boolean name="flutter.thermometer_on" value="true" />
</map>"""


def _tool():
    loader = importlib.machinery.SourceFileLoader('phone_adb', str(_ADB))
    module = importlib.util.module_from_spec(importlib.util.spec_from_loader('phone_adb', loader))
    loader.exec_module(module)
    return module


def _raw(width: int, height: int, top: int, body: int, overlay: int = 0) -> bytes:
    """A raw screencap: 16-byte header, the status bar rows filled with `top`, the rest with `body`,
    and the first row under the bar filled with `overlay` — a Bloco's number ticking there."""
    header = width.to_bytes(4, 'little') + height.to_bytes(4, 'little') + bytes(8)
    bar = bytes([top]) * (150 * width * 4)
    under = bytes([overlay]) * (width * 4)
    return header + bar + under + bytes([body]) * ((height - 151) * width * 4)


def test_a_prefs_edit_changes_the_named_values_and_keeps_the_rest():
    phone = _tool()
    out = phone.set_prefs(PREFS, {'flutter.overlay_style': 'block', 'flutter.overlay_size': '3'})
    assert '<string name="flutter.overlay_style">block</string>' in out
    assert 'name="flutter.overlay_size" value="3"' in out
    assert 'name="flutter.thermometer_on" value="true"' in out


def test_a_key_the_file_does_not_hold_is_refused_rather_than_added():
    phone = _tool()
    with pytest.raises(SystemExit, match='overlay_styel'):
        phone.set_prefs(PREFS, {'flutter.overlay_styel': 'block'})


def test_a_ticking_clock_or_overlay_is_not_a_scroll_but_a_repaint_is():
    phone = _tool()
    assert not phone.moved(_raw(64, 400, 1, 9, overlay=1), _raw(64, 400, 2, 9, overlay=2))
    assert phone.moved(_raw(64, 400, 1, 9), _raw(64, 400, 1, 8))


def test_scrolling_stops_at_the_first_frame_that_did_not_move(tmp_path, monkeypatch):
    phone = _tool()
    frames = iter([_raw(64, 400, 0, 1), _raw(64, 400, 5, 2, overlay=3), _raw(64, 400, 7, 2, overlay=4)])
    swipes = []

    def fake(*args, data=None):
        if args == ('exec-out', 'screencap'):
            return next(frames)
        if args[:3] == ('shell', 'input', 'swipe'):
            swipes.append(args)
        return b'png'

    monkeypatch.setattr(phone, 'adb', fake)
    monkeypatch.setattr(phone.time, 'sleep', lambda s: None)
    kept = phone.shoot(tmp_path, 'hoje', None)
    assert [p.name for p in kept] == ['hoje-01.png', 'hoje-02.png']
    assert len(swipes) == 2


def test_an_intent_action_and_an_app_are_told_apart():
    phone = _tool()
    assert phone.is_action('android.settings.SETTINGS')
    assert not phone.is_action('com.android.chrome')


def test_a_sheet_holds_every_shot_at_a_third_of_its_size(tmp_path):
    from PIL import Image
    phone = _tool()
    shots = []
    for i in range(4):
        path = tmp_path / f"s{i}.png"
        Image.new('RGB', (30, 60), (i * 60, 0, 0)).save(path)
        shots.append(path)
    board = Image.open(phone.sheet(shots, tmp_path / 'sheet.png'))
    assert board.size == (30, 40)
