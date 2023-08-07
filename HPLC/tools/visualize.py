

import plotly.express as px
import plotly.graph_objs as go
import pandas as pd
import numpy as np

from collections import defaultdict
from typing import Dict, List, Union
from HPLC.core.hplcexperiment import HPLCExperiment
from HPLC.core.measurement import Measurement
from HPLC.core.signaltype import SignalType
from HPLC.core.signal import Signal
from HPLC.core.peak import Peak
from HPLC.tools.analyze import _get_dataframe, subset_by_retention_time


def visualize_chromatogram(measurement: Measurement, signal_type: SignalType):
    """Visualizes a chromatogram of a single measurement."""

    signal = _get_signals_by_type(measurement, signal_type)

    peaks = [peak.__dict__ for peak in signal.peaks]
    peak_df = pd.DataFrame.from_dict(peaks)

    fig = px.bar(peak_df, x='retention_time', y='area',
                 log_y=True, custom_data=['id', 'type'])

    fig.update_traces(
        hovertemplate="<br>".join([
            "id: %{customdata[0]}",
            "retention_time: %{x}",
            "area: %{y}",
            "type: %{customdata[1]}",
        ])
    )

    fig.show()


def _get_peak_by_retention_time(
    peaks: List[Peak],
    retention_time: float,
    tolerance: float = 0.2
) -> Peak:

    lower_bound = retention_time - tolerance
    upper_bound = retention_time + tolerance

    peaks_in_interval = []
    retention_times = []
    for peak in peaks:
        retention_times.append(peak.retention_time)

    nearest_peak_id = _get_nearest_peak(retention_times, retention_time)

    if lower_bound <= peaks[nearest_peak_id].retention_time <= upper_bound:
        peaks_in_interval.append(peaks[nearest_peak_id])

    if len(peaks_in_interval) == 1:
        return peak

    elif len(peaks_in_interval) == 0:
        return None

    else:
        raise ValueError("More than one peak found in the interval.")


def visualize_areas(
    hplc_experiment: HPLCExperiment,
    signal_type: SignalType,
    peak_retention_times: Union[float, List[int]],
):

    if isinstance(peak_ids, int):
        peak_ids = [peak_ids]
    peak_ids = [str(peak_id) for peak_id in peak_ids]

    if signal_type not in SignalType.__members__:
        raise TypeError(
            f"signal_type must be one of {[s_type.value for s_type in SignalType]}")

    peak_datas = _get_peak_datas(hplc_experiment, signal_type, peak_ids)

    return peak_datas


def _get_signals_by_type(measurement: Measurement, signal_type: SignalType) -> Signal:
    """Returns a  ```Signal``` objects of the specified type."""

    return [signal for signal in measurement.signals if signal.type == signal_type][0]


def _get_peak_areas_by_ids(
    peaks: List[Peak],
    peak_ids: List[int]
) -> Dict[str, float]:
    """Extracts given peak areas from ```Peak``` objects and 
    returns a specified peaks as a dictionary."""

    peak_areas = {}
    peak_IDS = []
    for peak in peaks:
        peak_IDS.append(peak.id)

        if peak.id in peak_ids:
            peak_areas[peak.id] = peak.area
        else:
            print()
    print(peak_IDS)
    return peak_areas


def _get_peak_datas(
    hplc_experiment: HPLCExperiment,
    signal_type: SignalType,
    peak_ids: Union[int, List[int]],
):

    signals = []
    peak_datas = defaultdict(list)
    for measurement in hplc_experiment.measurements:

        peak_datas["datetime"].append(measurement.timestamp)
        signals.append(_get_signals_by_type(measurement, signal_type))

    assert len(signals) == len(peak_datas["datetime"])

    for signal in signals:

        measurement_areas = _get_peak_areas_by_ids(signal.peaks, peak_ids)
        for peak_id, area in measurement_areas.items():
            peak_datas[peak_id].append(area)

    _check_data_constency(peak_datas)

    return peak_datas


def _check_data_constency(dict_of_lists: Dict[str, List[float]]):
    """Checks if all lists in a dictionary have the same length.
    If not, a peak may not be detected in all measurements."""

    vals = list(dict_of_lists.values())
    l = len(vals[0])
    print([len(le) for le in vals])
    if not all(len(item) == l for item in vals):
        raise ValueError("Peak array lengths are inconsistent.")


def _get_nearest_peak(
        retention_times: List[float],
        retention_time: float
) -> int:
    return min(range(len(retention_times)), key=lambda i: abs(retention_times[i]-retention_time))


def _get_spectrum_data(signal: Signal) -> (List[float], List[float]):
    """Returns a tuple of lists of retention times and areas."""

    peak_positions = []
    peak_heights = []
    for peak in signal.peaks:
        heights, positions = _get_peak_triangle(peak)
        peak_heights.extend(heights)
        peak_positions.extend(positions)

    return (peak_positions, peak_heights)


def _get_peak_triangle(peak: Peak) -> (List[float], List[float]):
    """Returns a tuple of lists of retention times and areas."""

    position = peak.retention_time
    width = peak.width
    peak_x = [position - width/2, position, position + width/2]
    peak_y = [0, peak.height, 0]

    return (peak_x, peak_y)


def visualize_measurements(hplc_experiment: HPLCExperiment, detector: SignalType = "fid"):

    df = _get_dataframe(hplc_experiment)

    df = df[df['signal_type'] == detector]

    fig = px.scatter(
        x=df["timestamp"],
        y=df["retention_time"],
        color=np.log(df["area"]),
        labels=dict(
            x="time of HPLC run",
            y="retention time / min",
            color="log(peak area)"
        ),
        title=f"{detector} detector data",
    )

    return fig


def visualize_by_retention_times(
    hplc_experiment: HPLCExperiment,
    retention_times: List[float],
    tolerance: float = 0.1,
    detector: SignalType = "fid",
) -> List[Peak]:

    dfs = []
    for retention_time in retention_times:
        dfs.append(subset_by_retention_time(
            hplc_experiment=hplc_experiment,
            retention_time=retention_time,
            tolerance=tolerance,
            detector=detector,
        )
        )

    fig = go.Figure()

    for df in dfs:
        fig.add_trace(
            go.Scatter(
                x=df["timestamp"],
                y=df["area"],
                mode="markers",
                name=f"retention time: {df['retention_time'].iloc[0]:.2f} min",
            )
        )

    fig.update_layout(
        title=f"{detector} detector data",
        yaxis_title="peak area / a.u.",
        xaxis_title="time of measurement",
    )

    return fig
