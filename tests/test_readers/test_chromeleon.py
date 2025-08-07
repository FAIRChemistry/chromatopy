from chromhandler.handler import Handler


def test_read_chromeleon() -> None:
    dir_path = "docs/usage/data/chromeleon"

    ana = Handler.read_chromeleon(
        path=dir_path,
        values=[0] * 6,
        unit="min",
        ph=7.4,
        temperature=25.0,
        temperature_unit="Celsius",
        mode="timecourse",
    )

    assert len(ana.measurements) == 6
