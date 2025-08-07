from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import plotly.colors as pc
import plotly.graph_objects as go
import scipy
import scipy.stats
from plotly.express.colors import sample_colorscale

from .utility import generate_gaussian_data

if TYPE_CHECKING:
    from .handler import Handler


def generate_visibility(hover_text: str, fig: go.Figure) -> list[bool]:
    visibility = []
    for trace in fig.data:
        if trace.hovertext == hover_text:
            visibility.append(True)
        else:
            visibility.append(False)
    return visibility


def visualize_all(
    handler: Handler,
    assigned_only: bool = False,
    dark_mode: bool = False,
    show: bool = False,
) -> go.Figure:
    """Plots the fitted peaks of the chromatograms in an interactive figure.


    Args:
        handler (Handler): The Handler instance containing the data.
        assigned_only (bool, optional): If True, only the peaks that are assigned to a molecule are plotted. Defaults to False.
        dark_mode (bool, optional): If True, the figure is displayed in dark mode. Defaults to False.
        show (bool, optional): If True, shows the figure. Defaults to False.

    Returns:
        go.Figure: The plotly figure object.
    """
    if dark_mode:
        theme = "plotly_dark"
        signal_color = "white"
    else:
        theme = "plotly_white"
        signal_color = "black"

    peak_vis_mode = None

    fig = go.Figure()

    for meas in handler.measurements:
        for chrom in meas.chromatograms[:1]:
            # model peaks as gaussians
            if chrom.peaks:
                peaks_exist = True
                if len(chrom.peaks) == 1:
                    color_map = ["teal"]
                else:
                    color_map = sample_colorscale("viridis", len(chrom.peaks))

                for color, peak in zip(color_map, chrom.peaks):
                    if assigned_only and not peak.molecule_id:
                        continue

                    if peak.molecule_id:
                        peak_name = handler.get_molecule(peak.molecule_id).name
                    else:
                        if peak.retention_time is None:
                            raise ValueError("Peak retention time cannot be None")
                        peak_name = f"Peak {peak.retention_time:.2f}"

                    if peak.peak_start and peak.peak_end and peak.width:
                        if peak.amplitude is None or peak.retention_time is None:
                            raise ValueError(
                                "Peak amplitude and retention time must not be None for Gaussian visualization"
                            )
                        x_arr, data = generate_gaussian_data(
                            amplitude=peak.amplitude,
                            center=peak.retention_time,
                            half_height_diameter=peak.width,
                            start=peak.peak_start,
                            end=peak.peak_end,
                        )
                        peak_vis_mode = "gaussian"

                    elif peak.skew and peak.width:
                        if peak.retention_time is None or peak.amplitude is None:
                            raise ValueError(
                                "Peak retention time and amplitude must not be None for skewed visualization"
                            )
                        x_start = peak.retention_time - 3 * peak.width
                        x_end = peak.retention_time + 3 * peak.width
                        x_arr = np.linspace(x_start, x_end, 100).tolist()
                        data = (
                            scipy.stats.skewnorm.pdf(
                                x_arr,
                                peak.skew if peak.skew else 0,
                                loc=peak.retention_time,
                                scale=peak.width,
                            )
                            * peak.amplitude
                        )
                        peak_vis_mode = "skewnorm"

                    elif peak.retention_time and peak.amplitude:
                        interval = 0.03
                        left_shifted = peak.retention_time - interval
                        right_shifted = peak.retention_time + interval
                        x_arr = [
                            left_shifted,
                            right_shifted,
                            right_shifted,
                            left_shifted,
                            left_shifted,
                        ]
                        data = [0, 0, peak.amplitude, peak.amplitude, 0]

                    else:
                        interval = 0.03
                        left_shifted = peak.retention_time - interval
                        right_shifted = peak.retention_time + interval
                        x_arr = [
                            left_shifted,
                            right_shifted,
                            right_shifted,
                            left_shifted,
                            left_shifted,
                        ]
                        data = [0, 0, peak.area, peak.area, 0]

                    custom1 = [round(peak.area)] * len(x_arr)
                    custom2 = [round(peak.retention_time, 2)] * len(x_arr)
                    customdata = np.stack((custom1, custom2), axis=-1)
                    fig.add_trace(
                        go.Scatter(
                            visible=False,
                            x=x_arr,
                            y=data,
                            mode="lines",
                            name=peak_name,
                            customdata=customdata,
                            hovertemplate="<b>Area:</b> %{customdata[0]}<br>"
                            + "<b>Center:</b> %{customdata[1]}<br>"
                            + "<extra></extra>",
                            hovertext=f"{meas.id}",
                            line=dict(
                                color=color,
                                width=1,
                            ),
                            fill="tozeroy",
                            fillcolor=color,
                        )
                    )

            else:
                peaks_exist = False

            if chrom.times and chrom.signals:
                signal_exist = True
                fig.add_trace(
                    go.Scatter(
                        visible=False,
                        x=chrom.times,
                        y=chrom.signals,
                        mode="lines",
                        name="Signal",
                        hovertext=f"{meas.id}",
                        line=dict(
                            color=signal_color,
                            dash="solid",
                            width=1,
                        ),
                    )
                )
            else:
                signal_exist = False

            if chrom.processed_signal and chrom.times:
                processed_signal_exist = True
                fig.add_trace(
                    go.Scatter(
                        visible=False,
                        x=chrom.times,
                        y=chrom.processed_signal,
                        mode="lines",
                        name="Processed Signal",
                        hovertext=f"{meas.id}",
                        line=dict(
                            color="red",
                            dash="dot",
                            width=2,
                        ),
                    )
                )
            else:
                processed_signal_exist = False

    if assigned_only:
        n_peaks_in_first_chrom = len(
            [
                peak
                for peak in handler.measurements[0].chromatograms[0].peaks
                if peak.molecule_id
            ]
        )
    else:
        n_peaks_in_first_chrom = len(handler.measurements[0].chromatograms[0].peaks)

    if peak_vis_mode == "gaussian":
        from loguru import logger

        logger.info(
            "Gaussian peaks are used for visualization, the actual peak shape might differ and is based on the previous peak processing."
        )

    if signal_exist and not processed_signal_exist:
        fig.data[n_peaks_in_first_chrom].visible = True
    elif signal_exist and processed_signal_exist:
        fig.data[n_peaks_in_first_chrom].visible = True
        fig.data[n_peaks_in_first_chrom + 1].visible = True

    if peaks_exist:
        for i in range(n_peaks_in_first_chrom):
            fig.data[i].visible = True

    steps = []
    for meas in handler.measurements:
        for chrom in meas.chromatograms:
            step = {
                "label": f"{meas.id}",
                "method": "update",
                "args": [
                    {
                        "visible": generate_visibility(meas.id, fig),
                    }
                ],
            }
            steps.append(step)

    sliders = [
        {
            "active": 0,
            "currentvalue": {"prefix": "Chromatogram: "},
            "steps": steps,
        }
    ]

    fig.update_layout(
        sliders=sliders,
        xaxis_title="retention time [min]",
        yaxis_title="Intensity",
        template=theme,
    )

    if show:
        fig.show()
    else:
        return fig


def visualize_spectra(handler: Handler, dark_mode: bool = False) -> go.Figure:
    """
    Plots all chromatograms in the Handler in a single plot.

    Args:
        handler (Handler): The Handler instance containing the data.
        dark_mode (bool, optional): If True, the figure is displayed in dark mode. Defaults to False.

    Returns:
        go.Figure: The plotly figure object.
    """

    if dark_mode:
        theme = "plotly_dark"
    else:
        theme = "plotly_white"

    fig = go.Figure()

    color_map = pc.sample_colorscale("viridis", len(handler.measurements))
    for meas, color in zip(handler.measurements, color_map):
        for chrom in meas.chromatograms[:1]:
            fig.add_trace(
                go.Scatter(
                    x=chrom.times,
                    y=chrom.signals,
                    name=meas.id,
                    line=dict(width=2, color=color),
                )
            )

    if chrom.wavelength:
        wave_string = f"({chrom.wavelength} nm)"
    else:
        wave_string = ""

    fig.update_layout(
        xaxis_title="retention time [min]",
        yaxis_title=f"Intensity {wave_string}",
        height=600,
        legend={"traceorder": "normal"},
        template=theme,
    )

    return fig


def visualize(
    handler: Handler,
    n_cols: int = 2,
    figsize: tuple[float, float] = (15, 10),
    show_peaks: bool = True,
    show_processed: bool = False,
    rt_min: float | None = None,
    rt_max: float | None = None,
    save_path: str | None = None,
    assigned_only: bool = False,
    overlay: bool = False,
) -> None:
    """Creates a matplotlib figure with subplots for each measurement.

    Args:
        handler (Handler): The Handler instance containing the data.
        n_cols (int, optional): Number of columns in the subplot grid. Defaults to 2.
        figsize (tuple[float, float], optional): Figure size in inches (width, height). Defaults to (15, 10).
        show_peaks (bool, optional): If True, shows detected peaks. Defaults to True.
        show_processed (bool, optional): If True, shows processed signal. Defaults to False.
        rt_min (float | None, optional): Minimum retention time to display. If None, shows all data. Defaults to None.
        rt_max (float | None, optional): Maximum retention time to display. If None, shows all data. Defaults to None.
        save_path (str | None, optional): Path to save the figure. If None, the figure is not saved. Defaults to None.
        assigned_only (bool, optional): If True, only shows peaks that are assigned to a molecule. Defaults to False.
        overlay (bool, optional): If True, plots all chromatograms on a single axis. Defaults to False.
    """
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.cm import ScalarMappable
    from matplotlib.colors import Normalize

    n_measurements = len(handler.measurements)

    # First pass: collect all y-values to determine global y-range
    y_min = float("inf")
    y_max = float("-inf")
    for meas in handler.measurements:
        for chrom in meas.chromatograms[:1]:
            if chrom.signals:
                y_min = min(y_min, min(chrom.signals))
                y_max = max(y_max, max(chrom.signals))
            if show_processed and chrom.processed_signal:
                y_min = min(y_min, min(chrom.processed_signal))
                y_max = max(y_max, max(chrom.processed_signal))

    # Add some padding to the y-range
    y_range = y_max - y_min
    y_min = y_min - 0.05 * y_range
    y_max = y_max + 0.05 * y_range

    # Collect all retention times for consistent coloring
    all_retention_times = []
    molecule_ids = set()
    for meas in handler.measurements:
        for chrom in meas.chromatograms[:1]:
            if show_peaks and chrom.peaks:
                for peak in chrom.peaks:
                    if peak.retention_time is not None:
                        all_retention_times.append(peak.retention_time)
                        if peak.molecule_id:
                            molecule_ids.add(peak.molecule_id)

    if all_retention_times:
        # Create colormap for retention times
        retention_times = np.array(all_retention_times)
        norm = Normalize(vmin=min(retention_times), vmax=max(retention_times))
        cmap = plt.cm.get_cmap("viridis")
        sm = ScalarMappable(norm=norm, cmap=cmap)

        # Create a colormap for molecules (use a different colormap to distinguish from retention times)
        molecule_colors = {}
        if molecule_ids:
            molecule_list = list(molecule_ids)
            molecule_colors_list = plt.cm.get_cmap("tab10")(
                np.linspace(0, 1, len(molecule_list))
            )
            molecule_colors = {
                mol_id: color
                for mol_id, color in zip(molecule_list, molecule_colors_list)
            }

    if overlay:
        # Create a single figure with one axis
        fig, ax = plt.subplots(figsize=figsize)

        # Generate colors for different measurements
        measurement_colors = plt.cm.get_cmap("tab10")(np.linspace(0, 1, n_measurements))

        # Plot all measurements on the same axis
        for i, meas in enumerate(handler.measurements):
            # Plot signal with measurement-specific color
            for chrom in meas.chromatograms[:1]:
                if chrom.times and chrom.signals:
                    ax.plot(
                        chrom.times,
                        chrom.signals,
                        label=meas.id,
                        color=measurement_colors[i],
                        zorder=2,
                    )

                # Plot processed signal if requested
                if show_processed and chrom.processed_signal and chrom.times:
                    ax.plot(
                        chrom.times,
                        chrom.processed_signal,
                        label=f"{meas.id} (processed)",
                        color=measurement_colors[i],
                        linestyle="--",
                        alpha=0.7,
                        zorder=2,
                    )

            # Plot peaks if requested
            if show_peaks:
                for chrom in meas.chromatograms[:1]:
                    if chrom.peaks:
                        for peak in chrom.peaks:
                            # Skip unassigned peaks if assigned_only is True
                            if assigned_only and not peak.molecule_id:
                                continue

                            if peak.retention_time is not None:
                                # Determine color based on whether peak is assigned to a molecule
                                if (
                                    peak.molecule_id
                                    and peak.molecule_id in molecule_colors
                                ):
                                    # Use molecule-specific color for assigned peaks
                                    color = molecule_colors[peak.molecule_id]
                                else:
                                    # Use retention time color for unassigned peaks
                                    # Round to nearest 0.05 interval for discrete colors
                                    rt_discrete = (
                                        round(peak.retention_time / 0.05) * 0.05
                                    )
                                    color = sm.to_rgba(np.array([rt_discrete]))[0]

                                # Create label for legend
                                if peak.molecule_id:
                                    try:
                                        molecule = handler.get_molecule(
                                            peak.molecule_id
                                        )
                                        label = (
                                            f"{molecule.id} {peak.retention_time:.2f}"
                                        )
                                    except ValueError:
                                        label = f"Peak {peak.retention_time:.2f}"
                                else:
                                    label = f"Peak {peak.retention_time:.2f}"

                                # Plot vertical line with consistent color but measurement-specific linestyle
                                # Use a dashed line with increasing dash length based on measurement index
                                linestyle = (
                                    0,
                                    (1, i + 1),
                                )  # (0, (1, 1)) for first measurement, (0, (1, 2)) for second, etc.

                                ax.axvline(
                                    x=peak.retention_time,
                                    color=color,
                                    linestyle=linestyle,
                                    alpha=0.7,
                                    linewidth=1.5,
                                    label=f"{meas.id}: {label}",
                                    zorder=1,  # Put behind signal
                                )

        # Set plot properties
        ax.set_ylabel("Intensity")
        ax.set_xlabel("Retention time [min]")
        ax.grid(True, alpha=0.3)

        # Add legend with smaller font
        handles, labels = ax.get_legend_handles_labels()
        # Only keep unique entries in the legend
        by_label = dict(zip(labels, handles))
        ax.legend(
            by_label.values(),
            by_label.keys(),
            loc="upper right",
            fontsize=8,
            title="RT [min]",
            title_fontsize=9,
        )

        # Set y-axis limits
        ax.set_ylim(y_min, y_max)

        # Set x-axis limits if specified
        if rt_min is not None and rt_max is not None:
            ax.set_xlim(rt_min, rt_max)

    else:
        # Create figure with multiple subplots for each measurement
        n_rows = int(np.ceil(n_measurements / n_cols))

        # Create figure with shared y-axis
        fig, axes = plt.subplots(
            n_rows, n_cols, figsize=figsize, sharey=True, sharex=True
        )
        if n_measurements == 1:
            axes = np.array([axes])
        axes = axes.flatten()

        # Hide unused subplots
        for i in range(n_measurements, len(axes)):
            axes[i].set_visible(False)

        # Second pass: plot all data with shared y-range
        for idx, (meas, ax) in enumerate(zip(handler.measurements, axes)):
            # Plot peaks first (behind the signal)
            if show_peaks:
                for chrom in meas.chromatograms[:1]:
                    if chrom.peaks:
                        for peak in chrom.peaks:
                            # Skip unassigned peaks if assigned_only is True
                            if assigned_only and not peak.molecule_id:
                                continue

                            if peak.retention_time is not None:
                                # Determine color based on whether peak is assigned to a molecule
                                if (
                                    peak.molecule_id
                                    and peak.molecule_id in molecule_colors
                                ):
                                    # Use molecule-specific color for assigned peaks
                                    color = molecule_colors[peak.molecule_id]
                                else:
                                    # Use retention time color for unassigned peaks
                                    # Round to nearest 0.05 interval for discrete colors
                                    rt_discrete = (
                                        round(peak.retention_time / 0.05) * 0.05
                                    )
                                    color = sm.to_rgba(np.array([rt_discrete]))[0]

                                # Create label for legend
                                if peak.molecule_id:
                                    try:
                                        molecule = handler.get_molecule(
                                            peak.molecule_id
                                        )
                                        label = (
                                            f"{molecule.id} {peak.retention_time:.2f}"
                                        )
                                    except ValueError:
                                        label = f"Peak {peak.retention_time:.2f}"
                                else:
                                    label = f"Peak {peak.retention_time:.2f}"

                                # Plot vertical line with consistent color
                                ax.axvline(
                                    x=peak.retention_time,
                                    color=color,
                                    linestyle="-",
                                    alpha=0.7,
                                    linewidth=2,
                                    label=label,
                                    zorder=1,  # Put behind signal
                                )

            # Plot raw signal
            for chrom in meas.chromatograms[:1]:
                if chrom.times and chrom.signals:
                    ax.plot(
                        chrom.times,
                        chrom.signals,
                        label="Signal",
                        color="black",
                        zorder=2,
                    )

                # Plot processed signal if requested
                if show_processed and chrom.processed_signal and chrom.times:
                    ax.plot(
                        chrom.times,
                        chrom.processed_signal,
                        label="Processed",
                        color="red",
                        linestyle="--",
                        zorder=2,
                    )

            # Remove title and add text annotation in top left corner
            ax.text(
                0.02,
                0.95,
                meas.id,
                transform=ax.transAxes,
                fontsize=10,
                va="top",
                ha="left",
            )

            # Only show x-axis label for plots in the bottom row
            if idx >= n_measurements - n_cols:
                ax.set_xlabel("Retention time [min]")
            else:
                ax.set_xlabel("")

            if idx % n_cols == 0:  # Only show y-label for leftmost plots
                ax.set_ylabel("Intensity")
            ax.grid(True, alpha=0.3)
            ax.legend(loc="upper right", fontsize=8, title="RT [min]", title_fontsize=9)
            ax.set_ylim(y_min, y_max)  # Set consistent y-range for all plots

            # Set x-axis limits if specified
            if rt_min is not None and rt_max is not None:
                ax.set_xlim(rt_min, rt_max)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path)
    else:
        plt.show()
