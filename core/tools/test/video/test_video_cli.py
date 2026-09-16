# test_video_cli.py — T1 unit tests for the video CLI's batch path (no network, injected runners)
#
# The batch path exists because a step that costs N decisions is the step that gets skipped:
# an INBOX drain with eight links used to be eight invocations. What is asserted here is that
# one call covers all of them and that no single bad link can end the run.
import importlib.util
from importlib.machinery import SourceFileLoader

from conftest import WORKSPACE_ROOT  # the depth lives in one file, not nine

_PATH = WORKSPACE_ROOT / 'core/tools/video/video'
# The tool is extensionless by convention (core/tools/SPECS.md § Adding a tool), so the
# loader has to be named explicitly — import by path cannot infer it from the suffix.
_spec = importlib.util.spec_from_file_location('video_cli', _PATH,
                                               loader=SourceFileLoader('video_cli', str(_PATH)))
video_cli = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(video_cli)


def bundle(url, text='body', ok=True, method='captions'):
    return {'url': url, 'source': 'yt', 'ok': ok, 'title': 't',
            'uploader': None, 'text': text, 'method': method}


def test_urls_from_text_reads_bare_markdown_and_parenthesised_links():
    text = ('bare https://a.com/1 here\n'
            '[a reel](https://b.com/2) and (https://c.com/3)\n'
            'end of sentence https://d.com/4.\n')
    assert video_cli.urls_from_text(text) == [
        'https://a.com/1', 'https://b.com/2', 'https://c.com/3', 'https://d.com/4']


def test_urls_from_text_dedups_in_order():
    text = 'https://a.com/1 https://b.com/2 https://a.com/1'
    assert video_cli.urls_from_text(text) == ['https://a.com/1', 'https://b.com/2']


def test_a_raising_extractor_does_not_abort_the_batch():
    def explode(url, level='auto', save=False):
        if url == 'https://b.com':
            raise RuntimeError('login required')
        return bundle(url)

    out = video_cli.run_batch(['https://a.com', 'https://b.com', 'https://c.com'],
                              _assemble=explode, _fetch=lambda u: '')
    assert [b['url'] for b in out] == ['https://a.com', 'https://b.com', 'https://c.com']
    assert [b['ok'] for b in out] == [True, False, True]
    assert 'login required' in out[1]['error']


def test_a_link_with_no_media_falls_back_to_web_fetch():
    calls = []

    def fetch(url):
        calls.append(url)
        return 'page text'

    out = video_cli.run_batch(['https://page.com'],
                              _assemble=lambda u, **k: bundle(u, text='', ok=False,
                                                              method='none'),
                              _fetch=fetch)
    assert calls == ['https://page.com']
    assert out[0]['method'] == 'web/fetch'
    assert out[0]['text'] == 'page text'
    assert out[0]['ok'] is True


def test_a_link_with_media_never_reaches_web_fetch():
    def fetch(url):
        raise AssertionError('the ladder already answered')

    out = video_cli.run_batch(['https://v.com'], _assemble=lambda u, **k: bundle(u),
                              _fetch=fetch)
    assert out[0]['method'] == 'captions'


def test_from_file_reads_every_link_in_one_call(tmp_path):
    f = tmp_path / 'INBOX.md'
    f.write_text('- https://a.com/1 útil pro isoroll\n- [x](https://b.com/2)\n', encoding='utf-8', newline='\n')
    urls, level, save, as_json = video_cli.parse_args(['--from', str(f)])
    assert urls == ['https://a.com/1', 'https://b.com/2']
    assert (level, save, as_json) == ('auto', False, False)


def test_parse_args_keeps_the_single_url_form_and_its_flags():
    urls, level, save, as_json = video_cli.parse_args(['https://a.com', '--level', 'meta',
                                                       '--save', '--json'])
    assert urls == ['https://a.com']
    assert (level, save, as_json) == ('metadata', True, True)


def test_a_mixed_batch_prints_one_block_per_link_and_a_summary(capsys, monkeypatch):
    def half(url, level='auto', save=False):
        return bundle(url, text='' if url.endswith('2') else 'body',
                      ok=not url.endswith('2'), method='none')

    monkeypatch.setattr(video_cli, 'assemble', half)
    monkeypatch.setattr(video_cli, 'web_fetch', lambda u: '')
    code = video_cli.main(['https://a.com/1', 'https://b.com/2'])
    out = capsys.readouterr().out
    assert code == 0, 'a partial failure must not stop the drain'
    assert '[1/2] https://a.com/1' in out
    assert '[2/2] https://b.com/2' in out
    assert '2 links · 1 ok · 1 failed' in out


def test_no_links_is_not_an_error(tmp_path, capsys):
    f = tmp_path / 'INBOX.md'
    f.write_text('nothing captured yet\n', encoding='utf-8', newline='\n')
    assert video_cli.main(['--from', str(f)]) == 0
    assert 'no links found' in capsys.readouterr().err
