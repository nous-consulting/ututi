import doctest
from ututi.tests import UtutiLayer

def test_resize_image():
    """Tests for the image resizing function.

    resize_image scales an image so that it would fit into a specified
    bounding box.

        >>> from PIL import Image
        >>> from ututi.lib.image import resize_image

    For completeness let's check if this works with portrait
    orientation images.

        >>> img = Image.new("RGB", (200, 600))
        >>> result = resize_image(img, 100, 300)
        >>> result.size
        (100, 300)

        >>> result = resize_image(img, 100, 400)
        >>> result.size
        (100, 300)

        >>> result = resize_image(img, 100, 150)
        >>> result.size
        (50, 150)


    When resizing a square image, it will be scaled according to the
    smaller limit.

        >>> img = Image.new("RGB", (100, 100))
        >>> result = resize_image(img, 50, 100)
        >>> result.size
        (50,  50)

    Whether the limit is in x or y.

        >>> result = resize_image(img, 100, 50)
        >>> result.size
        (50,  50)

    The image can even be scaled up.

        >>> result = resize_image(img, 200, 100)
        >>> result.size
        (100, 100)

    When only one limit is given, the image is resized ignoring
    constraints on the skipped axis.

        >>> result = resize_image(img, width=60)
        >>> result.size
        (60, 60)

        >>> result = resize_image(img, height=70)
        >>> result.size
        (70, 70)

    Resizing non-square images is a little bit trickier. Let's see how
    this works with a landscape orientation image.

        >>> img = Image.new("RGB", (600, 200))
        >>> result = resize_image(img, 300, 100)
        >>> result.size
        (300, 100)

        >>> result = resize_image(img, 400, 100)
        >>> result.size
        (300, 100)

        >>> result = resize_image(img, 150, 100)
        >>> result.size
        (150, 50)

    We are capping the dimmensions to 300, so you can't make an image
    that is larger than 300 x 300. This protects us from extremely
    long images:

        >>> img = Image.new("RGB", (1000, 4))
        >>> result = resize_image(img, None, 30)
        >>> result.size
        (300, 1)

    And extremely wide images:

        >>> img = Image.new("RGB", (4, 1000))
        >>> result = resize_image(img, 30)
        >>> result.size
        (1, 300)

    Or just users trying to hack our system by passing very very very
    large dimmensions through URL:

        >>> img = Image.new("RGB", (10, 10))
        >>> result = resize_image(img, 1000000)
        >>> result.size
        (300, 300)

        >>> result = resize_image(img, None, 1000000)
        >>> result.size
        (300, 300)

    If we do not pass any dimmensions we should get the original image
    back:

        >>> img = Image.new("RGB", (45, 60))
        >>> result = resize_image(img, None, None)
        >>> result.size
        (45, 60)

    None, empty string or a string contianing an integer are handled
    as inputs too:

        >>> result = resize_image(img, None, 120)
        >>> result.size
        (90, 120)

        >>> result = resize_image(img, 90, None)
        >>> result.size
        (90, 120)

        >>> result = resize_image(img, '180')
        >>> result.size
        (180, 240)

        >>> result = resize_image(img, None, '180')
        >>> result.size
        (135, 180)

    """

def test_crop_square():
    """Tests for the image squaring function.

    crop_square squares image to a given size by removing some width or height.
    The image may be resized first.

        >>> from PIL import Image
        >>> from ututi.lib.image import crop_square

    It works with portrait images:

        >>> img = Image.new("RGB", (200, 600))
        >>> result = crop_square(img, 300)
        >>> result.size
        (300, 300)

    Landscape images:

        >>> img = Image.new("RGB", (300, 100))
        >>> result = crop_square(img, 200)
        >>> result.size
        (200, 200)

    And squared ones:

        >>> img = Image.new("RGB", (100, 100))
        >>> result = crop_square(img, 50)
        >>> result.size
        (50, 50)

        >>> img = Image.new("RGB", (50, 50))
        >>> result = crop_square(img, 100)
        >>> result.size
        (100, 100)

    """


def test_suite():
    suite = doctest.DocTestSuite(
        optionflags=doctest.ELLIPSIS | doctest.REPORT_UDIFF |
        doctest.NORMALIZE_WHITESPACE)
    suite.layer = UtutiLayer
    return suite

