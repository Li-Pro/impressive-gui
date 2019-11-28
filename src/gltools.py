##### RENDERING TOOL CODE ######################################################

# meshes for highlight boxes and the spotlight are laid out in the same manner:
# - vertex 0 is the center vertex
# - for each slice, there are two further vertices:
#   - vertex 2*i+1 is the "inner" vertex with full alpha
#   - vertex 2*i+2 is the "outer" vertex with zero alpha

class HighlightIndexBuffer(object):
    def __init__(self, npoints, reuse_buf=None, dynamic=False):
        if not reuse_buf:
            self.buf = gl.GenBuffers()
        elif isinstance(reuse_buf, HighlightIndexBuffer):
            self.buf = reuse_buf.buf
        else:
            self.buf = reuse_buf
        data = []
        for i in range(npoints):
            if i:
                b0 = 2 * i - 1
            else:
                b0 = 2 * npoints - 1
            b1 = 2 * i + 1
            data.extend([
                0, b1, b0,
                b1, b1+1, b0,
                b1+1, b0+1, b0
            ])
        self.vertices = 9 * npoints
        if dynamic:
            usage = gl.DYNAMIC_DRAW
        else:
            usage = gl.STATIC_DRAW
        gl.BindBuffer(gl.ELEMENT_ARRAY_BUFFER, self.buf)
        gl.BufferData(gl.ELEMENT_ARRAY_BUFFER, data=data, type=gl.UNSIGNED_SHORT, usage=usage)

    def draw(self):
        gl.BindBuffer(gl.ELEMENT_ARRAY_BUFFER, self.buf)
        gl.DrawElements(gl.TRIANGLES, self.vertices, gl.UNSIGNED_SHORT, 0)


def GenerateSpotMesh():
    global SpotVertices, SpotIndices
    rx0 = SpotRadius * PixelX
    ry0 = SpotRadius * PixelY
    rx1 = (SpotRadius + BoxEdgeSize) * PixelX
    ry1 = (SpotRadius + BoxEdgeSize) * PixelY
    slices = max(MinSpotDetail, int(2.0 * pi * SpotRadius / SpotDetail / ZoomArea))
    SpotIndices = HighlightIndexBuffer(slices, reuse_buf=SpotIndices, dynamic=True)

    vertices = [0.0, 0.0, 1.0]
    for i in range(slices):
        a = i * 2.0 * pi / slices
        vertices.extend([
            rx0 * sin(a), ry0 * cos(a), 1.0,
            rx1 * sin(a), ry1 * cos(a), 0.0
        ])
    if not SpotVertices:
        SpotVertices = gl.GenBuffers()
    gl.BindBuffer(gl.ARRAY_BUFFER, SpotVertices)
    gl.BufferData(gl.ARRAY_BUFFER, data=vertices, usage=gl.DYNAMIC_DRAW)
