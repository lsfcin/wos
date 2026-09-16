# T1 chat stitching: an audio line must never lose what was said, a bot menu must never survive,
# and a secret must never reach a versioned file. Zero-token, no network, no model.
from __future__ import annotations
import sys, pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / 'chat'))
import chat_stitch as stitch  # noqa: E402

LINE = "06/07/2026 18:05 - Lucas S. Figueiredo: ‎PTT-20260706-WA0012.opus (arquivo anexado)"


def test_the_audio_filename_is_recovered_from_the_export_line():
    assert stitch.ATTACHED.search(LINE).group(1) == "PTT-20260706-WA0012.opus"


def test_a_transcribed_audio_keeps_its_line_and_gains_the_words(tmp_path):
    (tmp_path / "PTT-20260706-WA0012.opus.txt").write_text("Boa noite, Severino.", encoding="utf-8", newline='\n')
    out = stitch.fold(LINE, tmp_path)
    assert out[0] == LINE
    assert out[1] == "    ↳ Boa noite, Severino."


def test_an_audio_with_no_transcript_still_keeps_its_line(tmp_path):
    """A turn someone spoke must stay visible even when the words are missing — dropping the
    line would hide that anything was said at all."""
    assert stitch.fold(LINE, tmp_path) == [LINE]


def test_the_cartorio_bot_menu_is_dropped():
    assert stitch.is_noise("*[ 1 ]* - *Orçamento*")
    assert not stitch.is_noise("23/07/2026 13:15 - Lucas S. Figueiredo: enviei ontem comprovantes")


def test_the_header_reports_the_period_the_file_covers():
    text = "29/05/2026 16:02 - a: oi\n20/07/2026 10:15 - b: tchau"
    assert stitch.header("Severino", text, 3) == (
        "# Conversa com Severino — 29/05/2026 a 20/07/2026, 3 áudios transcritos inline.")


def test_a_punctuated_cpf_is_redacted_anywhere():
    assert "047.529.214-64" not in stitch.redact("CPF/CNPJ 047.529.214-64")


def test_a_bare_cpf_is_redacted_when_the_turn_before_asked_for_it():
    """How it actually arrives in chat: the ask and the number are different lines."""
    out = stitch.redact("Brenda: Me informa o seu CPF, por favor.\nLucas: o meu é 04752921464")
    assert "04752921464" not in out


def test_a_tracking_password_is_replaced_by_its_label():
    out = stitch.redact("utilizando o protocolo 45.992 e a senha 88028708.")
    assert "88028708" not in out
    assert "45.992" in out, "o protocolo não é segredo e é o que torna o processo consultável"


def test_a_phone_number_is_not_mistaken_for_a_cpf():
    text = "Fones: 32274780, 81991805024, 81988015824"
    assert stitch.redact(text) == text
