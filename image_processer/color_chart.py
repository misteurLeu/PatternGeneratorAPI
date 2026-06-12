"""Define the list of RGBA colors avaible for use"""
from pathlib import Path
import pandas as pd

from input import COLORS_CHARTS, colors_chart_path, COLORS_CHART_HEADER


class ChartNotInChartType(Exception):
    pass


class ColorChart:

    def __init__(self, color_chart_key: str):
        self.color_chart_key = color_chart_key
        self.chart_path = Path(colors_chart_path) / f'{color_chart_key}.csv'
        self.chart = None
        self.color_list = []

    def load_chart(self, force_download: bool = False):
        """Load or Download the main chart and filter it to keep only keys from the selected chart."""

        if self.color_chart_key not in COLORS_CHARTS.keys():
            raise ChartNotInChartType(f"Error chart type {self.color_chart_key} not in ColorChart")

        if force_download or not self.chart_path.exists():
            self._download_chart(self.color_chart_key)

        self.chart = pd.read_csv(
            self.chart_path,
            sep=',',
            encoding='utf-8',
            # names=COLORS_CHART_HEADER
        )
        self.chart.reset_index(drop=True, inplace=True)
        self.color_list = [(int(pix['r']), int(pix['g']), int(pix['b'])) for id, pix in self.chart.iterrows()]


    @staticmethod
    def _download_chart(color_chart_key: str):
        """Download the main chart and filter it to keep only keys from the selected chart."""
        if color_chart_key not in COLORS_CHARTS.keys():
            raise ChartNotInChartType(f"Error chart type {color_chart_key} not in ColorChart")
        chart_keys = [color_chart_key]
        while COLORS_CHARTS[chart_keys[-1]]['parent'] is not None:
            parent_key = COLORS_CHARTS[chart_keys[-1]]['parent']
            chart_keys.append(parent_key)
        try:
            parent_chart = pd.read_csv(
                COLORS_CHARTS[chart_keys[-1]]['path'],
                sep=',',
                encoding='utf-8',
                names=COLORS_CHART_HEADER
            )
        except Exception as e:
            print(f"Error {e} color chart file cannot be retrieve under path {COLORS_CHARTS[color_chart_key]['path']}")
            exit(1)

        for key in chart_keys[::-1]:
            chart = parent_chart[parent_chart['ref'].isin(COLORS_CHARTS[key]['avaible_keys'])] \
                if COLORS_CHARTS[key]['avaible_keys'] is not None else parent_chart

            with open(Path(colors_chart_path) / f'{key}.csv', "w") as f:
                chart.to_csv(f)
