# T1 pdf twin: the frontmatter says what was converted and when it went stale, the git rule follows the origin, and a secret keeps the whole twin out of git. Zero-token, no network, no engine.
import pytest
from PIL import Image

import describe
import pdf_meta
import pdf_twin

WORDS = 'Resolução do conselho universitário sobre o projeto pedagógico do curso de computação aprovado hoje'


def make_pdf(path, text=WORDS):
    """The smallest PDF poppler reads as born-digital: one page, one line of Helvetica."""
    body = f'BT /F1 10 Tf 40 700 Td ({text}) Tj ET'.encode('latin-1')
    objs = [b'<< /Type /Catalog /Pages 2 0 R >>', b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
            b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R '
            b'/Resources << /Font << /F1 5 0 R >> >> >>',
            b'<< /Length %d >>\nstream\n' % len(body) + body + b'\nendstream',
            b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>']
    out, offsets = b'%PDF-1.4\n', []
    for n, obj in enumerate(objs, 1):
        offsets.append(len(out))
        out += b'%d 0 obj\n' % n + obj + b'\nendobj\n'
    xref = len(out)
    out += b'xref\n0 %d\n0000000000 65535 f \n' % (len(objs) + 1)
    out += b''.join(b'%010d 00000 n \n' % o for o in offsets)
    out += b'trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n' % (len(objs) + 1, xref)
    path.write_bytes(out)
    return path


def fake_engine(page_md=WORDS, figures=1):
    def run(engine, pdf, out):
        figs = []
        for i in range(figures):
            png = out / f'f{i}.png'
            Image.new('RGB', (80, 60), (40 * i, 200, 90)).save(png)
            figs.append({'page': 1, 'file': str(png)})
        return {'engine': f'{engine} 9.9', 'figures': figs,
                'pages': [page_md + '\n\n<!-- figure -->' * figures]}
    return run


def said(image, describer, ocr_text):
    return describe.Description('a green rectangle', describer, None, False)


def build(pdf, **kw):
    kw.setdefault('_engine', fake_engine())
    return pdf_twin.build(pdf, kw.pop('engine', 'docling'), _describe=said, _ocr=lambda p: '', **kw)


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    monkeypatch.setattr(pdf_twin, 'origin_live', lambda url: url == 'https://live.example/x.pdf')


def test_the_frontmatter_names_the_source_the_hash_and_the_audit(tmp_path):
    pdf = make_pdf(tmp_path / 'res.pdf')
    done = build(pdf)
    front = pdf_meta.read_frontmatter(done['twin'])
    assert done['twin'] == tmp_path / 'res' / 'res.md'
    assert set(front) == set(pdf_meta.FIELDS)
    assert (front['source'], front['sha256']) == ('../res.pdf', pdf_meta.sha256(pdf))
    assert (front['text_layer'], front['engine'], front['pdf']['pages']) == ('born-digital', 'docling 9.9', 1)
    assert front['audit']['word_coverage'] == 1.0 and front['audit']['pages'] == '1/1'
    assert '<!-- page 1 -->' in done['twin'].read_text(encoding='utf-8')


def test_a_description_is_what_the_routing_table_reads_and_survives_a_rebuild(tmp_path):
    """Without one, every twin routed as a placeholder: the engine cannot know what a PDF is for."""
    import pdf_cli
    from workspace_meta import file_description
    pdf = make_pdf(tmp_path / 'res.pdf')
    twin = build(pdf)['twin']
    assert pdf_meta.read_frontmatter(twin)['description'] is None
    pdf_cli.label(pdf, 'Resolução que aprova o projeto pedagógico')
    assert file_description(twin) == 'Resolução que aprova o projeto pedagógico'
    pdf.write_bytes(pdf.read_bytes() + b'% edited\n')
    build(pdf)
    assert pdf_meta.read_frontmatter(twin)['description'] == 'Resolução que aprova o projeto pedagógico'


def test_a_fresh_twin_is_skipped_and_a_changed_pdf_is_rebuilt(tmp_path):
    pdf = make_pdf(tmp_path / 'res.pdf')
    build(pdf)
    assert build(pdf)['status'] == 'fresh'
    pdf.write_bytes(pdf.read_bytes() + b'% edited\n')
    assert build(pdf)['status'] == 'written'


def test_the_twin_state_is_absent_then_fresh_then_stale(tmp_path):
    """The one definition the build and the read gate both ask."""
    pdf = make_pdf(tmp_path / 'res.pdf')
    assert pdf_meta.twin_state(pdf) == ('absent', tmp_path / 'res' / 'res.md')
    build(pdf)
    assert pdf_meta.twin_state(pdf)[0] == 'fresh'
    pdf.write_bytes(pdf.read_bytes() + b'% edited\n')
    assert pdf_meta.twin_state(pdf)[0] == 'stale'


def test_render_hands_back_every_asked_page_in_page_order(tmp_path):
    pdf = make_pdf(tmp_path / 'res.pdf')
    assert [p.name for p in pdf_meta.render(pdf, tmp_path / 'pg', dpi=30)] == ['pg-1.png']
    assert pdf_meta.render(pdf, tmp_path / 'none', [9], 30) == []   # no page 9: missing, not a crash


def test_a_lost_page_or_word_flags_the_twin_for_review(tmp_path):
    pdf = make_pdf(tmp_path / 'res.pdf')
    assert build(pdf, _engine=fake_engine('Resolução'))['needs_review'] is True


def test_no_origin_versions_small_previews_and_keeps_originals_local(tmp_path):
    folder = build(make_pdf(tmp_path / 'res.pdf'))['twin'].parent
    assert (folder / 'img' / 'p01-fig1.jpg').exists() and (folder / 'img' / 'p01-fig1.png').exists()
    assert (folder / '.gitignore').read_text(encoding='utf-8').splitlines()[0] == 'img/*.png'
    assert '](img/p01-fig1.jpg)' in (folder / 'res.md').read_text(encoding='utf-8')


def test_a_live_origin_keeps_every_image_out_of_git(tmp_path):
    done = build(make_pdf(tmp_path / 'res.pdf'), origin='https://live.example/x.pdf')
    folder = done['twin'].parent
    assert not (folder / 'img' / 'p01-fig1.jpg').exists()
    assert (folder / '.gitignore').read_text(encoding='utf-8').splitlines()[0] == 'img/'
    assert pdf_meta.read_frontmatter(done['twin'])['origin'] == 'https://live.example/x.pdf'


def test_a_secret_in_the_text_gitignores_the_whole_twin(tmp_path):
    cpf = '.'.join(['123', '456', '789']) + '-09'   # assembled here so this file carries none
    done = build(make_pdf(tmp_path / 'res.pdf'), _engine=fake_engine(f'{WORDS}\n\nCPF: {cpf}'))
    assert done['secrets'] and (done['twin'].parent / '.gitignore').read_text(encoding='utf-8').splitlines()[0] == '*'


def test_both_engines_write_the_same_twin_but_for_the_engine_line(tmp_path):
    texts = {}
    for engine in ('docling', 'pymupdf'):
        (tmp_path / engine).mkdir()
        done = build(make_pdf(tmp_path / engine / 'res.pdf'), engine=engine)
        texts[engine] = [ln for ln in done['twin'].read_text(encoding='utf-8').splitlines()
                         if not ln.startswith('engine:')]
    assert texts['docling'] == texts['pymupdf']


def test_a_missing_engine_venv_hands_back_the_install_command(tmp_path, monkeypatch):
    monkeypatch.setattr(pdf_twin, 'ENGINE_VENV', '.venv-absent')
    with pytest.raises(pdf_twin.EngineMissing, match='requirements-pdf.txt'):
        pdf_twin.run_engine('docling', make_pdf(tmp_path / 'res.pdf'), tmp_path)


def test_a_twin_is_generated_by_its_stamp_even_with_its_pdf_gone(tmp_path):
    """The size caps exempt a twin (file_law.is_generated_artifact): branches/casinhas versions its
    twins and keeps its PDFs in the Drive, so the stamp is asked, never the PDF beside it."""
    import file_law
    twin = build(make_pdf(tmp_path / 'res.pdf'))['twin']
    (tmp_path / 'res.pdf').unlink()
    assert pdf_meta.is_twin(twin) and file_law.is_generated_artifact(twin, tmp_path)
    hand = tmp_path / 'notes' / 'notes.md'
    hand.parent.mkdir()
    hand.write_text('---\nsource: "../other.pdf"\n---\nmine\n', encoding='utf-8', newline='\n')
    assert not pdf_meta.is_twin(hand) and not file_law.is_generated_artifact(hand, tmp_path)
