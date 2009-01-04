all: man demo

man: site/impressive.html html2man.py
	python html2man.py -O impressive.1 site/impressive.html

demo: demo.pdf

test: demo
	xpdf demo.pdf &

release:
	sh makerelease.sh

%.pdf:	%.tex
	pdflatex $<
	pdflatex $<

clt:	impressive-de.pdf
	sudo cpufreq-set -f 1733000
	./impressive.py -e impressive-de.pdf
	sudo cpufreq-set -f 800000

clean:
	rm -f *.{nav,out,snm,toc,vrb,aux,log,pyc,pyo}

distclean: clean
	rm -f impressive-de.pdf

.PHONY: all man demo test release clt clean distclean
