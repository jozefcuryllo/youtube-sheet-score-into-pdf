from moviepy.editor import *
import numpy as np
from PIL import Image
from fpdf import FPDF
import shutil
import os
import argparse

WIDTH_DPI_72 = 595
HEIGHT_DPI_72 = 842


def remove_background(im: Image) -> Image:
    """
    Remove rows with color darker than args.background [0-255]
    """
    img_array = np.array(im, dtype=np.uint8)

    rows_to_delete = []

    for i, row in enumerate(img_array):
        if np.all(row < args.background):
            rows_to_delete.append(i)

    if rows_to_delete:
        img_array = np.delete(img_array, rows_to_delete, axis=0)

    return Image.fromarray(img_array)


def get_concatenated_image(image1: Image, image2: Image) -> Image:
    """
    Concatenate images
    """
    if not image1:
        return image2

    result = Image.new("RGB", (image1.width, image1.height + image2.height))
    result.paste(image1, (0, 0))
    result.paste(image2, (0, image1.height))
    return result


def get_frames() -> list[Image.Image]:
    """
    Extract unique frames from the video clip
    """
    with VideoFileClip(args.input) as t:
        MIN_DIFF = t.h * t.w * args.diff / 100
        t = t.set_fps(1)
        prev = None
        new_frames = []
        for frame in t.iter_frames():

            if prev is None:
                new_frames.append(frame)
                prev = frame

            diff = np.count_nonzero(frame != prev)
            if diff > MIN_DIFF:
                new_frames.append(frame)
                prev = frame
        return new_frames


def create_pdf(frames: list[Image.Image]):
    """
    Create PDF from images
    """
    full = None
    elements = []
    for frame in frames:
        image = Image.fromarray(frame).convert("L")
        image = remove_background(image)
        image.thumbnail((WIDTH_DPI_72, WIDTH_DPI_72))
        elements.append(image)
        full = get_concatenated_image(full, image)

    pdf = FPDF(unit="pt")
    pdf.add_page()

    height = 0

    try:
        os.mkdir("tmp")
    except FileExistsError:
        pass

    for e in elements:
        e.convert("RGB").save("tmp/part.jpg")

        if height + e.height > HEIGHT_DPI_72:
            pdf.add_page()
            height = 0

        pdf.image("tmp/part.jpg", 0, height, 0, 0)

        height = height + e.height

    pdf.output(args.output)
    shutil.rmtree("tmp")


if __name__ == "__main__":
    argParser = argparse.ArgumentParser()
    argParser.add_argument("input", help="Input path (video clip)")
    argParser.add_argument(
        "-d", "--diff", help="Minimum threshold of difference to distinguish pages [0-100]", default="50", type=int)
    argParser.add_argument(
        "-b", "--background", help="Background color threshold [0-255]", default="100", type=int)
    argParser.add_argument(
        "-o", "--output", help="Output path [PDF only]", default="result.pdf")
    args = argParser.parse_args()

    create_pdf(frames=get_frames())
