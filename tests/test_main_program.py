import logging
import os
from pathlib import Path
import smtplib
import subprocess
import sys
from types import SimpleNamespace

import pytest

import main_program


def test_get_base_path_standard(monkeypatch):
    monkeypatch.setattr(main_program.sys, "frozen", False, raising=False)
    expected = os.path.dirname(os.path.abspath(main_program.__file__))
    assert main_program.get_base_path() == expected


def test_get_base_path_frozen(monkeypatch, tmp_path):
    monkeypatch.setattr(main_program.sys, "frozen", True, raising=False)
    monkeypatch.setattr(main_program.sys, "_MEIPASS", str(tmp_path), raising=False)
    assert main_program.get_base_path() == str(tmp_path)


def test_get_kjv_verse_success(monkeypatch):
    captured_urls = []

    class DummyResponse:
        status_code = 200

        def __init__(self):
            self._json = {"verses": [
                {"verse": 16, "text": "Verse one."},
                {"verse": 17, "text": "Verse two."}
            ]}

        def raise_for_status(self):
            return None

        def json(self):
            return self._json

    def fake_get(url, timeout):
        captured_urls.append(url)
        return DummyResponse()

    monkeypatch.setattr(main_program.requests, "get", fake_get)
    verses = main_program.get_kjv_verse("John 3:16")
    assert verses == [
        {"verse": 16, "text": "Verse one."},
        {"verse": 17, "text": "Verse two."}
    ]
    assert "john%203%3a16" in captured_urls[0].lower()


def test_get_kjv_verse_handles_error(monkeypatch):
    def fake_get(url, timeout):
        raise main_program.requests.exceptions.RequestException("boom")

    monkeypatch.setattr(main_program.requests, "get", fake_get)
    assert main_program.get_kjv_verse("John 3:16") == []


def test_setup_logging_creates_file(app_env):
    logger = main_program.setup_logging()
    log_files = list(app_env.logs_dir.glob("app_*.log"))
    try:
        assert log_files, "Expected a log file to be created"
        assert any(isinstance(handler, logging.handlers.RotatingFileHandler) for handler in logger.handlers)
    finally:
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
            handler.close()


def test_init_file_creates_agenda_file(app_env):
    assert app_env.next_markdown.exists()
    content = app_env.next_markdown.read_text()
    assert app_env.next_week_str in content
    assert "2024-01-20" not in content.splitlines()[0]
    assert (app_env.next_markdown.stat().st_mode & 0o777) == 0o777
    assert (main_program.INPUT_DIR.stat().st_mode & 0o777) == 0o555


def test_bible_reading_updates_rotation(app_env):
    result = main_program.bible_reading()
    assert result["status"] == "success"
    updated = app_env.next_markdown.read_text()
    assert "Bible Reading Rotation - 1 Corinthians 13:1-13" in updated


def test_prayer_card_advances_page(app_env):
    result = main_program.prayer_card()
    assert result["status"] == "success"
    updated = app_env.next_markdown.read_text()
    assert "Prayer Card Together - Page 2 Faithful Witnesses:" in updated
    assert "Acts 1:8" in updated


def test_international_reading_inserts_text(app_env):
    result = main_program.international_reading()
    assert result["status"] == "success"
    updated = app_env.next_markdown.read_text()
    assert "International Reading by TaeWoo Lee" in updated
    assert "stand firm" in updated


def test_state_reading_updates_section(app_env):
    result = main_program.state_reading()
    assert result["status"] == "success"
    updated = app_env.next_markdown.read_text()
    assert "State Reading by Alvin Beverly" in updated
    assert "Florida leadership" in updated


def test_widow_prayer_formats_names(app_env):
    result = main_program.widow_prayer()
    assert result["status"] == "success"
    updated = app_env.next_markdown.read_text()
    assert "Pray for the Widows by Donald Tise - 27. Faithful Families" in updated
    assert "Sanford - Jane Doe" in updated


def test_pastor_prayer_cycles_entry(app_env):
    result = main_program.pastor_prayer()
    assert result["status"] == "success"
    updated = app_env.next_markdown.read_text()
    assert "Church Beta - Pastor Beta" in updated


def test_print_v1_runs_lp_six_times(app_env, monkeypatch):
    calls = []

    def fake_run(cmd, capture_output, text, check):
        calls.append(cmd)
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    assert main_program.print_v1_6x()["status"] == "success"
    assert len(calls) == 6
    assert all(cmd[:2] == ["lp", "-n"] for cmd in calls)


def test_print_v1_handles_print_error(app_env, monkeypatch):
    def fake_run(cmd, capture_output, text, check):
        return SimpleNamespace(returncode=1, stdout="", stderr="printer jam")

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = main_program.print_v1_6x()
    assert result["status"] == "error"
    assert "printer jam" in result["error"]


def test_kjv_verses_inserts_verses(app_env, monkeypatch):
    references = []

    def fake_get(reference):
        references.append(reference)
        return [
            {"verse": 4, "text": f"{reference} verse 1"},
            {"verse": 5, "text": f"{reference} verse 2"},
        ]

    monkeypatch.setattr(main_program, "get_kjv_verse", fake_get)
    result = main_program.kjv_verses()
    assert result["status"] == "success"
    agenda = app_env.next_markdown.read_text()
    assert "4. Romans 5:1-2 verse 1" in agenda
    assert "5. Romans 5:1-2 verse 2" in agenda
    assert references[-1] == "Romans 5:1-2"


def test_kjv_verses_handles_reference_without_explicit_verse(app_env, monkeypatch):
    def fake_get(reference):
        if reference == "Genesis 1":
            return [
                {"verse": None, "text": "In the beginning reference text."},
                {"verse": None, "text": "And the earth was without form."},
            ]
        if reference == "Romans 5:1-2":
            return []
        return []

    monkeypatch.setattr(main_program, "get_kjv_verse", fake_get)
    result = main_program.kjv_verses()
    assert result["status"] == "success"
    agenda = app_env.next_markdown.read_text()
    assert "1. In the beginning reference text." in agenda
    assert "2. And the earth was without form." in agenda


def test_print_v2_runs_once(app_env, monkeypatch):
    calls = []

    def fake_run(cmd, capture_output, text, check):
        calls.append(cmd)
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    assert main_program.print_v2_1x()["status"] == "success"
    assert len(calls) == 1
    assert calls[0][:2] == ["lp", "-n"]


def test_print_v2_handles_error(app_env, monkeypatch):
    def fake_run(cmd, capture_output, text, check):
        return SimpleNamespace(returncode=1, stdout="", stderr="no printer")

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = main_program.print_v2_1x()
    assert result["status"] == "error"
    assert "no printer" in result["error"]


def test_email_v2_sends_message(app_env, monkeypatch):
    app_env.next_docx_path.write_text("docx data")
    sent_messages = []

    class FakeSMTP:
        def __init__(self, host, port):
            self.host = host
            self.port = port

        def starttls(self):
            sent_messages.append("starttls")

        def login(self, user, password):
            sent_messages.append(("login", user, password))

        def sendmail(self, from_addr, to_addrs, msg):
            sent_messages.append(("sendmail", from_addr, tuple(to_addrs)))

        def quit(self):
            sent_messages.append("quit")

    monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)
    result = main_program.email_v2()
    assert result["status"] == "success"
    assert any(isinstance(entry, tuple) and entry[0] == "sendmail" for entry in sent_messages)


def test_email_v2_handles_failure(app_env, monkeypatch):
    app_env.next_docx_path.write_text("docx data")

    class FakeSMTP:
        def __init__(self, host, port):
            pass

        def starttls(self):
            pass

        def login(self, user, password):
            pass

        def sendmail(self, from_addr, to_addrs, msg):
            raise RuntimeError("smtp down")

        def quit(self):
            pass

    monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)
    result = main_program.email_v2()
    assert result["status"] == "error"
    assert "smtp down" in result["error"].lower()


def test_email_v2_missing_attachment(app_env):
    app_env.next_docx_path.unlink(missing_ok=True)
    result = main_program.email_v2()
    assert result["status"] == "error"
    assert "missing" in result["error"].lower()


def test_copy_file_v1_handles_missing_agenda(app_env):
    main_program.NEXT_WEEK_AGENDA_FILE.unlink()
    result = main_program.copy_file_v1()
    assert result["status"] == "error"
    assert "not found" in result["error"].lower()


def test_move_file_v2_requires_docx(app_env):
    app_env.next_docx_path.unlink(missing_ok=True)
    result = main_program.move_file_v2()
    assert result["status"] == "error"
    assert "DOCX" in result["error"]


def test_copy_file_v1_moves_latest_file(app_env):
    destination = main_program.INPUT_DIR / f"{app_env.next_week_str} Saturday Prayer Breakfast Agenda.md"
    last_week_file = main_program.INPUT_DIR / f"{app_env.last_week_str} Saturday Prayer Breakfast Agenda.md"
    assert last_week_file.exists()
    assert not destination.exists()
    result = main_program.copy_file_v1()
    assert result["status"] == "success"
    assert destination.exists()
    assert not last_week_file.exists()
    assert (main_program.INPUT_DIR.stat().st_mode & 0o777) == 0o555


def test_move_file_v2_transfers_files(app_env):
    app_env.next_docx_path.write_text("docx data")
    result = main_program.move_file_v2()
    assert result["status"] == "success"
    assert main_program.NEXT_WEEK_AGENDA_FILE.parent == app_env.temp_dir
    assert main_program.NEXT_WEEK_AGENDA_FILE.exists()
    assert (app_env.temp_dir.stat().st_mode & 0o777) == 0o555


def test_convert_file_uses_docx_module(app_env, monkeypatch):
    created = []

    class DummyDocument:
        def __init__(self):
            self.content = []
            created.append(self)

        def add_paragraph(self, text, style=None):
            self.content.append(("paragraph", text, style))

        def add_heading(self, text, level=1):
            self.content.append(("heading", text, level))

        def save(self, path):
            self.saved_path = path
            Path(path).write_text("docx data")

    fake_docx = SimpleNamespace(Document=DummyDocument)
    monkeypatch.setitem(sys.modules, "docx", fake_docx)
    app_env.next_docx_path.unlink(missing_ok=True)
    result = main_program.convert_file()
    assert result["status"] == "success"
    doc = created[-1]
    assert doc.saved_path == str(app_env.next_docx_path)


@pytest.mark.parametrize(
    "procedure_name",
    ["procedure_15", "procedure_16", "procedure_17", "procedure_18", "procedure_19", "procedure_20"],
)
def test_placeholder_procedures_return_success(procedure_name):
    proc = getattr(main_program, procedure_name)
    assert proc()["status"] == "success"


def test_main_reports_failures(monkeypatch):
    fake_logger = SimpleNamespace(
        info=lambda *args, **kwargs: None,
        debug=lambda *args, **kwargs: None,
        warning=lambda *args, **kwargs: None,
        error=lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(main_program, "setup_logging", lambda: fake_logger)
    monkeypatch.setattr(main_program.os, "makedirs", lambda *args, **kwargs: None)

    procedure_order = [
        "init_file",
        "bible_reading",
        "prayer_card",
        "international_reading",
        "state_reading",
        "widow_prayer",
        "pastor_prayer",
        "print_v1_6x",
        "copy_file_v1",
        "kjv_verses",
        "print_v2_1x",
        "convert_file",
        "email_v2",
        "move_file_v2",
        "procedure_15",
        "procedure_16",
        "procedure_17",
        "procedure_18",
        "procedure_19",
        "procedure_20",
    ]
    calls = []

    def make_proc(name, status="success", raise_error=False):
        def _proc():
            calls.append(name)
            if raise_error:
                raise RuntimeError("boom")
            return {"status": status, "procedure": name}

        return _proc

    monkeypatch.setattr(main_program, "init_file", make_proc("init_file"))
    monkeypatch.setattr(main_program, "bible_reading", make_proc("bible_reading"))
    monkeypatch.setattr(main_program, "prayer_card", make_proc("prayer_card", status="error"))
    monkeypatch.setattr(main_program, "international_reading", make_proc("international_reading"))
    monkeypatch.setattr(main_program, "state_reading", make_proc("state_reading"))
    monkeypatch.setattr(main_program, "widow_prayer", make_proc("widow_prayer"))
    monkeypatch.setattr(main_program, "pastor_prayer", make_proc("pastor_prayer", raise_error=True))
    monkeypatch.setattr(main_program, "print_v1_6x", make_proc("print_v1_6x"))
    monkeypatch.setattr(main_program, "copy_file_v1", make_proc("copy_file_v1"))
    monkeypatch.setattr(main_program, "kjv_verses", make_proc("kjv_verses"))
    monkeypatch.setattr(main_program, "print_v2_1x", make_proc("print_v2_1x"))
    monkeypatch.setattr(main_program, "convert_file", make_proc("convert_file"))
    monkeypatch.setattr(main_program, "email_v2", make_proc("email_v2"))
    monkeypatch.setattr(main_program, "move_file_v2", make_proc("move_file_v2"))
    for name in ["procedure_15", "procedure_16", "procedure_17", "procedure_18", "procedure_19", "procedure_20"]:
        monkeypatch.setattr(main_program, name, make_proc(name))

    exit_code = main_program.main()
    assert exit_code == 1
    assert calls[: len(procedure_order)] == procedure_order
