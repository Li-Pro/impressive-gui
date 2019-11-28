<?php include("menu.php"); ?>

<h1>Frequently Asked Questions</h1>

<p class="q">I have a multi-monitor setup and Impressive never comes up on the correct monitor. What can I do?</p>
<p class="a">Unfortunately PyGame, the windowing API currently used by Impressive, does not contain any support for multi-monitor setups whatsoever. This means that you can't really tell Impressive on with monitor it shall run &ndash; at least not directly. Starting from version 0.10.4, Impressive has options that make it possible to use some kind of &raquo;manual&laquo; multi-screen support. In particular, the so-called &raquo;fake fullscreen&laquo; mode (which is basically windowed mode, but without a frame and title bar around the window) is instrumental to this.</p>
<p>Imagine you have a two-monitor setup: The primary monitor is 1600x900, the secondary monitor is 1024x768 and logically located right of the primary one. To run a presentation on the secondary monitor, you can try the following:<code class="pre">
    impressive -ff -g 1024x768+1600+0
</code>This runs Impressive in a borderless window, at the position and size of the second screen.</p>

<p class="q">Is there any kind of &raquo;presenter screen&laquo; in Impressive?</p>
<p class="a">No, and there is currently no proper way (or plans) to implement such a thing. This is due to limitations in PyGame and Impressive's code structure, both of which are hard to overcome.</p>
<p style="margin-bottom:0;">That being said, there is a feature called &raquo;half-screen mode&laquo; (command line option <code>-H</code>) that <em>does</em> implement a presenter screen, but it depends on three factors:</p>
<ul style="margin-top:0;">
<li>The two screens have identical resolutions, and the presenter screen is on the right.</li>
<li>Impresive is run with a large resolution that spans both screens.</li>
<li>The slides already contain the presenter screen's contents on the right side. The only authoring tool (that I know of) capable of doing this is LaTeX's <code>beamer</code> package with the directive<code class="pre">
    \setbeameroption{show notes on second screen=right}
</code>in the header.</li>
<li>The slide contents themselves should have the same or a wider aspect ratio than the screens, otherwise they won't be centered properly.</li>
</ul>

<p class="q">Can I make notes on slides or paint on them?</p>
<p class="a">Unfortunately, no. This is a frequently requested feature that's not trivial to implement, so it will not be added in the foreseeable future.</p>

<p class="q">My presentation contains videos, but Impressive fails to play them. How can I make them work?</p>
<p class="a">You can't. Impressive is not able to extract videos from PDF files, let alone play them in a small window inside the page at the proper position and size. The only way to get video in Impressive is by using the '<code>video</code>' page property, and even then it's important to know that this is an experimental feature that shouldnt't be relied on.</p>

<p class="q">Impressive doesn't run on Windows; it complains that my graphics drivers are too old.</p>
<p class="a">Usually this means that your installed graphics driver doesn't come with OpenGL support, and Windows falls back to its severely outdated software renderer that is missing essential features which are required by Impressive. There are basically two scenarios where this can happen.</p>
<p>If you're sitting in front of a real, physical machine that's running Windows natively, the most likely reason is that no proper graphics driver has been installed. (Recent versions of Windows may install a graphics driver automatically, but it's sometimes a feature-reduced version, lacking OpenGL support, among others.) In this case, install a proper graphics driver from your GPU vendor (<a href="https://www.amd.com/support">AMD</a>, <a href="https://downloadcenter.intel.com/">Intel</a> or <a href="https://www.geforce.com/drivers">nVidia</a>) and Impressive should work fine.</p>
<p>If you're running Windows in a VM or using it via a Remote Desktop connection, there's typically no 3D-accelerated graphics driver available at all, and the only thing you can do is use a more capable software renderer. One such example is Mesa's <code>llvmpipe</code>, for which <a href="https://github.com/pal1000/mesa-dist-win/releases">pre-built Windows binaries</a> exist. You need to download the latest <code>mesa3d-...-release-msvc.7z</code> package, and put the <code>opengl32.dll</code> file from either the <code>x86</code> or <code>x64</code> folder of the archive into the directory where Impressive is installed. If you're using the official Win32 packages of Impressive, the <code>x86</code> version is the correct one for Impressive up to 0.12.x, and the <code>x64</code> one is to be used from 0.13.0 on; if you're running Impressive from source code, the correct version depends on the &raquo;bitness&laquo; of your Python installation. With the proper <code>opengl32.dll</code>, Impressive should work again, although with reduced performance.</p>

</div></body></html>
