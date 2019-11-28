##### STOCK SHADERS ############################################################

class SimpleQuad(object):
    "vertex buffer singleton for a simple quad (used by various shaders)"
    vbuf = None
    @classmethod
    def draw(self):
        gl.set_enabled_attribs(0)
        if not self.vbuf:
            self.vbuf = gl.GenBuffers()
            gl.BindBuffer(gl.ARRAY_BUFFER, self.vbuf)
            gl.BufferData(gl.ARRAY_BUFFER, data=[0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 1.0, 1.0])
        else:
            gl.BindBuffer(gl.ARRAY_BUFFER, self.vbuf)
        gl.VertexAttribPointer(0, 2, gl.FLOAT, False, 0, 0)
        gl.DrawArrays(gl.TRIANGLE_STRIP, 0, 4)


class TexturedRectShader(GLShader):
    vs = """
        attribute highp vec2 aPos;
        uniform highp vec4 uPosTransform;
        uniform highp vec4 uScreenTransform;
        uniform highp vec4 uTexTransform;
        varying mediump vec2 vTexCoord;
        void main() {
            highp vec2 pos = uPosTransform.xy + aPos * uPosTransform.zw;
            gl_Position = vec4(uScreenTransform.xy + pos * uScreenTransform.zw, 0.0, 1.0);
            vTexCoord = uTexTransform.xy + aPos * uTexTransform.zw;
        }
    """
    fs = """
        uniform lowp vec4 uColor;
        uniform lowp sampler2D uTex;
        varying mediump vec2 vTexCoord;
        void main() {
            gl_FragColor = uColor * texture2D(uTex, vTexCoord);
        }
    """
    attributes = { 0: 'aPos' }
    uniforms = ['uPosTransform', 'uScreenTransform', 'uTexTransform', 'uColor']

    def draw(self, x0, y0, x1, y1, s0=0.0, t0=0.0, s1=1.0, t1=1.0, tex=None, color=1.0):
        self.use()
        if tex:
            gl.BindTexture(gl.TEXTURE_2D, tex)
        if isinstance(color, float):
            gl.Uniform4f(self.uColor, color, color, color, 1.0)
        else:
            gl.Uniform(self.uColor, color)
        gl.Uniform(self.uPosTransform, x0, y0, x1 - x0, y1 - y0)
        gl.Uniform(self.uScreenTransform, ScreenTransform)
        gl.Uniform(self.uTexTransform, s0, t0, s1 - s0, t1 - t0)
        SimpleQuad.draw()
RequiredShaders.append(TexturedRectShader)


class TexturedMeshShader(GLShader):
    vs = """
        attribute highp vec3 aPosAndAlpha;
        uniform highp vec4 uPosTransform;
        uniform highp vec4 uScreenTransform;
        uniform highp vec4 uTexTransform;
        varying mediump vec2 vTexCoord;
        varying lowp float vAlpha;
        void main() {
            highp vec2 pos = uPosTransform.xy + aPosAndAlpha.xy * uPosTransform.zw;
            gl_Position = vec4(uScreenTransform.xy + pos * uScreenTransform.zw, 0.0, 1.0);
            vTexCoord = uTexTransform.xy + aPosAndAlpha.xy * uTexTransform.zw;
            vAlpha = aPosAndAlpha.z;
        }
    """
    fs = """
        uniform lowp sampler2D uTex;
        varying mediump vec2 vTexCoord;
        varying lowp float vAlpha;
        void main() {
            gl_FragColor = vec4(1.0, 1.0, 1.0, vAlpha) * texture2D(uTex, vTexCoord);
        }
    """
    attributes = { 0: 'aPosAndAlpha' }
    uniforms = ['uPosTransform', 'uScreenTransform', 'uTexTransform']

    def setup(self, x0, y0, x1, y1, s0=0.0, t0=0.0, s1=1.0, t1=1.0, tex=None):
        self.use()
        if tex:
            gl.BindTexture(gl.TEXTURE_2D, tex)
        gl.Uniform(self.uPosTransform, x0, y0, x1 - x0, y1 - y0)
        gl.Uniform(self.uScreenTransform, ScreenTransform)
        gl.Uniform(self.uTexTransform, s0, t0, s1 - s0, t1 - t0)
RequiredShaders.append(TexturedMeshShader)


class BlurShader(GLShader):
    vs = """
        attribute highp vec2 aPos;
        uniform highp vec4 uScreenTransform;
        varying mediump vec2 vTexCoord;
        void main() {
            gl_Position = vec4(uScreenTransform.xy + aPos * uScreenTransform.zw, 0.0, 1.0);
            vTexCoord = aPos;
        }
    """
    fs = """
        uniform lowp float uIntensity;
        uniform mediump sampler2D uTex;
        uniform mediump vec2 uDeltaTexCoord;
        varying mediump vec2 vTexCoord;
        void main() {
            lowp vec3 color = (uIntensity * 0.125) * (
                texture2D(uTex, vTexCoord).rgb * 3.0
              + texture2D(uTex, vTexCoord + uDeltaTexCoord * vec2(+0.89, +0.45)).rgb
              + texture2D(uTex, vTexCoord + uDeltaTexCoord * vec2(+0.71, -0.71)).rgb
              + texture2D(uTex, vTexCoord + uDeltaTexCoord * vec2(-0.45, -0.89)).rgb
              + texture2D(uTex, vTexCoord + uDeltaTexCoord * vec2(-0.99, +0.16)).rgb
              + texture2D(uTex, vTexCoord + uDeltaTexCoord * vec2(-0.16, +0.99)).rgb
            );
            lowp float gray = dot(vec3(0.299, 0.587, 0.114), color);
            gl_FragColor = vec4(mix(color, vec3(gray, gray, gray), uIntensity), 1.0);
        }
    """
    attributes = { 0: 'aPos' }
    uniforms = ['uScreenTransform', 'uDeltaTexCoord', 'uIntensity']

    def draw(self, dtx, dty, intensity=1.0, tex=None):
        self.use()
        if tex:
            gl.BindTexture(gl.TEXTURE_2D, tex)
        gl.Uniform(self.uScreenTransform, ScreenTransform)
        gl.Uniform2f(self.uDeltaTexCoord, dtx, dty)
        gl.Uniform1f(self.uIntensity, intensity)
        SimpleQuad.draw()
# (not added to RequiredShaders because this shader is allowed to fail)


class ProgressBarShader(GLShader):
    vs = """
        attribute highp vec2 aPos;
        uniform highp vec4 uPosTransform;
        varying mediump float vGrad;
        void main() {
            gl_Position = vec4(uPosTransform.xy + aPos * uPosTransform.zw, 0.0, 1.0);
            vGrad = 1.0 - 2.0 * aPos.y;
        }
    """
    fs = """
        uniform lowp vec4 uColor0;
        uniform lowp vec4 uColor1;
        varying mediump float vGrad;
        void main() {
            gl_FragColor = mix(uColor0, uColor1, 1.0 - abs(vGrad));
        }
    """
    attributes = { 0: 'aPos' }
    uniforms = ['uPosTransform', 'uColor0', 'uColor1']

    def draw(self, x0, y0, x1, y1, color0, color1):
        self.use()
        tx0 = ScreenTransform[0] + ScreenTransform[2] * x0
        ty0 = ScreenTransform[1] + ScreenTransform[3] * y0
        tx1 = ScreenTransform[0] + ScreenTransform[2] * x1
        ty1 = ScreenTransform[1] + ScreenTransform[3] * y1
        gl.Uniform4f(self.uPosTransform, tx0, ty0, tx1 - tx0, ty1 - ty0)
        gl.Uniform(self.uColor0, color0)
        gl.Uniform(self.uColor1, color1)
        SimpleQuad.draw()
RequiredShaders.append(ProgressBarShader)
