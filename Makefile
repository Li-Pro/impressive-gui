all: impressive.py man demo

man: impressive.1

impressive.1: site/impressive.html html2man.py
	python html2man.py -O $@ site/impressive.html

demo: demo.pdf

test: demo
	xpdf demo.pdf &

release:
	sh makerelease.sh

%.pdf:	%.tex
	pdflatex -halt-on-error $<
	pdflatex -halt-on-error $<

impressive.py: compile.py impressive_dev.py src/*.py
	python compile.py
	chmod +x $@

clean:
	rm -f *.nav *.out *.snm *.toc *.vrb *.aux *.log *.pyc *.pyo

distclean: clean
	rm -f demo.pdf impressive.1 impressive.py

.PHONY: all man demo test release clean distclean
