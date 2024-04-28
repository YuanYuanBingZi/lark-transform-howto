"""Reshaping the concrete syntax or parse tree of a sequence of sums
into the desired abstract syntax tree.

Typically I would put this in the AST source file, but have separated it out
for this example so there is no confusion about the parts.
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

    def number(self, children):
        """number, unlike NUMBER, is a non-terminal symbol.
        It has a single child, which will have been transformed
        by the NUMBER method above.
        """
        log.debug(f"Processing 'number' with {children}")
        return children[0]

    def plus(self, children):
        log.debug(f"Processing 'plus' with {children}")
        # Note the token '+' is not one of the children;
        # that's why I told Lark to represent the node as 'plus'
        left, right = children
        return sums_ast.Plus(left, right)

    def minus(self, children):
        log.debug(f"Processing 'minus' with {children}")
        # See 'plus' above.  Same deal.
        left, right = children
        return sums_ast.Minus(left, right)

    def sum(self, children):
        """Note we have renamed the recursive cases to 'plus' and 'minus',
        so this method will be called only for a 'sum' node representing
        the base case, sum -> number.
        """
        log.debug(f"Processing sum base case {children}")
        return children[0]

    def seq_one(self, children):
        """This will always be the first reduction to seq"""
        log.debug(f"Processing sequence (base case) with {children}")
        seq = sums_ast.Seq()
        seq.append(children[0])
        log.debug(f"Sequence is now {seq}")
        return seq

    def seq_more(self, children):
        """This left-recursive production will always be reduced AFTER
        the base case has been reduced.
        """
        log.debug(f"Processing seq (recursive case) with {children}")
        seq, sum = children
        seq.append(sum)
        return seq
