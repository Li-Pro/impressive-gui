import Image

Height = 32
Width = 64
FileName = "../site/menu_%s.png"

GradStart = 0.875
GradEnd = 0.75

BaseGradient = [GradStart + (y / float(Height - 1)) * (GradEnd - GradStart) for y in xrange(Height)]
def tf(x): return x*x * (3 - 2*x)
TransitionL = [tf((x + 0.5) / Width) for x in xrange(Width)]
TransitionR = TransitionL[:]
TransitionR.reverse()
NoTransition = Width * [1.0]

NormalColor = (1.0, 1.0, 1.0)
ActiveColor = (0.75, 0.75, 1.0)
CurrentColor = (0.85, 0.85, 0.88)

LightenFactor = [0.5**b for b in (1,2,3,4,5,6,7,8)] + [0.0] * (Height - 8)
DarkenFactor = [1.0] * (Height - 8) + [1.0-0.5**b for b in (8,7,6,5,4,3,2,1)]

DitherMatrix = (
    ( 4, 9, 7,11),
    (12, 0,15, 3),
    ( 6,10, 5, 8),
    (14, 2,13, 1),
)

def makeimg(name, color, trans):
    name = FileName % name
    print name
    data = []
    for y in xrange(Height):
        b = BaseGradient[y] * DarkenFactor[y]
        lf = LightenFactor[y]
        ilf = 1.0 - lf
        for x in xrange(len(trans)):
            t = trans[x]
            d = (DitherMatrix[y & 3][x & 3] + 0.5) / 16
            for c in color:
                i = (1.0 - t + t * c) * b
                i = lf + ilf * i
                data.append(chr(max(0, min(255, int(i * 255 + d)))))
    Image.fromstring('RGB', (len(trans), Height), "".join(data)).save(name)

makeimg("n", NormalColor, NoTransition)
makeimg("c_c", CurrentColor, NoTransition)
makeimg("c_l", CurrentColor, TransitionL)
makeimg("c_r", CurrentColor, TransitionR)
makeimg("a_c", ActiveColor, NoTransition)
makeimg("a_l", ActiveColor, TransitionL)
makeimg("a_r", ActiveColor, TransitionR)
