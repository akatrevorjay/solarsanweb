
#
# Custom serializer field
#

class Color(object):
    """
    A color represented in the RGB colorspace.
    """
    def __init__(self, red, green, blue):
        assert(red >= 0 and green >= 0 and blue >= 0)
        assert(red < 256 and green < 256 and blue < 256)
        self.red, self.green, self.blue = red, green, blue

class ColourField(serializers.WritableField):
    """
    Color objects are serialized into "rgb(#, #, #)" notation.
    """
    def to_native(self, obj):
        return "rgb(%d, %d, %d)" % (obj.red, obj.green, obj.blue)

    def from_native(self, data):
        data = data.strip('rgb(').rstrip(')')
        red, green, blue = [int(col) for col in data.split(',')]
        return Color(red, green, blue)
