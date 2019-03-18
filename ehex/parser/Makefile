MODULES = asp.py ehex.py model.py

all: $(MODULES)
	
%.py: %.ebnf asp-core.ebnf
	tatsu --generate-parser --outfile $@ $<

model.py: ehex.ebnf asp-core.ebnf
	tatsu --object-model --outfile $@ $<

clean:
	rm -rf $(MODULES)
