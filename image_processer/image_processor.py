from functools import lru_cache
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from basic_colormath import get_delta_e_matrix
from collections import defaultdict

import math
import numpy as np

from input import images_path, image_out_path
from .color_chart import ColorChart


class ImageProcessor:
    def __init__(self, image_name, color_chart_key, max_color, target_size):
        self.path_image_in = Path(images_path) / image_name
        self.image_name = image_name
        for i in range(999999):
            self.image_out_name = f"colored_{self.image_name.split('.')[0]}_{i}.png"
            if not (Path(image_out_path) / self.image_out_name).exists():
                break
        else:
            raise Exception(f'Unable to find an avaible output name for file {self.image_name}')

        self.color_chart = ColorChart(color_chart_key)
        self.image = None
        self.filtered_colors = []
        self.matched_colors_grouped = defaultdict(lambda: {"colors": []})
        self.matched_colors = {}
        self.max_color = max_color
        self.target_size = target_size
        self.interpolation = Image.NEAREST

    def load(self):
        self.color_chart.load_chart()
        with Image.open(self.path_image_in) as img:
            resized = self.resize_image(img)
            self.image = np.array(resized.convert(mode='RGB'))

    def resize_image(self, img: Image.Image) -> Image.Image:
        if isinstance(self.target_size, tuple):
            return img.resize(self.target_size, self.interpolation)
        if isinstance(self.target_size, int):
            w, h = img.size
            if (w >= h and w >= self.target_size) or (w <= h and w < self.target_size):
                h = int(self.target_size * h / w)
                w = self.target_size
            if (h >= w and h >= self.target_size) or (h <= w and h < self.target_size):
                w = int(self.target_size * w / h)
                h = self.target_size
            return img.resize((w, h), self.interpolation)



    def extract_colors(self):
        img_flat = self.image.flat
        print(f"image size {len(img_flat)} {len(img_flat) / 3}")
        flat_image = [
            (int(pix_r), int(pix_g), int(pix_b)) for
            pix_r, pix_g, pix_b in
            zip(img_flat[::3], img_flat[1::3], img_flat[2::3])
        ]
        print(f"pixels generated {len(flat_image)}")
        filtered_colors = set(flat_image)
        size = len(filtered_colors)
        for i, color in enumerate(filtered_colors):
            match_color = self.get_nearest_color_chached(color)
            print(f'converting color {i}/{size}', end='\r', flush=True)
            self.matched_colors_grouped[match_color]['colors'].append(color)
        self.reduce_colors()

    def unwrap_matched_colors(self):
        result = {}
        for color in self.matched_colors_grouped.keys():
            for match_color in self.matched_colors_grouped[color]['colors']:
                result[match_color] = color
        return result

    def reduce_colors(self):
        if self.max_color <= 0:
            return
        colors = list(self.matched_colors_grouped.keys())
        matrixed = get_delta_e_matrix(colors)
        deleted = []
        while len(self.matched_colors_grouped) > self.max_color:
            distance_min = 0
            color1 = (0, 0, 0)
            color2 = (0, 0, 0)
            for i in range(1, len(colors)):
                if i in deleted:
                    continue
                for j in range(i + 1, len(colors)):
                    if j in deleted:
                        continue
                    if matrixed[i, j] < distance_min or distance_min == 0:
                        distance_min = matrixed[i, j]
                        color1 = colors[i]
                        color2 = colors[j]
            to_merge1 = self.matched_colors_grouped.pop(color1)
            to_merge2 = self.matched_colors_grouped.pop(color2)
            merged = to_merge1['colors'] + to_merge2['colors']
            if len(to_merge1['colors']) > len(to_merge2['colors']):
                self.matched_colors_grouped[color1]['colors'] = merged
                deleted.append(colors.index(color2))
            else:
                self.matched_colors_grouped[color2]['colors'] = merged
                deleted.append(colors.index(color1))

    def replace_color(self):
        """Replace the color from image with the nearest in the chart."""
        if len(self.matched_colors) == 0:
            self.extract_colors()
        colors = self.unwrap_matched_colors()

        converted = np.array([[colors[(int(color_in[0]), int(color_in[1]), int(color_in[2]))] for color_in in row] for row in self.image])

        new_im = Image.fromarray(converted.astype('uint8'), 'RGB')
        new_im.save(Path(image_out_path) / self.image_out_name)

    def get_nearest_color(self, color):
        return np.array(self.get_nearest_color_chached(tuple(color)), dtype=np.uint8)

    @lru_cache()
    def get_nearest_color_chached(self, color: tuple):
        """Search for the nearest color in color chart."""
        matrix = get_delta_e_matrix([color], self.color_chart.color_list)
        matrix_lst = list(matrix.flat)
        min_dist = min(matrix_lst)
        index = matrix_lst.index(min_dist)
        return self.get_color_from_index(index)

    def get_color_from_index(self, index: int) -> tuple[int, int, int]:
        return (
            int(self.color_chart.chart.iloc[index]['r']),
            int(self.color_chart.chart.iloc[index]['g']),
            int(self.color_chart.chart.iloc[index]['b'])
        )
