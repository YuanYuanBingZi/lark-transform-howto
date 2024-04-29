"""Abstract syntax representation of a sequence of sums."""

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

class ASTNode:
    """Abstract base class for abstract sequence of sequence of sums"""
    def __init__(self):
        """This is an abstract class and should not be instantiated"""
        this_class = self.__class__.__name__
        if this_class == "ASTNode":
            raise NotImplementedError("ASTNode is an abstract class and should not be instantiated")
        else:
            raise NotImplementedError(f"{this_class} is missing a constructor method")

class Expr(ASTNode):
    """ Represents an expression, which could be a simple term or a series of additions/subtractions of terms. """
    pass

class Term(Expr):
    """ Represents a term, which could be a simple factor or a series of multiplications/divisions of factors. """
    pass

# A sum is either an integer or a binary operation

class Factor(Term):
    """Typically some tokens define leaves of the AST.  Leaves of a Sum
    are integer literals.
    """
    def __init__(self, value: int):
        self.value = value

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return repr(self.value)

class BinOp(Expr):
    """Represents addition or subtraction"""
    def __init__(self, op: str, left: Expr, right: Expr):
        self.op = op
        self.left = left
        self.right = right

    def __str__(self) -> str:
        """Fully parenthesized is easiest"""
        return f"({self.left} {self.op} {self.right})"

    def __repr__(self) -> str:
        clazz = self.__class__.__name__
        return f"{clazz}({repr(self.left)}, {repr(self.right)})"


class Plus(BinOp):
    def __init__(self, left: ASTNode, right: ASTNode):
        super().__init__('+', left, right)

class Minus(BinOp):
    def __init__(self, left: ASTNode, right: ASTNode):
        super().__init__('-', left, right)

class Multiply(BinOp):
    def __init__(self, left: Expr, right: Expr):
        super().__init__('*', left, right)

class Divide(BinOp):
    def __init__(self, left: Expr, right: Expr):
        super().__init__('/', left, right)


class Seq(ASTNode):
    """A sequence of sums.  We could represent it in a treelike manner
    to better match a left-recursive grammar, but we'll instead represent it
    as a list of sums to illustrate how we can apply a lark transformer to
    reshape it.
    """
    def __init__(self):
        self.exprs: list[Expr] = []

    def append(self, expr: Expr):
        self.exprs.append(expr)

    def __str__(self) -> str:
        el_strs = ", ".join(str(e) for e in self.exprs)
        return f"[{el_strs}]"

    def __repr__(self):
        return f"seq({repr(self.exprs)})"

def smoke_test_sums():
    sum1 = Plus(1, Minus(2, 3))
    sum2 = Minus(2, 1)
    seq = Seq()
    seq.append(sum1)
    seq.append(sum2)
    print(seq)
    mul1 = Minus(Plus(1, Multiply(1, 2)), 1)
    mul2 = Divide(Multiply(1, Plus(1, 2)), Plus(1,2))
    seq.append(mul1)
    seq.append(mul2)
    print(seq)

if __name__ == "__main__":
    smoke_test_sums()