"""Simple example: Read a sequence of sums,
parse with Lark to form concrete syntax tree,
transform to form abstract syntax tree.
"""

import lark
import sums_ast
import sums_reshape


def main():
    # Step 1:  Process the grammar to create a parser (and lexer)
    gram_file = open("sums.lark", "r")
    parser = lark.Lark(gram_file)

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
    # Warning:  Lousy exceptions because of the way Lark applies these.
    transformer = sums_reshape.SumsTransformer()
    ast = transformer.transform(concrete)
    print(ast)



# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
