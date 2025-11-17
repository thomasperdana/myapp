from datetime import datetime as real_datetime
from pathlib import Path
import sys
from types import SimpleNamespace
import textwrap

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import main_program


FIXED_NOW = real_datetime(2024, 1, 24, 8, 0, 0)


class FixedDateTime(real_datetime):
    @classmethod
    def now(cls, tz=None):
        if tz:
            return tz.fromutc(FIXED_NOW.replace(tzinfo=tz))
        return FIXED_NOW


def _create_input_files(input_dir):
    input_dir.mkdir(parents=True, exist_ok=True)

    agenda_content = textwrap.dedent(
        """
        North Seminole County Gideons - 2024-01-20 Saturday Prayer Breakfast Agenda
        Bible Reading Rotation - Genesis 1
        Prayer Card Together - Page 1 Hope Section: 1. Share the Gospel
        International Reading by Current Reader
        Old international content line

        State Reading by Someone
        Legacy state reading content

        Pray for the Widows by Donald Tise - 26. Early Church
        Old widow entry

        Pray for Local Pastor by Johnny Perry - Church Alpha - Pastor Alpha
        Devotional Thought - Romans 5:1-2
        """
    ).strip()
    (input_dir / "2024-01-20 Saturday Prayer Breakfast Agenda.md").write_text(
        agenda_content
    )

    hq2 = textwrap.dedent(
        """
        ## **JANUARY**
        | Date | Evening |
        |------|---------|
        | 27 | 1 Corinthians 13:1-13 |
        | 28 | Romans 8 |
        """
    ).strip()
    (input_dir / "hq2.md").write_text(hq2)

    prayer = textwrap.dedent(
        """
        ## Page 2
        ### Faithful Witnesses
        2. Encourage the faithful
        * Acts 1:8
        """
    ).strip()
    (input_dir / "prayer.md").write_text(prayer)

    hq1 = textwrap.dedent(
        """
        ## **DAY 27**
        Pray for believers to stand firm.

        ## **DAY 28**
        Pray for courage.
        """
    ).strip()
    (input_dir / "hq1.md").write_text(hq1)

    state = textwrap.dedent(
        """
        ## Day 27
        Pray for Florida leadership.
        Remember the upcoming outreach.

        ---

        ## Day 28
        Continue praying.
        """
    ).strip()
    (input_dir / "fl.md").write_text(state)

    widow = textwrap.dedent(
        """
        ### 27. Faithful Families
        - Jane Doe, Sanford
        - Mary Major, Longwood
        - Ellen Grace, Lake Mary
        """
    ).strip()
    (input_dir / "widow.md").write_text(widow)

    pastor = textwrap.dedent(
        """
        | # | Pastor Name | Church Name |
        |---|-------------|-------------|
        | 1 | Pastor Alpha | Church Alpha |
        | 2 | Pastor Beta | Church Beta |
        """
    ).strip()
    (input_dir / "pastor.md").write_text(pastor)


def _reset_globals():
    main_program.INPUT_DIR = None
    main_program.OUTPUT_DIR = None
    main_program.LAST_WEEK_DATE = None
    main_program.NEXT_WEEK_DATE = None
    main_program.NEXT_WEEK_AGENDA_FILE = None
    main_program.NEXT_WEEK_AGENDA_FILE_DOCX = None


@pytest.fixture
def app_env(tmp_path, monkeypatch):
    base_dir = tmp_path / "myapp"
    (base_dir / "output").mkdir(parents=True, exist_ok=True)
    (base_dir / "logs").mkdir(parents=True, exist_ok=True)
    (base_dir / "temp").mkdir(parents=True, exist_ok=True)
    _create_input_files(base_dir / "input")

    monkeypatch.setenv("MYAPP_BASE_DIR", str(base_dir))
    main_program.APP_BASE_DIR = base_dir
    monkeypatch.setattr(main_program, "datetime", FixedDateTime)

    _reset_globals()
    result = main_program.init_file()
    assert result["status"] == "success"

    env = SimpleNamespace(
        base_dir=base_dir,
        input_dir=base_dir / "input",
        output_dir=base_dir / "output",
        logs_dir=base_dir / "logs",
        temp_dir=base_dir / "temp",
        last_week_str="2024-01-20",
        next_week_str="2024-01-27",
        next_markdown=main_program.NEXT_WEEK_AGENDA_FILE,
        next_docx_path=main_program.NEXT_WEEK_AGENDA_FILE_DOCX,
    )

    yield env

    for path in env.input_dir.rglob("*"):
        path.chmod(0o755)
    env.input_dir.chmod(0o755)
    env.temp_dir.mkdir(exist_ok=True)
    env.temp_dir.chmod(0o755)
