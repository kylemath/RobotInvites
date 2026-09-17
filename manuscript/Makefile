all: figures.pdf manuscript.pdf

experiment-results.json experiment-summary.md:
	cd .. && python3 run_experiments.py

figures.pdf: experiment-results.json plot_experiments.py
	python3 plot_experiments.py

manuscript.pdf: figures.pdf manuscript.tex references.bib
	pdflatex manuscript.tex
	bibtex manuscript
	pdflatex manuscript.tex
	pdflatex manuscript.tex

clean:
	rm -f manuscript.aux manuscript.bbl manuscript.blg manuscript.log manuscript.out manuscript.pdf figures.pdf figures.png
