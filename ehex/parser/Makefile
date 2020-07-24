MODULES = elpparser.py models/elpmodel.py

all: $(MODULES)

%parser.py: grammars/%.ebnf
	tatsu --generate-parser --outfile $@ \
	      --name $(shell echo $* | tr a-z A-Z) $<

models/%model.py: grammars/%.ebnf
	tatsu --object-model --outfile $@ \
	      --name $(shell echo $* | tr a-z A-Z) $<

grammars/elp.ebnf: grammars/asp.ebnf
	touch $@

grammars/asp.ebnf: grammars/literals.ebnf
	touch $@

grammars/literals.ebnf: grammars/terms.ebnf
	touch $@

clean:
	rm -rf $(MODULES)
