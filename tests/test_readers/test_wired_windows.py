import os

from chromhandler import Handler


def test_windows() -> None:
    path = "docs/examples/data/agilent_rdl"

    # print path and all files in the directory
    print(path)
    print(os.listdir(path))

    # Create a Handler object
    ana = Handler.read_agilent(
        path=path,
        ph=7.0,
        temperature=25.0,
        mode="timecourse",
    )

    assert len(ana.measurements) == 2
