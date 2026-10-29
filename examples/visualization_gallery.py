"""Export every supported chart using synthetic data; no automatic display."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from nielytics.core.visualization import (
    plot_bar,
    plot_box,
    plot_correlation,
    plot_distribution,
    plot_geographic,
    plot_histogram,
    plot_line,
    plot_scatter,
    plot_seasonal,
    plot_timeseries,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("charts"))
    parser.add_argument("--show", action="store_true", help="Open HTML charts in a browser")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=24, freq="MS"),
        "sample": range(1, 25),
        "value": [4, 6, 8, 5, 3, 7, 9, 12, 8, 6, 5, 2] * 2,
    })
    title = "Synthetic measurements — not climate observations"
    charts = {
        "line": plot_line(frame, "sample", "value", title=title),
        "bar": plot_bar(frame, "sample", "value", title=title),
        "histogram": plot_histogram(frame, "value", bins=8, title=title),
        "box": plot_box(frame, columns=["value"], title=title),
        "scatter": plot_scatter(frame, "sample", "value", title=title),
        "correlation": plot_correlation(frame[["sample", "value"]], title=title),
        "timeseries": plot_timeseries(frame, "date", "value", title=title),
        "distribution": plot_distribution(frame, "value", bins=8, title=title),
        "seasonal": plot_seasonal(frame, "date", "value", title=title),
    }
    for name, figure in charts.items():
        path = args.output_dir / f"{name}.html"
        figure.write_html(path, include_plotlyjs=True, auto_open=args.show)
        print(path.resolve())
    points = pd.DataFrame({"longitude": [76.6, 77.6, 80.3],
                           "latitude": [12.3, 13.0, 13.1], "value": [4., 8., 6.]})
    geographic = plot_geographic(points, value="value", title=title)
    path = args.output_dir / "geographic.png"
    geographic.savefig(path, dpi=150, bbox_inches="tight")
    print(path.resolve())
    geographic.clear()


if __name__ == "__main__":
    main()
