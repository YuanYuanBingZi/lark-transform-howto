"""Reshaping the concrete syntax or parse tree of a sequence of sums
into the desired abstract syntax tree.

Alternative version to go with sums_alt.lark
"""

import sums_ast
import lark

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

class SumsTransformer(lark.Transformer):
    """We write a transformer for each node in the parse tree
    (concrete syntax) by writing a method with the same name.
    Non-terminal symbols are passed a list of their children
    after transformation, which proceeds from leaves to root
    recursively. Terminal symbols (like NUMBER) are instead
    passed a lark.Token structure.
    """

    def NUMBER(self, data):
        """Terminal symbol, a regular expression in the grammar"""
        log.debug(f"Processing token NUMBER with {data}")
        val = int(data.value)
        ast_node = sums_ast.Number(val)
        log.debug(f"Processed token into value {ast_node}")
        return ast_node

    # By defining _number instead of number, we "inlined" these nodes
    # in "sum", which will now include the results of processing NUMBER instead.
    #
    # def number(self, children):
    #     """number, unlike NUMBER, is a non-terminal symbol.
    #     It has a single child, which will have been transformed
    #     by the NUMBER method above.
    #     """
    #     log.debug(f"Processing 'number' with {children}")
    #     return children[0]


    def sum(self, children):
        """The "!" in the grammar preserves the "+" and "-".  Since we are no longer
        relabeling the nodes to "plus" and "minus", we must look at the length of
        children to distinguish base case from recursive case.
        """
        log.debug(f"Processing sum with {children}")
        if len(children) == 1:
            return children[0]
        else:
            assert len(children) == 3, "Recursive cases of 'sum' have three parts including operation"
            left, op, right = children
            # The literal string will be represented by a Token object
            if op.value == "+":
                return sums_ast.Plus(left, right)
            elif op.value == "-":
                return sums_ast.Minus(left, right)
            else:
                raise ValueError(f"Bad token {op}")


    def seq(self, children):
        """Since we used the extended syntax for + or *, the children
        will be a list, and the length of the list will be the number of
        matched components.
        """
        log.debug(f"Processing sequence with {children}")
        seq = sums_ast.Seq()
        for child in children:
            seq.append(child)
        return seq





