# Newly Add-on by YuanYuanBingZi
This small smaple of Lark has been extended to include operations: plus, minus, multiply and divide.
The new concrete grammer is on -> muls.lark
The new python file of abstract syntax tree is on -> muls_ast.py and muls_reshape.py
The new running and test example is on -> main_muls.py and example_muls.txt


This modification helps me better understand how Lark transfer the language based on the grammar.
I got some errors first as the syntax tree is really weird, "DEBUG:muls_reshape:Processing 'multply' with [Tree(Token('RULE', 'term'), [5]), 3]
3", and I add the term function to the reshape file and fix this bug.

# Parsing and abstract syntax with Lark

Lark is a very nice parser generator with inadequate 
documentation. I've spent far too many hours trying to answer 
questions with the provided Lark documentation, including recipes 
with insufficient explanation and reference with missing details. 
This short _howto_ is an attempt to save you some of those hours.  
It is focused on one particular use case: 

- You want to parse something akin to programming language source 
  code using an LALR(1) parser.
- You want to transform the concrete syntax tree into an abstract 
  syntax tree.

## Getting started

This example uses Lark 1.1.7 installed in a virtual environment (venv).
To get started, assuming you are using Linux or MacOS, use these 
commands in the project directory. 

```shell
python3 -m venv venv
source env/bin/activate
pip install -r requirements.txt
```

The sample files referenced in this document are

- `sums.lark`: A Lark grammar for a semicolon-separated sequence
   of simple arithmetic expressions (sums).  This file includes
   the extended BNF grammar, lexical rules for skipping whitespace
   imported from Lark libraries, and a lexical rule for recognizing
   integer literals. 
- `example_sums.txt`: Example input conforming to the grammar in 
  `sums.lark`. 
- `sums_ast.py`:  Python classes for the abstract syntax tree 
  structure that we wish to obtain by parsing `examples_sums.txt` 
  with `sums.lark`.
- `sums_reshape.py`: A Lark _Transformer_ class that can reshape the 
  concrete syntax tree produced by a Lark parser based on
  `sums.lark` into the abstract syntax described by `sums_ast.py`.
- `main.py`:  Steps in the overall process.
  - builds a Lark parser from `sums.lark`
  - applies that parser to `example_sums.txt` to produce a concrete 
    syntax tree
  - applies the `Transformer` in `sums_reshape.py` to convert the 
    concrete syntax tree into an abstract syntax tree based on 
    `sums_ast.py`.
  - prints a "pretty-printed" version of both the concrete syntax 
    tree and the abstract syntax tree (AST).  The pretty-printed 
    from of the AST looks like a list of fully parenthesized 
    arithmetic expressions. 
- `sums_alt.lark`, `sums_alt_reshape.py`, and `main_alt.py`repeat 
  this process with an alternative version of the grammar (but with 
  the same abstract syntax definition)

## Sketch of the example

To keep the example very, very simple, we will assume we are
parsing a sequence of sums, like this: 

```
5 - (4 - 3); 7 - 2 - 1; 13; 4+7;
```

Such a sequence can be described by a context-free grammar.  We want
`7 - 2 - 1` to be grouped as `(7 - 2) - 1`, so we will write the 
recursive grammar for sums in a left-recursive style: 

```
sum ::= number;
sum ::= sum "+" number;
sum ::= sum "-" number;
```

Lark grammar syntax uses `:` in place of `::=`, and uses indentation 
and line breaks much as Python does to group parts of a production,
so in Lark syntax this could be 

```
sum: number
    | sum "+" number
    | sum "-" number

```
In addition to describing how the non-terminal `sum` can be parsed, 
this rule would describe the possible shapes of a concrete syntax 
tree produced by a Lark parser.  A `sum` node could have a single 
child which is a `number` node, or it could have a left child which 
is another `sum` node and a right child which is a `number` node.  
The literal tokens `+` or `-` would be lost.  There is a way to 
preserve the literal tokens in a Lark parser, but we will use a 
different tactic below, relabeling some of the nodes.

Sequences will also be expressed with left recursion. We'll require 
sequences to include at least one sum: 

```bnf
seq: seq sum ";" 
    | sum ";"    

```

Lark's extended BNF would also let us use Kleene star (`*`)
to directly express a sequence, but the left-recursive rules will 
suit our purpose here. 

## Designing the abstract syntax 

Ideally,  design of abstract syntax should precede design of the
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

## Alternative Lark grammar constructs

The Lark parser generator supports a number of extensions and 
conveniences that can change the concrete syntax tree.  We have used 
a few of them in ``sums_alt.lark`. 

### Inlining non-terminals

In the first version of the grammer, we used a non-terminal `number` 
which just matched a single terminal symbol (token) `NUMBER`.  In 
`sums_alt.lark` we rename this to `_number`.  The leading underscore 
indicates that we do _not_ want nodes in the concrete syntax tree 
for `number`.  Rather, we want the children of `_number` to be 
"inlined" where it appears on the right-hand side of a grammar rule. 
Thus, where our revised grammar says 
``` 
!sum:  sum "+" _number
    | sum "-" _number
    | _number
```
we will not find `_number` nodes in the concrete syntax for `sum`, 
but will instead find nodes for the token `NUMBER`.  

### Preserving literal tokens

We have also prepended "!" to the definition of `sum`.  This 
preserves the literal tokens for "+" and "-".  With this change, we 
no longer need to rename concrete syntax tree nodes to "plus" and 
"minus" to tell them apart.  With this change and the prior change 
to "_number", our transformation rule in `sums_alt.lark` will look 
like this: 

```python
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
```

### Sequences with "*" or "+"

We initially used a left-recursive rule to match a sequence of sums 
separated by semicolons.  

```
seq: seq sum ";" -> seq_more
    | sum ";"    -> seq_one
```

This left-recursive scheme is an idiom of 
bottom-up (LR) parsing, and is how you would match a sequence with 
many other LALR(1) parser generators including Yacc or Bison for 
C/C++ or CUP for Java.  It was also straightforward to convert it 
into a list when the concrete syntax nodes were labeled `seq_more` 
and `seq_one`.  

As an alternative, Lark supports using Kleene-star (`*`) for a 
sequence of zero or more items or `+` for a sequence of one or more. 
We can rewrite the rule for `seq` this way: 

```
seq: (sum ";")+
```

If we use this approach, the children of the `seq` node in the 
concrete syntax will be a list of nodes returned by our 
trasformation of `sum` nodes.  (Nodes for `";"` will not be included 
because we did not prepend `seq` by `!`.)  Our transformation method 
for `seq` will become: 

```python
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
```

The revised grammar is illustrated in `sums_alt.lark`, with a 
corresponding revised transformer in `sums_alt_reshape.py`.
`main_alt.py` applies the revised grammar and transformer.  Note 
that we did _not_ change the definition of the abstract syntax tree. 
This is important:  You want a well-designed abstract syntax tree 
that is not overly coupled to details of concrete syntax. 

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


