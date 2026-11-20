# T1 describe: an answer that ignores the image's own text is escalated, and a chain that runs out keeps its best answer flagged rather than nothing. Zero-token, no network.
import describe
import video_media

OCR = 'Receita Federal cadastro pessoa física número inscrição'


def backends(**answers):
    """Fake describers: a string is the answer, an exception is raised, a missing name is unused."""
    def make(name, answer):
        def run(image, prompt):
            if isinstance(answer, Exception):
                raise answer
            return answer, name
        return run
    return {name: make(name, answer) for name, answer in answers.items()}


def test_overlap_counts_the_ocr_words_the_description_kept():
    assert describe.overlap(OCR, 'Um cartão da Receita Federal com cadastro e número de inscrição') == round(5 / 7, 2)


def test_too_little_ocr_cannot_judge_so_any_answer_passes():
    assert describe.overlap('ok', 'anything') is None
    said = describe.describe('x.png', 'agy', 'ok', backends=backends(agy='a photo of a tree'))
    assert (said.by, said.needs_review) == ('agy', False)


def test_an_invented_description_escalates_to_the_next_describer():
    said = describe.describe('x.png', 'agy', OCR, backends=backends(
        agy='a bar chart about sales', claude='cartão Receita Federal, cadastro pessoa física, número inscrição'))
    assert (said.by, said.needs_review) == ('claude', False)


def test_a_failing_or_empty_describer_is_skipped_not_raised():
    said = describe.describe('x.png', 'local', OCR, backends=backends(
        local=RuntimeError('ollama down'), agy='   ', claude='Receita Federal cadastro pessoa física número'))
    assert said.by == 'claude'


def test_when_every_describer_fails_the_check_the_best_is_kept_and_flagged():
    said = describe.describe('x.png', 'agy', OCR, backends=backends(
        agy='a chart', claude='a card from the Receita Federal'))
    assert (said.by, said.needs_review, said.text) == ('claude', True, 'a card from the Receita Federal')


def test_nothing_at_all_is_an_empty_flagged_description():
    said = describe.describe('x.png', 'claude', OCR, backends=backends(claude=RuntimeError('no')))
    assert said == describe.Description('', None, None, True)


def test_video_frames_go_through_the_shared_describer(monkeypatch):
    seen = {}

    def fake(image, describer, ocr_text='', prompt=describe.FIGURE_PROMPT, backends=None):
        seen.update(image=image, describer=describer, prompt=prompt)
        return describe.Description('a dog on a beach', 'agy', None, False)
    monkeypatch.setattr(describe, 'describe', fake)
    assert video_media.caption_image('f.png') == 'a dog on a beach'
    assert seen == {'image': 'f.png', 'describer': 'agy', 'prompt': describe.FRAME_PROMPT}


def test_agy_logged_out_is_asked_once_and_never_prompted(monkeypatch, capsys):
    """Logged out, `agy -p` opens a browser login per figure; `agy models` lists nothing instead."""
    calls = []

    def run(cmd, **kw):
        calls.append(cmd)
        assert kw.get('stdin') is describe.subprocess.DEVNULL
        return describe.subprocess.CompletedProcess(cmd, 0, stdout='Fetching available models...\n', stderr='')
    monkeypatch.setattr(describe, '_AGY_LOGGED_IN', None)
    monkeypatch.setattr(describe.subprocess, 'run', run)
    assert not describe.agy_logged_in() and not describe.agy_logged_in()
    assert calls == [['agy', 'models']] and 'agy is not logged in' in capsys.readouterr().err


def test_agy_logged_in_lists_its_models(monkeypatch):
    monkeypatch.setattr(describe, '_AGY_LOGGED_IN', None)
    monkeypatch.setattr(describe.subprocess, 'run', lambda cmd, **kw: describe.subprocess.CompletedProcess(
        cmd, 0, stdout='gemini-3.8-flash-high\tGemini 3.8 Flash (High)\n', stderr=''))
    assert describe.agy_logged_in()
