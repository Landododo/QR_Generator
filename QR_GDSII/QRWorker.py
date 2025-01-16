import multiprocessing
import os

import gdspy, multiprocess
from typing import Callable
# Monkey-patch dill
import multiprocess.pool as pool
from multiprocess import Value, Lock

from coverage.types import AnyCallable

from QR_GDSII.QR_Code_Generator import GDSIIQRGenerator
# Must be top level, all context is provided as params

global_lock = Lock()
shared_counter = Value('i', 0)

def get_id():
    with global_lock:
        shared_counter.value += 1
        return shared_counter.value

def worker_func(x, y, qr_generator, data_format, coord_to_position_func, layer, get_id, kwargs):
    return qr_generator.create_gdsii(data_format(x,y, *coord_to_position_func(x,y)),
                                        layer=layer,
                                        id_provider=get_id,
                                        **kwargs), x, y


def default_data_format(x,y, x_actual, y_actual):
    return f"{x},{y}"

def round_floats(x,y, x_actual, y_actual):
    return f"{round(x,3)},{round(y,3)}"

def default_coord_to_pos_behavior(x,y):
    return x,y

def generate_and_place_batch(qr_generator: GDSIIQRGenerator,
                                gdsii_library: gdspy.library,
                                x_count: int,
                                y_count: int = None,
                                layer=1,
                                coordinate_to_position_func: Callable[[int, int], tuple[float, float]] = default_coord_to_pos_behavior,
                                thread_count = os.cpu_count()//2,
                                data_format: Callable[[float, float, float, float], str] = default_data_format,
                                additional_drawings: AnyCallable = None,
                                **kwargs
                           ):
    """
    :param qr_generator: An instance of GDSIIQRGenerator, initialized with the desired parameters
    :param gdsii_library: A gdsii library (parent file) to place the cell in
    :param x_count: How many QR Codes to generate on the x-axis.
    :param y_count: How many QR Codes to generate on the y-axis. Defaults to the x-axis if not specified.
    :param spacing: the spacing between 2 qr cells (um)
    :param padding: the padding on the outside of the grid of qr codes
    :param layer: Layer to draw GDSII cells on.
        :param coordinate_to_position_func: A function that will take the x and y indexes of the
    qr code, and map it to the position of the __bottom left__ corner of the desired position as
    a tuple of coordinates in micrometers.
    (Reduction is already taken into account)
    :param thread_count: How many worker threads to use. Defaults to have of available threads
    :param data_format: A function to map the x and y coordinates to a payload, encoded by the QR
    code.
    :param qr_size: a float with the size of the qr code
    :param kwargs: Any remaining arguments are directly passed to the create_gdsii method of the qr_generator.
    :param additional_drawings: Function that post-processes additional drawings like text relative to
    each QR code.
    :return:
    """
    parent_cell = gdspy.Cell("QR_Array_Parent")
    if not y_count:
        y_count = x_count
    # Additional parameters are layer and any extra kwargs are inferred as metadata
    # For instance, T is an example instance metadata, or metadata local to the QR code
    # You can add instance metadata to the QR code such as an ID,

    # Parallelize cell generation and placement
    with pool.Pool(min(thread_count, 1)) as p:
        for qr_cell, x, y in p.starmap(worker_func, ((x, y, qr_generator, data_format, coordinate_to_position_func, layer,  get_id, kwargs)
                            for y in range(y_count) for x in range(x_count))):
            bottom_left = coordinate_to_position_func(x, y)
            #final_x = bottom_left[0] + qr_generator.reduction
            #final_y = bottom_left[1] + qr_generator.reduction
            parent_cell.add(gdspy.CellReference(qr_cell, bottom_left))
            if additional_drawings is not None:
                additional_drawings(qr_generator.qr_code_size, x,y, parent_cell, *bottom_left)

    gdsii_library.add(parent_cell)