<?php include("menu.php"); ?>

<pre id="notes" style="display:none;">
</pre>

<h1>Frequently Asked Questions</h1>

<p class="q">Why are some symbols rendered incorrectly on some systems?</p>
<p class="a">You're most likely using the GhostScript rendering backend if you encounter this. First of all, try to use Xpdf-based rendering, as this solves a lot of problems. If you're stuck with GhostScript for some reason, note that some versions prior to 8.15 seem to have some serious rendering bugs (like drawing hyphens at the wrong location in some pdfTeX genereted files) or even crashes. To solve this, you should upgrade to a newer GhostScript version. If you can't or don't want to do that, you can also try to find a machine with a decent Xpdf or GhostScript installation an render the PDF into images there using Impressive's <code>-o</code> option.<br />
The Windows version of Impressive already ships with Xpdf 3.02, so you will likely not get any of these problems there.</p>

<p class="q">Impressive shows annoying white stripes in gradients. How can I get rid of them?</p>
<p class="a">This is a common problem with a whole bunch of PDF viewers and results from the way gradients are stored in PDF files: They aren't. In PDF versions prior to 1.5 (I guess), gradients have to be &raquo;simulated&laquo; using a series of rectangular &raquo;strips&laquo; whose colors are interpolated from the gradient start color to the gradient end color. Almost every application produces PDFs that way.</p>
<p>The problem arises if the PDF display application tries to apply fancy anti-aliasing to smooth the edges of text and lines. Usually, this is done by an algorithm called &raquo;multisampling&laquo; that smooths the edges of each object <em>individually</em>. So, if one of the gradient strips ends in the middle of a pixel, the antialiasing would blend that pixel towards white (the page background color). But then, the next strip is rendered, and it (of course) starts in the middle of the very same pixel. So, the renderer blends the strip's color with the color that is already in the buffer &mdash; the one that has already been blended with white! All in all, this worst case scenario results in a stripe that is 25 percent white, which is easily visible and, unfortunately, quite annoying.</p>
<p>There are three possible solutions to this problem: First, don't use gradients at all. (Yes, I <em>am</em> serious.) Second, if you absolutely have to use gradients, try another PDF-producing application to generate the slides. Or third, use the Impressive command line switch &raquo;<code>&ndash;s</code>&laquo; to disable multisampling (GhostScript only) and use supersampling instead. This method simply renders the page un-antialiased, but with double resolution. Afterwards, it scales the resulting oversized image down to screen resolution again. This effectively eliminates the annoying stripes, but degrades overall antialiasing quality a bit, because Xpdf's and GhostScript's 16x multisampling is much more precise than Impressive's simple 4x supersampling. Moreover, it is much slower and uses four times as much memory. So use it with care.</p>

<p class="q">In some PDF files, all text has jagged edges, like antialiasing is absent. How do I force antialiasing?</p>
<p class="a">This is most probably a problem with the rendering backend. I don't have a real solution for that other than trying the alternative renderer (Xpdf if you used GhostScript, or vice-versa). In general, this kind of problems seems to be much more common with GhostScript than it is with Xpdf.<br />
If changing the backend doesn't help either, you may try the aforementioned &raquo;<code>&ndash;s</code>&laquo; option as a last resort.</p>

<p class="q">I get a lot of font-related warnings. Is anything wrong?</p>
<p class="a">On Windows, Xpdf seems to print the following two messages for every page rendered:<br />
<code style="white-space:pre;">    Error: No display font for 'Symbol'
    Error: No display font for 'ZapfDingbats'</code><br />
As far as I see, there's no problem with that, so you can safely ignore these errors. If there are really missing characters or something like that, you may try GhostScript-based rendering instead. To check if it helps, install GhostScript on your system and use the <code>-P</code> switch to point to the installed <code>gswin32c.exe</code> (Windows) or <code>gs</code> (Unix) executable.</p>

<p class="q">I have a multi-monitor setup and Impressive behaves strangely. What can I do?</p>
<p class="a">Unfortunately PyGame, the windowing API currently used by Impressive, does not contain any support for multi-monitor setups whatsoever. This means that you can't really tell Impressive on with monitor it shall run. On Linux, you can try to run it in windowed mode, move the window to the proper monitor and enable fullscreen mode there, but it isn't guaranteed that this works either.</p>
<p>As a corollary to PyGame's inability to support multiple monitors or even multiple windows, it is also <em>not</em> possible to have a presenter screen like OpenOffice or Keynote.</p>

</div></body></html>
