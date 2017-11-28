MODULES = ehex.py model.py answerset.py

all: $(MODULES)
	
%.py: %.ebnf
	tatsu --generate-parser --outfile $@ $<

model.py: ehex.ebnf
	tatsu --object-model --outfile $@ $<

clean:
	rm -rf $(MODULES)
