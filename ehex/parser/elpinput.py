import fileinput
from collections import defaultdict

from tatsu.exceptions import FailedSemantics

from ehex.parser.elpparser import ELPParser
from ehex.utils.logging import get_logger

from .models import auxmodel, elpmodel

logger = get_logger(__name__)

_elpparser = ELPParser()


class ModelBuilder(elpmodel.ELPModelBuilderSemantics):
    def __init__(self, *args, **kws):
        super().__init__(*args, **kws)

    def modal_literal(self, ast, *args, **kws):
        if ast.negation:
            # Normalize modal: not K a -> M not a, not M a -> K not a
            modality = "K" if ast.modality == "M" else "M"
            naf_literal = elpmodel.StandardLiteral(
                negation="not", atom=ast.literal.atom
            )
        else:
            modality = ast.modality
            naf_literal = ast.literal
        modal = elpmodel.ModalLiteral(
            negation=None, modality=modality, literal=naf_literal
        )
        return modal

    def NAME(self, ast, *args, **kws):
        prefix = auxmodel.PREFIX
        if ast.startswith(prefix):
            raise FailedSemantics(
                f'"{prefix}" prefix is reserved for internal use'
            )
        return ast


def read_input(*files):
    if not files:
        logger.info("Reading from <stdin>")
    buffers = defaultdict(list)
    with fileinput.input(files) as infile:
        for line in infile:
            buffers[fileinput.filename()].append(line)
    for name, buf in buffers.items():
        yield name, "".join(buf)


def elpparse(src, name="<src>"):
    # This name may occur in error messages
    return _elpparser.parse(
        src,
        "program",
        filename=name,
        semantics=ModelBuilder(),
    )


def join_elps(elps):
    return elpmodel.Program(
        rules=[rule for elp in elps for rule in elp.rules],
    )


def parse(*elps):
    elps = read_input(*elps)
    return join_elps([elpparse(src, name) for name, src in elps])
