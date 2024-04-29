"""Simple example with alternative ways of expressing the grammar in
Lark.
"""

import lark
import sums_ast          # Same as before we changed the grammar
import sums_alt_reshape  # ... but reshaping depends on grammar as well as AST structure


def main():
    # Step 1:  Process the grammar to create a parser (and lexer)
    gram_file = open("sums_alt.lark", "r")
    parser = lark.Lark(gram_file, parser="lalr")

    # Step 2: Use the parser (and lexer) to create a parse tree
    # (concrete syntax)
    src_file = open("example_sums.txt", "r")
    src_text = "".join(src_file.readlines())
    concrete = parser.parse(src_text)
    print("Parse tree (concrete syntax):")
    print(concrete.pretty())

    # Step 3: Transform the concrete syntax tree into
    # an abstract tree, starting from the leaves and working
    # up.
    transformer = sums_alt_reshape.SumsTransformer()
    ast = transformer.transform(concrete)
    print(ast)
    print(f"as {repr(ast)}")

# Warning:  Lousy exceptions when you call 'transform'
#   because of the way Lark applies these.
#   'transform' looks for methods that match the node name, then
#   calls them, so you will get an exception within the Lark code rather
#   than an exception directly associated with your transformation method.


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()
