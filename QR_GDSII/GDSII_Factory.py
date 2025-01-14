from typing import overload
from qrcode.image.base import BaseImage
import gdspy

class GDSIIFactory(BaseImage):
    """
    An intermediate image processor that hooks into the qrcode library

    Use .get_image() to return the file
    """

    kind = "GDSII"
    allowed_kinds = ("GDSII",)
    needs_drawrect = True
    needs_context = True
    needs_processing = True

    def __init__(self, border, width, _, layer=1, cell_name="QR", library=None, gdsii_box_size=None, **kwargs):
        if library is None:
            raise ValueError("GDSII library must be provided as a keyword argument")
        self.cell_name = cell_name
        self.layer = layer
        self.negate_cell = None
        self.library = library

        # qrcode prevents decimal box sizes: hence this little workaround
        if gdsii_box_size is None:
            raise ValueError("Please specify a gdsii box size as a keyword argument")
        self.box_size = gdsii_box_size


        super().__init__(border, width, gdsii_box_size, **kwargs)


    def new_image(self):
        self.negate_cell = gdspy.Cell(self.cell_name+"_negate")
        return gdspy.Cell(self.cell_name)

    def init_new_image(self):
        # Fill the image with black
        self._img.add(
            gdspy.Rectangle((self.border, self.border),
                            (self.width * self.box_size, self.width * self.box_size),
                            layer=self.layer or 1)
        )

    def process(self):
        polyset = gdspy.boolean(self._img, self.negate_cell, "not", layer=self.layer or 1)
        c = self.library.new_cell(self.cell_name+"_final")
        c.add(polyset)

    def save(self, stream, kind=None):
        self.check_kind(kind)
        gdspy.write_gds(stream)

    def pixel_box(self, row, col):
        """
        A helper method for pixel-based image generators that specifies the
        four pixel coordinates for a single rect.
        """
        x = (col + self.border) * self.box_size
        y = (row + self.border) * self.box_size
        return (
            (x, y),
            (x + self.box_size, y + self.box_size),
        )

    def drawrect(self, row, col):
        """
        Not Used
        :param row:
        :param col:
        :return:
        """
        pass

    def drawrect_context(self, row, col, qr):
        if not bool(qr.modules[row][col]):
            print(*self.pixel_box(row, col))
            self.negate_cell.add(gdspy.Rectangle(*self.pixel_box(row, col), layer = self.layer or None))