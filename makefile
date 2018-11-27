# $Id$

test:	pyburg.py sample6.brg
		python3 cyburg.py sample6.brg sample6.py

clean::
		rm -f -r __pycache__; rm -f *.pyc; rm -f *.txtc

clobber::	clean
		rm -f parsetab.py parser.out
