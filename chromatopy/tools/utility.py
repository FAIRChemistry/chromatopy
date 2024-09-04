import plotly.graph_objects as go

from chromatopy.model import Chromatogram


def _resolve_chromatogram(
    chromatograms: list[Chromatogram], wavelength: float | None
) -> Chromatogram:
    if len(chromatograms) == 1:
        return chromatograms[0]

    if len(chromatograms) > 1:
        assert (
            wavelength is not None
        ), "Multiple chromatograms found, but no wavelength is specified."

        # check that any of the chromatograms has the specified wavelength
        assert any(
            [chrom.wavelength == wavelength for chrom in chromatograms]
        ), f"No chromatogram found with wavelength {wavelength} nm."

        return next(chrom for chrom in chromatograms if chrom.wavelength == wavelength)

    raise ValueError("No chromatogram found.")


def generate_visibility(hover_text: str, fig: go.Figure) -> list[bool]:
    visibility = []
    for trace in fig.data:
        if trace.hovertext == hover_text:
            visibility.append(True)
        else:
            visibility.append(False)
    return visibility
