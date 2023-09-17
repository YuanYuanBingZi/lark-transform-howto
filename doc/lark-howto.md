# Parsing and abstract syntax with Lark

Lark is a very nice parser generator with wholly inadequate 
documentation. I've spent far too many hours trying to answer 
questions with the provided Lark documentation, including recipes 
with insufficient explanation and reference with missing details. 
This short _howto_ is an attempt to save you some of those hours.  
It is focused on one particular use case: 

- You want to parse something akin to programming language source 
  code using an LALR(1) parser.
- You want to transform the concrete syntax tree into an abstract 
  syntax tree.

## Sketch of the example

To keep the example very, very simple, we will assume we are
parsing a sequence of sums, like this: 

```
5 - (4 - 3); 7 - 2 - 1; 13; 4+7;
```

Such a sequence can be described by a context-free grammar.  We want
`7 - 2 - 1` to be grouped as `(7 - 2) - 1`, so we will write the 
recursive grammar for sums in a left-recursive style: 

```bnf
sum ::= number;
sum ::= sum '+' number;
sum ::= sum '-' number;
```

(This is not Lark syntax, which we will get to shortly.)

Sequences will also be expressed with left recursion.  For the 
moment we'll require sequences to include at least one sum: 

```bnf
seq ::= sum ';'
seq ::  seq sum ';'
```

We will initially use this left-recursive scheme for a sequence in 
Lark.  Lark's extended BNF will also let us use Kleene star (`*`)
to directly express a sequence, which we will also consider below. 

## Designing the abstract syntax 

Logically design of abstract syntax should precede design of the
grammar.  In practice they are more often interleaved, but we should 
try to make the AST as useful as possible for static analysis and 
intermediate code generation, rather than fitting it closely to the 
concrete syntax.  In this example, I will create an AST class for
a sequence of sums that is represented as a list, although the 
concrete syntax described below will build a tree structure. 

```
class Seq(ASTNode):
    """A sequence of sums.  We could represent it in a treelike manner
    to better match a left-recursive grammar, but we'll instead represent it
    as a list of sums to illustrate how we can apply a lark transformer to
    reshape it.
    """
    def __init__(self):
        self.sums: list[Sum] = []

    def append(self, sum: Sum):
        self.sums.append(sum)
```

The full abstract syntax tree structure is defined in `sums_ast.lark`. 

## Labeling concrete syntax nodes

We will not try to create the abstract syntax directly during parsing,
but we will put handy labels on nodes in the parse tree to make it
easier for us to reshape the tree later.  For example, here is the 
portion of the Lark grammar describing sums in `sums.lark`:

```
sum:  sum "+" number -> plus
    | sum "-" number -> minus
    | number
```

The `"+"` and `"-"` are tokens (terminal symbols) that will not be 
part of the concrete syntax tree produced by Lark.  In lieu of 
having those strings in the tree, we will label those subtrees as 
`plus` and `minus`.  We will make use of these labels when 
transforming the parse tree into abstract syntax.  

We will similarly use node names distinct from the non-terminal name 
`seq` to distinguish between the base case and the recursive case in
parsing a sequence of sums: 

```
seq: seq sum ";" -> seq_more
    | sum ";"    -> seq_one
```

Note that our parse tree will represent a sequence as a tree, while 
our abstract syntax represented it as a linear list.  We'll handle 
the conversion in a Lark `Transformer`. 

## The concrete syntax tree

We create a parser (in `main.py`) from the grammar

```python
    gram_file = open("sums.lark", "r")
    parser = lark.Lark(gram_file)
```

This parser can then be used to create the concrete syntax tree: 

```python
    src_file = open("example_sums.txt", "r")
    src_text = "".join(src_file.readlines())
    parse_tree = parser.parse(src_text)
```

I am using the terms "parse tree" and "concrete syntax tree" almost 
interchangeably, but there are a couple of significant differences. 
Technically the internal nodes of the parse tree are non-terminal 
symbols of the grammar, and leaf nodes are terminal symbols.  The 
tree actually returned by the parser is defined by a Lark data 
structure that is largely isomorphic to the parse tree, but with 
with fields and methods defined by Lark.  Also the tree structure  
produced by our Lark parser will not include literal strings like
";", "+", and "-". 
Most importantly to us, 
where we have specified node names that differ from non-terminals, 
those node names will appear in the concrete syntax tree.  

Consider the expression `2-7 + 5` in `example_sums.txt`. The parse 
tree this expression could be described as
sum(sum(number('2'), '-', number('7'), number('5'))), but with our
labeling of productions in the grammar we will get the concrete 
syntax tree 
plus(minus(number('2'), number('7')), number('5')). It is this 
concrete syntax tree that we will transform into our abstract syntax 
tree. 

## Writing a Transformer

Lark offers three different ways to walk over a concrete syntax 
tree:  visitors, interpreters, and transformers.  A transformer is 
most suitable for converting concrete syntax to abstract syntax. It 
works from the leaves up (or you can think of it working recursively 
depth-first), so at each concrete syntax tree node corresponding to 
a non-terminal symbol in the grammar, we will be given a list of 
children that have already been transformed. 

We create a subclass of `lark.Transformer`, and write a method with 
the same name as each node that we want to transform (which will be 
all of them).

```python
class SumsTransformer(lark.Transformer):
    """We write a transformer for each node in the parse tree
    (concrete syntax) by writing a method with the same name.
    Non-terminal symbols are passed a list of their children
    after transformation, which proceeds from leaves to root
    recursively. Terminal symbols (like NUMBER) are instead
    passed a lark.Token structure.
    """
```

For terminal symbols (other than literals like ';') we write a 
method that is given the node itself.  One of the fields of that 
node is `value`, which contains the text of the token. 

```python
    def NUMBER(self, data):
        """Terminal symbol, a regular expression in the grammar"""
        log.debug(f"Processing token NUMBER with {data}")
        val = int(data.value)
        ast_node = sums_ast.Number(val)
        log.debug(f"Processed token into value {ast_node}")
        return ast_node
```

This method processes text matched by a _lexical_ production in the 
Lark grammar, given as a regular expression: 

``` 
NUMBER: /[0-9]+/
```

For a non-terminal symbol, we similarly write a method with the same 
name.  However, rather than being passed that node of the concrete 
syntax tree, we are passed a list of its children _after 
transformation_.  In our case this means we will be passed a list of 
abstract syntax tree nodes.  Consider the following production rule 
from `sums.lark`: 

```
number: NUMBER
```

Our method `number` will be given a list with just one element, and 
that element will be the result returned by our `NUMBER` method: 

```python
    def number(self, children):
        """number, unlike NUMBER, is a non-terminal symbol.
        It has a single child, which will have been transformed
        by the NUMBER method above.
        """
        log.debug(f"Processing 'number' with {children}")
        return children[0]
```

Note also  that our AST in this case is slightly "shorter" than the 
concrete syntax tree.  We could have omitted the non-terminal symbol 
from our grammar as well by just using the terminal symbol in our 
grammar for `sum`, e.g., 

```
sum:  sum "+" NUMBER -> plus
    | sum "-" NUMBER -> minus
    | NUMBER
```

However, often we will find that one logical "leaf" type in the AST 
can be represented by multiple token patterns, in which case a 
non-terminal like `number` (rather than a token name like `NUMBER`) 
will help organize our grammar. 

Note that whether we make the base case of `sum` be `number` (a 
non-terminal) of `NUMBER` (a terminal symbol, i.e., a token), we 
have not given a label to that production rule.  Thus there will be 
three possible labels for concrete syntax tree nodes representing 
the non-terminal symbol "sum":  "plus", "minus", and "sum".  When we 
see a node labeled "sum", we will know that it corresponds to this 
base case in which a sum is made up of a single number, and process 
it accordingly: 

```python
    def sum(self, children):
        """Note we have renamed the recursive cases to 'plus' and 'minus',
        so this method will be called only for a 'sum' node representing
        the base case, sum -> number.
        """
        log.debug(f"Processing sum base case {children}")
        return children[0]
```
 
## Order of reductions

We noted above that our concrete syntax treats a sequence of sums as 
a tree, while our abstract syntax represents them as a list.  Making 
this transformation requires some understanding of how parsing works.
In particular, you must know that for thes grammar productions: 

``` 
seq: seq sum ";" -> seq_more
    | sum ";"    -> seq_one
```

the base case (`seq_one`) will _always_ occur before the recursive 
case (`seq_more`).  Thus we can transform the tree to a list list this: 

```python
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
```

This ordering was not intuitive to me when I first encountered 
bottom-up parsing, and I have noticed that it seems to puzzle others 
learning to write LALR(1) parsers for the first time.  I promise you,
this is the _only_ way this grammar can be processed, so you can 
depend on it.  In time it will become more natural. 

## Apply the transformation

The sample program `main.py` transforms the concrete syntax tree 
into an abstract syntax tree, and then prints the abstract syntax tree. 

```python
    transformer = sums_reshape.SumsTransformer()
    ast = transformer.transform(concrete)
    print(ast)
```

The input text
```
5 +
3 ;

2-7 + 5 ;
```

is parsed into a concrete syntax tree that Lark's pretty printer 
represents as 

```
seq_more
  seq_one
    plus
      sum
        number	5
      number	3
  plus
    minus
      sum
        number	2
      number	7
    number	5
```

and our transformer converts that into a tree that we can print as a 
list of fully parenthesized expressions: 

```
[(5 + 3), ((2 - 7) + 5)]
```

## Parting advice: Approach AST-building incrementally

Do not be tempted to write a whole programming language grammar, and 
then a whole transformer to concrete syntax, in one or two steps.  
The debugging is too hard, especially when Lark throws exceptions 
that are not easy to trace back to your source code.  That way 
madness lies. 

Instead, build your grammar and test transformations in small 
fragments. Even if you have a full grammar, extract a little bit of 
it, and build a transformer for that bit. If you work bottom-up, you 
can build up parts of your concrete grammar, corresponding parts of 
your abstract syntax, and the transformation together, incrementally.
It is also possible build some fragments top-down (e.g., writing the 
overall scheme for `if` statements before you have defined 
conditional expressions) by using dummy tokens to define 
non-terminals that you have not yet defined.   You can then fit 
pieces together.

As you incrementally build up your parser and transformer, you 
should also be building up example source texts to test them on.  
Keep them simple!  Your primary consideration should be ease of 
debugging, so at least one of your examples should be as simple as 
possible while still exercising the parts of the grammar you are 
working on.

If you get stuck or confused, break it down farther, and simplify 
your examples.  Do not waste hours trying to understand a complex 
tree structure.  Be ruthless in your deconstruction and methodical 
in putting the pieces back together. 


