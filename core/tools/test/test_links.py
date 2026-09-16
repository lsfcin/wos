# T1 links: a short name stays sayable, a private thing never gets one, and a live link never moves.
import pytest

import links_core


@pytest.fixture
def mapfile(tmp_path):
    """A map of its own, so a test never writes the real one."""
    return tmp_path / 'links.txt'


def test_a_short_name_is_a_name_a_room_can_be_told(mapfile):
    for good in ('ai4good', 'ai4good/setup', 'ai4good/aula3', 'rva-chico', 'ppc2026'):
        links_core.validate_short_name(good)


def test_a_short_name_stops_at_one_level_because_nobody_recites_a_tree():
    """The one level is for a course. A second is a directory, and a directory is not sayable."""
    with pytest.raises(links_core.Refused):
        links_core.validate_short_name('academy/teaching/ai4good')


@pytest.mark.parametrize('bad', ['AI4Good', 'ai4 good', 'ai4_good', '-ai4good', 'ai4good/', 'olá'])
def test_a_short_name_that_cannot_be_typed_from_memory_is_refused(bad):
    with pytest.raises(links_core.Refused):
        links_core.validate_short_name(bad)


@pytest.mark.parametrize('short_name', ['casinhas', 'casinhas-planta', 'saude-exames',
                                  'financas-irpf', 'branches/casinhas'])
def test_a_private_subtree_never_gets_a_public_short_name(short_name):
    """A redirect is public: a guessable short name turns 'anyone with the link' into discoverable.

    `casinhas-planta` is the case that matters and the one this check first let through — a flat
    hyphenated short name is exactly how a one-off is named, so the hyphen is a word boundary here.
    """
    with pytest.raises(links_core.Refused):
        links_core.check_private(short_name)


def test_the_file_recording_the_link_can_refuse_it_too():
    """The URL cannot say whether a document is private; where it is being written down can."""
    with pytest.raises(links_core.Refused):
        links_core.check_private('planta', home='branches/casinhas/projeto.md')
    links_core.check_private('setup', home='academy/teaching/ai4good/CONTEXT.md')


def test_a_taken_short_name_is_refused_rather_than_moved(mapfile):
    """A short name already said out loud to a room must not start pointing somewhere else."""
    links_core.add('ai4good', 'https://example.com/a', path=mapfile)
    with pytest.raises(links_core.Refused) as e:
        links_core.add('ai4good', 'https://example.com/b', path=mapfile)
    assert 'https://example.com/a' in str(e.value), "the refusal must name the current target"


def test_a_target_that_is_not_a_url_never_reaches_the_site(mapfile):
    with pytest.raises(links_core.Refused):
        links_core.add('ai4good', 'docs.google.com/forms/d/abc', path=mapfile)


def test_the_map_round_trips_through_the_file(mapfile):
    links_core.add('ai4good/setup', 'https://example.com/f', owner='ai4good', path=mapfile)
    links_core.add('rva-chico', 'https://example.com/t', path=mapfile)
    rows = links_core.load(mapfile)
    assert [r['short_name'] for r in rows] == ['ai4good/setup', 'rva-chico'], "sorted by short_name"
    assert links_core.load(mapfile)[1]['owner'] == 'rva-chico', "owner defaults to the first segment"


def test_find_is_how_a_growing_map_stays_cheap(mapfile):
    links_core.add('ai4good', 'https://example.com/a', path=mapfile)
    links_core.add('rva-chico', 'https://example.com/t', path=mapfile)
    assert [r['short_name'] for r in links_core.find('ai4', mapfile)] == ['ai4good']
    assert [r['short_name'] for r in links_core.find('example.com/t', mapfile)] == ['rva-chico']


def test_the_redirect_file_is_what_cloudflare_reads(mapfile):
    links_core.add('ai4good/setup', 'https://example.com/f', path=mapfile)
    out = links_core.redirects(links_core.load(mapfile))
    assert out == '/ai4good/setup https://example.com/f 302\n'


def test_the_redirect_is_302_because_a_301_outlives_the_fix(mapfile):
    """A 301 is cached by the browser forever, so a wrong target survives correcting the map."""
    links_core.add('ai4good', 'https://example.com/a', path=mapfile)
    assert ' 301' not in links_core.redirects(links_core.load(mapfile))


def test_check_reads_the_file_rather_than_trusting_the_writer(mapfile):
    """Rows can arrive by hand-edit, which is the only path `add`'s refusals do not cover."""
    mapfile.write_text('short_name\turl\towner\tadded\n'
                       'Casinhas\tnot-a-url\tx\t2026-09-06\n'
                       'ai4good\thttps://example.com/a\tai4good\t2026-09-06\n'
                       'ai4good\thttps://example.com/b\tai4good\t2026-09-06\n',
                       encoding='utf-8', newline='\n')
    findings = links_core.check(links_core.load(mapfile))
    assert len(findings) == 3, findings
    assert any('listed twice' in f for f in findings)


def test_the_real_map_is_clean():
    """The one this workspace ships. A finding here is a link handed to a room."""
    assert links_core.check(links_core.load()) == []
