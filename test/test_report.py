from __future__ import annotations
from datetime import datetime
import pytest
from con_duct.__main__ import Averages, ProcessStats, Sample

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


def test_process_stats_green() -> None:
    # Assert does not raise
    ProcessStats(
        pcpu=1.0,
        pmem=1.1,
        rss=1024,
        vsz=1025,
        timestamp=datetime.now().astimezone().isoformat(),
    )


def test_process_stats_handle_ints() -> None:
    # Assert does not raise
    ProcessStats(
        pcpu=1,
        pmem=1,
        rss=1024,
        vsz=1025,
        timestamp=datetime.now().astimezone().isoformat(),
    )


def test_process_stats_incorrect_pcpu_type() -> None:
    with pytest.raises(TypeError):
        ProcessStats(
            pcpu="oopsie",  # type: ignore[arg-type]
            pmem=1.1,
            rss=1024,
            vsz=1025,
            timestamp=datetime.now().astimezone().isoformat(),
        )


def test_process_stats_incorrect_pmem_type() -> None:
    with pytest.raises(TypeError):
        ProcessStats(
            pcpu=1.1,
            pmem="oopsie",  # type: ignore[arg-type]
            rss=1024,
            vsz=1025,
            timestamp=datetime.now().astimezone().isoformat(),
        )


def test_process_stats_incorrect_rss_type() -> None:
    with pytest.raises(TypeError):
        ProcessStats(
            pcpu=1.1,
            pmem=1.0,
            rss="oopsie",  # type: ignore[arg-type]
            vsz=1025,
            timestamp=datetime.now().astimezone().isoformat(),
        )


def test_process_stats_incorrect_vsz_type() -> None:
    with pytest.raises(TypeError):
        ProcessStats(
            pcpu=1.1,
            pmem=1.0,
            rss=1025,
            vsz="oopsie",  # type: ignore[arg-type]
            timestamp=datetime.now().astimezone().isoformat(),
        )


def test_averages_assert_num_green() -> None:
    # Assert does not raise
    Averages._assert_num(0, 1, 1.0, 0.1)


def test_averages_assert_num_invalid() -> None:
    with pytest.raises(AssertionError):
        Averages._assert_num("oops")  # type: ignore[arg-type]
