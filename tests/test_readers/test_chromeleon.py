from chromatopy.tools.analyzer import ChromAnalyzer


def test_read_chromeleon() -> None:
    dir_path = "docs/examples/data/chromeleon"

    ana = ChromAnalyzer.read_chromeleon(
        path=dir_path,
        values=[0] * 6,
        unit="min",
        ph=7.4,
        temperature=25.0,
        temperature_unit="C",
        mode="timecourse",
    )

    assert len(ana.measurements) == 6
