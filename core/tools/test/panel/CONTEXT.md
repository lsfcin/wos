# panel
> T1 unit tests for the panel tool. Every model is faked: no network, no quota.

<!-- routing:start -->
## Routing

| File | Interface | Description |
|------|-----------|-------------|
| [`test_panel.py`](test_panel.py) | [`test_panel.pyi`](test_panel.pyi) | T1 panel/ask: a spent quota or a broken call falls to the next model, the first verdict wins, and none at all stops with every reason. Models faked. |
<!-- routing:end -->
