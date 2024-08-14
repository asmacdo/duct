from __future__ import annotations
from datetime import datetime
from unittest import mock
import pytest
from con_duct.__main__ import (
    EXECUTION_SUMMARY_FORMAT,
    Averages,
    ProcessStats,
    Report,
    Sample,
)

stat0 = ProcessStats(
    pcpu=0.0, pmem=0, rss=0, vsz=0, timestamp="2024-06-11T10:09:37-04:00"
)

stat1 = ProcessStats(
    pcpu=1.0, pmem=0, rss=0, vsz=0, timestamp="2024-06-11T10:13:23-04:00"
)


def test_sample_max_initial_values_one_pid() -> None:
    maxes = Sample()
    ex0 = Sample()
    ex0.add_pid(1, stat0)
    maxes = maxes.max(ex0)
    assert maxes.stats == {1: stat0}


def test_sample_max_one_pid() -> None:
    maxes = Sample()
    maxes.add_pid(1, stat0)
    ex1 = Sample()
    ex1.add_pid(1, stat1)
    maxes = maxes.max(ex1)
    assert maxes.stats == {1: stat1}


def test_sample_max_initial_values_two_pids() -> None:
    maxes = Sample()
    ex0 = Sample()
    ex0.add_pid(1, stat0)
    ex0.add_pid(2, stat0)
    maxes = maxes.max(ex0)
    assert maxes.stats == {1: stat0, 2: stat0}


def test_sample_maxtwo_pids() -> None:
    maxes = Sample()
    maxes.add_pid(1, stat0)
    maxes.add_pid(2, stat0)
    ex1 = Sample()
    ex1.add_pid(1, stat1)
    maxes = maxes.max(ex1)
    ex2 = Sample()
    ex2.add_pid(2, stat1)
    maxes = maxes.max(ex2)
    assert maxes.stats == {1: stat1, 2: stat1}


def test_average_no_samples() -> None:
    averages = Averages()
    assert averages.num_samples == 0
    sample = Sample()
    sample.averages = averages
    serialized = sample.for_json()
    assert "averages" in serialized
    assert not serialized["averages"]


def test_averages_one_sample() -> None:
    sample = Sample()
    sample.add_pid(1, stat0)
    averages = Averages.from_sample(sample)
    assert averages.rss == sample.total_rss
    assert averages.vsz == sample.total_vsz
    assert averages.pmem == sample.total_pmem
    assert averages.pcpu == sample.total_pcpu
    assert averages.num_samples == 1


def test_averages_two_samples() -> None:
    sample = Sample()
    sample.add_pid(1, stat0)
    averages = Averages.from_sample(sample)
    sample2 = Sample()
    sample2.add_pid(2, stat1)
    averages.update(sample2)
    assert averages.pcpu == (stat0.pcpu + stat1.pcpu) / 2


def test_averages_three_samples() -> None:
    sample = Sample()
    sample.add_pid(1, stat0)
    averages = Averages.from_sample(sample)
    sample2 = Sample()
    sample2.add_pid(2, stat1)
    averages.update(sample2)
    averages.update(sample2)
    assert averages.pcpu == (stat0.pcpu + (2 * stat1.pcpu)) / 3


@pytest.mark.parametrize(
    "pcpu, pmem, rss, vsz",
    [
        (1.0, 1.1, 1024, 1025),
        (0.5, 0.7, 20.48, 40.96),
        (1, 2, 3, 4),
        (0, 0.0, 0, 0.0),
        (2.5, 3.5, 8192, 16384),
        (100.0, 99.9, 65536, 131072),
    ],
)
def test_process_stats_green(pcpu: float, pmem: float, rss: int, vsz: int) -> None:
    # Assert does not raise
    ProcessStats(
        pcpu=pcpu,
        pmem=pmem,
        rss=rss,
        vsz=vsz,
        timestamp=datetime.now().astimezone().isoformat(),
    )


@pytest.mark.parametrize(
    "pcpu, pmem, rss, vsz",
    [
        ("only", 1.1, 1024, 1025),
        (0.5, "takes", 20.48, 40.96),
        (1, 2, "one", 4),
        (1, 2, 3, "value"),
        ("2", "fail", "or", "more"),
    ],
)
def test_process_stats_red(pcpu: float, pmem: float, rss: int, vsz: int) -> None:
    with pytest.raises(AssertionError):
        ProcessStats(
            pcpu=pcpu,
            pmem=pmem,
            rss=rss,
            vsz=vsz,
            timestamp=datetime.now().astimezone().isoformat(),
        )


@mock.patch("con_duct.__main__.LogPaths")
@mock.patch("con_duct.__main__.subprocess.Popen")
def test_execution_summary_formatted(
    mock_popen: mock.MagicMock, mock_log_paths: mock.MagicMock
) -> None:
    mock_log_paths.prefix = "mock_prefix"
    report = Report(
        "_cmd", [], None, mock_popen, mock_log_paths, EXECUTION_SUMMARY_FORMAT, False
    )

    output = report.execution_summary_formatted
    assert "None" not in output
    assert "unknown" in output
