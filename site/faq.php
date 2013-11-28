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
<li>The two screen have identical resolutions, and the presenter screen is on the right.</li>
<li>Impresive is run with a large resolution that spans both screens.</li>
<li>The slides already contain the presenter screen's contents on the right side. The only authoring tool (that I know of) capable of doing this is LaTeX's <code>beamer</code> package with the directive<code class="pre">
    \setbeameroption{show notes on second screen=right}
</code>in the header.</li>
<li>The slide contents themselves should have the same or a wider aspect ratio than the screens, otherwise they won't be centered properly.</li>
</ul>

<p class="q">I get a lot of font-related warnings. Is anything wrong?</p>
<p class="a">On Windows, Xpdf seems to print the following two messages for every page rendered:<code class="pre">
    Error: No display font for 'Symbol'
    Error: No display font for 'ZapfDingbats'
</code>As far as I see, there's no problem with that, so you can safely ignore these errors. If there are really missing characters or something like that, you may try GhostScript-based rendering instead. To check if it helps, install GhostScript on your system and use the <code>-P</code> switch to point to the installed <code>gswin32c.exe</code> (Windows) or <code>gs</code> (Unix) executable.</p>

<p class="q">My presentation contains videos, but Impressive fails to play them. How can I make them work?</p>
<p class="a">You can't. Impressive is not able to extract videos from PDF files, let alone play them in a small window inside the page at the proper position and size. The only way to get video in Impressive is by using the '<code>video</code>' page property, and even then it's important to know that this is an experimental feature that shouldnt't be relied on.</p>

</div></body></html>
