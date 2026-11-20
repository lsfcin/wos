# T1 links: a short name stays sayable, a private thing never gets one, and a live link never moves.
import pathlib
import pytest
from conftest import needs
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
    links_core.check_private('setup', home='academy/teaching/classes/ai4good/CONTEXT.md')


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


# ── publish: a course page reaches the site whole, and nothing internal comes along ─────────────
import pages  # noqa: E402


@pytest.fixture
def course(tmp_path):
    """classes/<course>/ with a page, two artefacts and the CONTEXT.md every folder here carries."""
    classes = tmp_path / 'classes'
    (classes / 'ai4good' / 'artefatos').mkdir(parents=True)
    (classes / 'ai4good' / 'disciplina.md').write_text('# page\n', encoding='utf-8', newline='\n')
    for name in ('3-base.md', '5-arena.md', 'CONTEXT.md'):
        (classes / 'ai4good' / 'artefatos' / name).write_text(name, encoding='utf-8', newline='\n')
    return classes


def test_a_course_page_lands_under_its_course_name(course, tmp_path):
    page = course / 'ai4good' / 'disciplina.md'
    assert pages.mirror_of(page, tmp_path / 'site', course) == tmp_path / 'site' / 'ai4good' / 'disciplina.md'


@pytest.mark.parametrize('where', ['elsewhere/page.md', 'classes/ai4good/artefatos/3-base.md'])
def test_a_file_that_is_not_a_course_page_has_no_public_place(course, tmp_path, where):
    with pytest.raises(pages.Refused):
        pages.mirror_of(tmp_path / where, tmp_path / 'site', course)


def test_publishing_a_page_carries_its_artefacts_but_never_the_folder_notes(course, tmp_path):
    """The glob the old hand-written steps used shipped artefatos/CONTEXT.md to the public repo."""
    site = tmp_path / 'site'
    pages.mirror(course / 'ai4good' / 'disciplina.md', site, course)
    assert sorted(p.name for p in (site / 'ai4good' / 'artefatos').iterdir()) == ['3-base.md', '5-arena.md']
    assert (site / 'ai4good' / 'disciplina.md').read_text(encoding='utf-8') == '# page\n'


def test_an_artefact_folder_reaches_the_site_with_its_examples_but_not_its_notes(course, tmp_path):
    """artefatos/brw/ holds the model and the two examples a student opens from the artefact."""
    folder = course / 'ai4good' / 'artefatos' / 'brw'
    folder.mkdir()
    for name in ('modelo.md', 'excelente.md', 'CONTEXT.md'):
        (folder / name).write_text(name, encoding='utf-8', newline='\n')
    site = tmp_path / 'site'
    pages.mirror(course / 'ai4good' / 'disciplina.md', site, course)
    assert sorted(p.name for p in (site / 'ai4good' / 'artefatos' / 'brw').iterdir()) == ['excelente.md', 'modelo.md']


def test_a_page_without_a_drawn_block_runs_no_generator(course):
    assert pages.redraw(course / 'ai4good' / 'disciplina.md') == []


def test_resolve_page_finds_page_from_classes_or_relative_path(course, tmp_path):
    page = course / 'ai4good' / 'disciplina.md'
    assert pages.resolve_page(pathlib.Path('ai4good/disciplina.md'), classes=course, root=tmp_path) == page
    assert pages.resolve_page(page, classes=course, root=tmp_path) == page


def _git(cwd, *args):
    import subprocess
    # the workspace's global hooksPath judges workspace commits; a throwaway repo is not one
    return subprocess.run(['git', '-c', 'core.hooksPath=/dev/null', *args], cwd=cwd, check=True, capture_output=True, text=True, encoding='utf-8').stdout


@pytest.fixture
def browser_edit(course, tmp_path):
    """The site as the workspace last published it, then one commit made from the browser on top."""
    remote, site, other = tmp_path / 'remote.git', tmp_path / 'site', tmp_path / 'other'
    _git(tmp_path, 'init', '-q', '--bare', '-b', 'main', str(remote))
    _git(tmp_path, 'clone', '-q', str(remote), str(site))
    for repo in (site,):
        _git(repo, 'config', 'user.email', 't@t'); _git(repo, 'config', 'user.name', 't')
    page = course / 'ai4good' / 'disciplina.md'
    page.write_text('um\ndois\ntrês\nquatro\ncinco\n', encoding='utf-8', newline='\n')
    pages.mirror(page, site, course)
    _git(site, 'add', '-A'); _git(site, 'commit', '-q', '-m', 'publish'); _git(site, 'push', '-q', '-u', 'origin', 'HEAD')
    _git(tmp_path, 'clone', '-q', str(remote), str(other))
    _git(other, 'config', 'user.email', 'b@b'); _git(other, 'config', 'user.name', 'b')

    def edit(text, path='ai4good/disciplina.md'):
        (other / path).parent.mkdir(parents=True, exist_ok=True)
        (other / path).write_text(text, encoding='utf-8', newline='\n')
        _git(other, 'add', '-A'); _git(other, 'commit', '-q', '-m', f'editor: {path}'); _git(other, 'push', '-q')
    return page, site, edit


def test_a_browser_edit_comes_home_when_the_workspace_did_not_move(course, browser_edit):
    page, site, edit = browser_edit
    edit('um\nDOIS\ntrês\n')
    assert pages.pull(site, course) == [page]
    assert page.read_text(encoding='utf-8') == 'um\nDOIS\ntrês\n'


def test_a_browser_edit_and_a_workspace_edit_apart_both_survive(course, browser_edit):
    page, site, edit = browser_edit
    edit('UM\ndois\ntrês\nquatro\ncinco\n')
    page.write_text('um\ndois\ntrês\nquatro\nCINCO\n', encoding='utf-8', newline='\n')
    pages.pull(site, course)
    assert page.read_text(encoding='utf-8') == 'UM\ndois\ntrês\nquatro\nCINCO\n'


def test_the_same_line_changed_on_both_sides_is_refused_and_nothing_moves(course, browser_edit):
    page, site, edit = browser_edit
    edit('um\nbrowser\ntrês\n')
    page.write_text('um\nworkspace\ntrês\n', encoding='utf-8', newline='\n')
    head = _git(site, 'rev-parse', 'HEAD')
    with pytest.raises(pages.Refused, match='disciplina.md'):
        pages.pull(site, course)
    assert page.read_text(encoding='utf-8') == 'um\nworkspace\ntrês\n'
    assert _git(site, 'rev-parse', 'HEAD') == head


def test_deliveries_travel_both_ways_beside_the_page(course, browser_edit, tmp_path):
    """The slots' links live in entregas.tsv: the site writes it, publish carries it, pull brings it home."""
    page, site, edit = browser_edit
    edit('# aluno\tcódigo\tlink\nedson\tbrw\thttps://d/1\n', path='ai4good/entregas.tsv')
    assert pages.pull(site, course) == [course / 'ai4good' / 'entregas.tsv']
    assert 'https://d/1' in pages.mirror(page, tmp_path / 'other-site', course)[1].read_text(encoding='utf-8')
    edit('# aluno\tcódigo\tparecer\nedson\tbrw\tfalta a prova\n', path='ai4good/pareceres.tsv')
    assert pages.pull(site, course) == [course / 'ai4good' / 'pareceres.tsv']
    assert 'falta a prova' in pages.mirror(page, tmp_path / 'other-site', course)[2].read_text(encoding='utf-8')


def test_a_site_file_with_no_course_home_moves_the_clone_but_touches_no_workspace_file(course, browser_edit):
    page, site, edit = browser_edit
    edit('// viewer\n', path='viewer.js')
    assert pages.pull(site, course) == []
    assert (site / 'viewer.js').read_text(encoding='utf-8') == '// viewer\n'


def test_a_push_off_main_is_refused_because_only_main_goes_live(browser_edit):
    site = browser_edit[1]
    _git(site, 'switch', '-q', '-c', 'feature/x')
    head = _git(site, 'rev-parse', 'HEAD')
    with pytest.raises(pages.Refused, match='feature/x'):
        pages.push(site, ['ai4good'], 'redirects')
    assert _git(site, 'rev-parse', 'HEAD') == head


def test_a_page_with_habilidades_block_runs_arvore_generator(course):
    needs('academy'); page = course / 'ai4good' / 'disciplina.md'   # arvore.py lives in academy/
    page.write_text('<!-- habilidades:start -->\n<!-- habilidades:end -->', encoding='utf-8', newline='\n')
    (course / 'ai4good' / 'arvore.yaml').write_text('- nome: TestSkill\n  url: https://example.com/test\n', encoding='utf-8', newline='\n')
    assert 'arvore.py' in pages.redraw(page)
    assert '- **[testskill](https://example.com/test)**' in page.read_text(encoding='utf-8')

