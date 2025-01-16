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
    cell_id = 0

    def __init__(self, border, width, _, layer=1, reduction=0, cell_name="QR", library=None, gdsii_box_size=None, id_provider=None, **kwargs):
        self.bg: gdspy.Polygon = None
        self.library = library
            # raise ValueError("GDSII library must be provided as a keyword argument")
        self.cell_name = cell_name
        self.layer = layer
        self.negate = None
        self.reduction = reduction
        self.result = None
        if id_provider is None:
            GDSIIFactory.cell_id += 1
            self.id = GDSIIFactory.cell_id
        else:
            self.id = id_provider()


        # qrcode prevents decimal box sizes: hence this little workaround
        if gdsii_box_size is None:
            raise ValueError("Please specify a gdsii box size as a keyword argument")
        self.box_size = gdsii_box_size


        super().__init__(border, width, gdsii_box_size, **kwargs)


    def new_image(self):
        self.negate = []
        c = gdspy.Cell(self.cell_name + f"_{self.id}")
        #self.library.add(c, True)
        return c

    def init_new_image(self):
        # Fill the image with black
        self.bg = gdspy.Rectangle((self.border, self.border),
                        (self.width * self.box_size, self.width * self.box_size),
                                layer=self.layer or 1)

    def process(self):
        negate = gdspy.PolygonSet(self.negate, layer=self.layer)
        polyset = gdspy.boolean(self.bg, negate, "not", layer=self.layer or 1)
        processed_code = gdspy.boolean(polyset, None, "or", layer=self.layer or 1)
        # if self.library is not None:
        #     c = self.library.new_cell(self.cell_name+f"_{self.id}"+"_final")
        #     c.add(processed_code)
        #main_cell = gdspy.Cell(self.cell_name+f"_{self.id}"+"_final")
        self._img.add(processed_code)
        return processed_code

    def save(self, stream, kind=None):
        self.check_kind(kind)
        gdspy.write_gds(stream)

    def pixel_box(self, row, col):
        """
        A helper method for pixel-based image generators that specifies the
        four pixel coordinates for a single rect.
        """
        x = (col + self.border) * self.box_size + self.reduction
        y = (row + self.border) * self.box_size + self.reduction
        return (
            (x + self.reduction, y + self.reduction),
            (x + self.box_size + self.reduction, y + self.box_size + self.reduction),
        )

    def pixel_coords(self, row, col):
        x = (col + self.border) * self.box_size - self.reduction
        y = (row + self.border) * self.box_size - self.reduction
        return (
            (x - self.reduction, y - self.reduction),
            (x - self.reduction, y + self.box_size + self.reduction),
            (x + self.box_size + self.reduction, y + self.box_size + self.reduction),
            (x + self.box_size + self.reduction, y-self.reduction),
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
            self.negate.append(self.pixel_coords(row, col))
            #self.negate.append(gdspy.Rectangle(*self.pixel_box(row, col), layer = self.layer or None))