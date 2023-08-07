import pandas as pd

from typing import List
from HPLC.core.hplcexperiment import HPLCExperiment
from HPLC.core.peak import Peak
from HPLC.core.signaltype import SignalType


def subset_by_retention_time(
    hplc_experiment: HPLCExperiment,
    retention_time: float,
    tolerance: float = 0.1,
    detector: SignalType = "fid",
) -> List[Peak]:

    df = _get_dataframe(hplc_experiment)

    df = df[df.signal_type == detector]

    lower_ret = retention_time - tolerance
    upper_ret = retention_time + tolerance
    df = df[df["retention_time"].between(lower_ret, upper_ret)]

    return df


def _get_dataframe(hplc_experiment: HPLCExperiment) -> pd.DataFrame:

    datas = []
    for measurement in hplc_experiment.measurements:
        for signal in measurement.signals:
            for peak in signal.peaks:
                peak_data = dict(
                    timestamp=measurement.timestamp,
                    signal_type=signal.type,
                    peak_id=peak.id,
                    retention_time=peak.retention_time,
                    area=peak.area,
                    height=peak.height,
                    width=peak.width,
                )

                datas.append(peak_data)

    return pd.DataFrame(datas)
