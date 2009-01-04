##### TRANSITIONS ##############################################################

# Each transition is represented by a class derived from impressive.Transition
# The interface consists of only two methods: the __init__ method may perform
# some transition-specific initialization, and render() finally renders a frame
# of the transition, using the global texture identifierst Tcurrent and Tnext.

# Transition itself is an abstract class
class AbstractError(StandardError):
    pass
class Transition:
    def __init__(self):
        pass
    def render(self, t):
        raise AbstractError

# an array containing all possible transition classes
AllTransitions=[]

# a helper function doing the common task of directly blitting a background page
def DrawPageDirect(tex):
    glDisable(GL_BLEND)
    glBindTexture(TextureTarget, tex)
    glColor3d(1, 1, 1)
    DrawFullQuad()

# a helper function that enables alpha blending
def EnableAlphaBlend():
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)


# Crossfade: one of the simplest transition you can think of :)
class Crossfade(Transition):
    """simple crossfade"""
    def render(self,t):
      DrawPageDirect(Tcurrent)
      EnableAlphaBlend()
      glBindTexture(TextureTarget, Tnext)
      glColor4d(1, 1, 1, t)
      DrawFullQuad()
AllTransitions.append(Crossfade)


# Slide: a class of transitions that simply slide the new page in from one side
# after an idea from Joachim B Haga
class Slide(Transition):
    def origin(self, t):
        raise AbstractError
    def render(self, t):
        cx, cy, nx, ny = self.origin(t)
    	glBindTexture(TextureTarget, Tcurrent)
    	DrawQuad(cx, cy, cx+1.0, cy+1.0)
    	glBindTexture(TextureTarget, Tnext)
    	DrawQuad(nx, ny, nx+1.0, ny+1.0)

class SlideLeft(Slide):
    """Slide to the left"""
    def origin(self, t): return (-t, 0.0, 1.0-t, 0.0)
class SlideRight(Slide):
    """Slide to the right"""
    def origin(self, t): return (t, 0.0, t-1.0, 0.0)
class SlideUp(Slide):
    """Slide upwards"""
    def origin(self, t): return (0.0, -t, 0.0, 1.0-t)
class SlideDown(Slide):
    """Slide downwards"""
    def origin(self, t): return (0.0, t, 0.0, t-1.0)
AllTransitions.extend([SlideLeft, SlideRight, SlideUp, SlideDown])


# Squeeze: a class of transitions that squeeze the new page in from one size
class Squeeze(Transition):
    def params(self, t):
        raise AbstractError
    def inv(self): return 0
    def render(self, t):
        cx1, cy1, nx0, ny0 = self.params(t)
        if self.inv():
            t1, t2 = (Tnext, Tcurrent)
        else:
            t1, t2 = (Tcurrent, Tnext)
    	glBindTexture(TextureTarget, t1)
    	DrawQuad(0.0, 0.0, cx1, cy1)
    	glBindTexture(TextureTarget, t2)
    	DrawQuad(nx0, ny0, 1.0, 1.0)
class SqueezeHorizontal(Squeeze):
    def split(self, t): raise AbstractError
    def params(self, t):
        t = self.split(t)
        return (t, 1.0, t, 0.0)
class SqueezeVertical(Squeeze):
    def split(self, t): raise AbstractError
    def params(self, t):
        t = self.split(t)
        return (1.0, t, 0.0, t)

class SqueezeLeft(SqueezeHorizontal):
    """Squeeze to the left"""
    def split(self, t): return 1.0 - t
class SqueezeRight(SqueezeHorizontal):
    """Squeeze to the right"""
    def split(self, t): return t
    def inv(self): return 1
class SqueezeUp(SqueezeVertical):
    """Squeeze upwards"""
    def split(self, t): return 1.0 - t
class SqueezeDown(SqueezeVertical):
    """Squeeze downwards"""
    def split(self, t): return t
    def inv(self): return 1
AllTransitions.extend([SqueezeLeft, SqueezeRight, SqueezeUp, SqueezeDown])


# Wipe: a class of transitions that softly "wipe" the new image over the old
# one along a path specified by a gradient function that maps normalized screen
# coordinates to a number in the range [0.0,1.0]
WipeWidth = 0.25
class Wipe(Transition):
    def grad(self, u, v):
        raise AbstractError
    def afunc(self, g):
        pos = (g - self.Wipe_start) / WipeWidth
        return max(min(pos, 1.0), 0.0)
    def render(self, t):
        DrawPageDirect(Tnext)
        EnableAlphaBlend()
        glBindTexture(TextureTarget, Tcurrent)
        self.Wipe_start = t * (1.0 + WipeWidth) - WipeWidth
        DrawMeshQuad(t, lambda t, u, v: \
                     (u, v, 0.0,  u,v,  1.0, self.afunc(self.grad(u, v))))

class WipeDown(Wipe):
    """wipe downwards"""
    def grad(self, u, v): return v
class WipeUp(Wipe):
    """wipe upwards"""
    def grad(self, u, v): return 1.0 - v
class WipeRight(Wipe):
    """wipe from left to right"""
    def grad(self, u, v): return u
class WipeLeft(Wipe):
    """wipe from right to left"""
    def grad(self, u, v): return 1.0 - u
class WipeDownRight(Wipe):
    """wipe from the upper-left to the lower-right corner"""
    def grad(self, u, v): return 0.5 * (u + v)
class WipeUpLeft(Wipe):
    """wipe from the lower-right to the upper-left corner"""
    def grad(self, u, v): return 1.0 - 0.5 * (u + v)
class WipeCenterOut(Wipe):
    """wipe from the center outwards"""
    def grad(self, u, v):
        u -= 0.5
        v -= 0.5
        return sqrt(u * u * 1.777 + v * v) / 0.833
class WipeCenterIn(Wipe):
    """wipe from the edges inwards"""
    def grad(self, u, v):
        u -= 0.5
        v -= 0.5
        return 1.0 - sqrt(u * u * 1.777 + v * v) / 0.833
AllTransitions.extend([WipeDown, WipeUp, WipeRight, WipeLeft, \
                       WipeDownRight, WipeUpLeft, WipeCenterOut, WipeCenterIn])

class WipeBlobs(Wipe):
    """wipe using nice \"blob\"-like patterns"""
    def __init__(self):
        self.uscale = (5.0 + random.random() * 15.0) * 1.333
        self.vscale =  5.0 + random.random() * 15.0
        self.uofs = random.random() * 6.2
        self.vofs = random.random() * 6.2
    def grad(self,u,v):
        return 0.5 + 0.25 * (cos(self.uofs + u * self.uscale) \
                          +  cos(self.vofs + v * self.vscale))
AllTransitions.append(WipeBlobs)

class PagePeel(Transition):
    """an unrealistic, but nice page peel effect"""
    def render(self,t):
        glDisable(GL_BLEND)
        glBindTexture(TextureTarget, Tnext)
        DrawMeshQuad(t, lambda t, u, v: \
                     (u, v, 0.0,  u, v,  1.0 - 0.5 * (1.0 - u) * (1.0 - t), 1.0))
        EnableAlphaBlend()
        glBindTexture(TextureTarget, Tcurrent)
        DrawMeshQuad(t, lambda t, u, v: \
                     (u * (1.0 - t), 0.5 + (v - 0.5) * (1.0 + u * t) * (1.0 + u * t), 0.0,
                      u, v,  1.0 - u * t * t, 1.0))
AllTransitions.append(PagePeel)

### additional transition by Ronan Le Hy <rlehy@free.fr> ###

class PageTurn(Transition):
    """another page peel effect, slower but more realistic than PagePeel"""
    alpha = 2.
    alpha_square = alpha * alpha
    sqrt_two = sqrt(2.)
    inv_sqrt_two = 1. / sqrt(2.)
    def warp(self, t, u, v):
        # distance from the 2d origin to the folding line
        dpt = PageTurn.sqrt_two * (1.0 - t)
        # distance from the 2d origin to the projection of (u,v) on the folding line
        d = PageTurn.inv_sqrt_two * (u + v)
        dmdpt = d - dpt
        # the smaller rho is, the closer to asymptotes are the x(u) and y(v) curves
        # ie, smaller rho => neater fold
        rho = 0.001
        common_sq = sqrt(4. - 8 * t - 4.*(u+v) + 4.*t*(t + v + u) + (u+v)*(u+v) + 4 * rho) / 2.
        x = 1. - t + 0.5 * (u - v) - common_sq
        y = 1. - t + 0.5 * (v - u) - common_sq
        z = - 0.5 * (PageTurn.alpha * dmdpt + sqrt(PageTurn.alpha_square * dmdpt*dmdpt + 4))
        if dmdpt < 0:
            # part of the sheet still flat on the screen: lit and opaque
            i = 1.0
            alpha = 1.0
        else:
            # part of the sheet in the air, after the fold: shadowed and transparent
            # z goes from -0.8 to -2 approximately
            i = -0.5 * z
            alpha = 0.5 * z + 1.5
            # the corner of the page that you hold between your fingers
            dthumb = 0.6 * u + 1.4 * v - 2 * 0.95
            if dthumb > 0:
                z -= dthumb
                x += dthumb
                y += dthumb
                i = 1.0
                alpha = 1.0
        return (x,y,z, u,v, i, alpha)
    def render(self, t):
        glDisable(GL_BLEND)
        glBindTexture(TextureTarget, Tnext)
        DrawMeshQuad(t,lambda t, u, v: \
                    (u, v, 0.0,  u, v,  1.0 - 0.5 * (1.0 - u) * (1.0 - t), 1.0))
        EnableAlphaBlend()
        glBindTexture(TextureTarget, Tcurrent)
        DrawMeshQuad(t, self.warp)
AllTransitions.append(PageTurn)

##### some additional transitions by Rob Reid <rreid@drao.nrc.ca> #####

class ZoomOutIn(Transition):
    """zooms the current page out, and the next one in."""
    def render(self, t):
        glColor3d(0.0, 0.0, 0.0)
        DrawFullQuad()
        if t < 0.5:
            glBindTexture(TextureTarget, Tcurrent)
            scalfact = 1.0 - 2.0 * t
            DrawMeshQuad(t, lambda t, u, v: (0.5 + scalfact * (u - 0.5), \
                                             0.5 + scalfact * (v - 0.5), 0.0, \
                                             u, v, 1.0, 1.0))
        else:
            glBindTexture(TextureTarget, Tnext)
            scalfact = 2.0 * t - 1.0
            EnableAlphaBlend()
            DrawMeshQuad(t, lambda t, u, v: (0.5 + scalfact * (u - 0.5), \
                                             0.5 + scalfact * (v - 0.5), 0.0, \
                                             u, v, 1.0, 1.0))
AllTransitions.append(ZoomOutIn)

class SpinOutIn(Transition):
    """spins the current page out, and the next one in."""
    def render(self, t):
        glColor3d(0.0, 0.0, 0.0)
        DrawFullQuad()
        if t < 0.5:
            glBindTexture(TextureTarget, Tcurrent)
            scalfact = 1.0 - 2.0 * t
        else:
            glBindTexture(TextureTarget, Tnext)
            scalfact = 2.0 * t - 1.0
        sa = scalfact * sin(16.0 * t)
        ca = scalfact * cos(16.0 * t)
        DrawMeshQuad(t,lambda t, u, v: (0.5 + ca * (u - 0.5) - 0.75 * sa * (v - 0.5),\
                                        0.5 + 1.333 * sa * (u - 0.5) + ca * (v - 0.5),\
                                        0.0, u, v, 1.0, 1.0))
AllTransitions.append(SpinOutIn)

class SpiralOutIn(Transition):
    """flushes the current page away to have the next one overflow"""
    def render(self, t):
        glColor3d(0.0, 0.0, 0.0)
        DrawFullQuad()
        if t < 0.5:
            glBindTexture(TextureTarget,Tcurrent)
            scalfact = 1.0 - 2.0 * t
        else:
          glBindTexture(TextureTarget,Tnext)
          scalfact = 2.0 * t - 1.0
        sa = scalfact * sin(16.0 * t)
        ca = scalfact * cos(16.0 * t)
        DrawMeshQuad(t, lambda t, u, v: (0.5 + sa + ca * (u - 0.5) - 0.75 * sa * (v - 0.5),\
                                         0.5 + ca + 1.333 * sa * (u - 0.5) + ca * (v - 0.5),\
                                         0.0, u, v, 1.0, 1.0))
AllTransitions.append(SpiralOutIn)

# the AvailableTransitions array contains a list of all transition classes that
# can be randomly assigned to pages
AvailableTransitions=[ # from coolest to lamest
    # PagePeel, # deactivated: too intrusive
    WipeBlobs,
    WipeCenterOut,WipeCenterIn,
    WipeDownRight,WipeUpLeft,WipeDown,WipeUp,WipeRight,WipeLeft,
    Crossfade
]
