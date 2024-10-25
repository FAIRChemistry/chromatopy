import os

from chromatopy import ChromAnalyzer


def test_windows():
    path = "docs/examples/data/agilent_rdl"

    # print path and all files in the directory
    print(path)
    print(os.listdir(path))

    # Create a ChromAnalyzer object
    ana = ChromAnalyzer.read_agilent(
        path=path,
        ph=7.0,
        temperature=25.0,
        mode="timecourse",
    )

    assert len(ana.measurements) == 2
