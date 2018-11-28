#!/usr/bin/env python3
import random
import copy


class Evaluator():
    """ Given an expression and a list of variables, evaluates all possible
        results of the expression
    """

    def __init__(self, expression: str, variables: list):
        self.expression = expression
        # Replace the operators with ones that Python recognises so eval works
        self.__expression = self.expression.replace(
            "OR", "or").replace("NOT", "not").replace("AND", "and")
        self.variables = sorted(variables)
        self.lines = []

    def eval(self):
        """ Evaluate the expression
        """
        self.lines = []
        for i in range(2 ** len(self.variables)):
            self.lines.append({})
            for j, var in enumerate(self.variables):
                self.lines[i][var] = 1 if i & (
                    1 << (len(self.variables) - j - 1)) else 0
            globs = copy.deepcopy(self.lines[i])
            globs["__builtins__"] = None
            # TODO: Bad idea, but it works for now -- will change to a parser
            # later, which would also allow grabbing subexpressions
            evaluated = eval(self.__expression, globs)
            self.lines[i][' '] = "{1:^{0:d}}".format(
                len(self.expression), evaluated)

    def __iter__(self):
        self.n = 0
        return self

    def __next__(self):
        if self.n < len(self.lines):
            line = " | ".join(str(val)
                              for _, val in self.lines[self.n].items())
            self.n += 1
            return line
        raise StopIteration


class TruthTable():
    """ Provided with an evaluator, will print the corresponding truth table
        for the expression
    """

    def __init__(self, evaluator: Evaluator):
        self.evaluator = evaluator

    def __str__(self):
        return "{} | {}\n{}\n{}".format(" | ".join(self.evaluator.variables),
                                        self.evaluator.expression,
                                        "-" *
                                        (len(self.evaluator.variables) * 3 +
                                         5 + len(self.evaluator.expression)),
                                        "\n".join(self.evaluator))


class ExpressionBuilder():
    """ Given variables and operators, generates a random boolean expression
    """

    def __init__(self, variables: list, operators: list, paren_count: int = 1):
        assert(len(variables) == len(operators) + 1)

        self.paren_count = paren_count

        self.variables = self.__generate_variables_order(variables)
        self.operators = self.__generate_operator_order(operators)
        self.not_expr = self.__generate_not_subexpression()

        self.parentheses = {}
        self.expression = []

    def __str__(self) -> str:
        return " ".join(self.expression)

    def build(self) -> None:
        """ Build the expression
        """
        self.expression = self.variables[:]

        for i, operator in enumerate(self.operators):
            self.expression.insert(2 * i + 1, operator)

        # Push on the NOT expressions
        self.expression.insert(self.expression.index(self.not_expr[0]), "NOT")
        self.expression.insert(self.expression.index("NOT") + 1, "(")

        self.parentheses = self.__generate_indices_of_variables()

        if self.not_expr[1] == 0:
            # Not has lowest precedence, so place it around the expression
            parens = list(self.parentheses.items())
            position = parens.index(
                (self.not_expr[0], self.parentheses[self.not_expr[0]]))
            if position == len(parens) - 1:
                # For when the NOT is around the last variable in the
                # expression
                self.expression.append(")")
            else:
                right = parens[position + 1][0]
                self.expression.insert(self.parentheses[right] + 1, ")")
        else:
            # Insert the closing parenthesis of the NOT right after the
            # variable
            self.expression.insert(self.expression.index("NOT") + 3, ")")

        for _ in range(self.paren_count):
            self.parentheses = self.__generate_indices_of_variables()
            self.parentheses[self.not_expr[0]] -= 2

            left_paren, right_paren = self.__generate_parentheses_positions(
                self.parentheses)

            self.__insert_parentheses(
                self.parentheses, left_paren, right_paren)

    def __generate_indices_of_variables(self) -> dict:
        """ Generate the variable indices inside the expression
        """
        indices = dict(
            sorted(map(lambda var: (var, self.expression.index(var)),
                       self.variables), key=lambda kv: kv[1]))
        return indices

    def __insert_parentheses(self,
                             parentheses: list,
                             left: str,
                             right: str) -> None:
        """ Insert a set of parentheses into the expression
        """
        if right == self.not_expr[0]:
            # If the right variable is being NOT'ed, then we need to move the
            # position of the right parentheses
            parentheses[right] += 2

        # Make up for the fact that it needs to be after the variable
        parentheses[right] += 1

        if parentheses[left] == 0 and parentheses[right] >= \
                len(self.expression) - 1:
            # Basically, if it's around the entire expression it's useless
            return

        # Insert the right one first so that we don't have to account for the
        # new element
        self.expression.insert(self.parentheses[right], ")")
        self.expression.insert(self.parentheses[left], "(")

    def __generate_parentheses_positions(self, parentheses: dict) -> tuple:
        """ Come up with some positions for parentheses
        """
        left = random.choice(list(parentheses.keys())[:-1])
        parens = list(parentheses.items())
        right = parens[parens.index((left, parentheses[left])) + 1][0]
        return (left, right)

    def __generate_variables_order(self, choices: list) -> list:
        """ Generate a random ordering of the variables
        """
        variables = choices[:]
        random.shuffle(variables)
        return variables

    def __generate_operator_order(self, operators: list):
        """ Generate a random ordering of the operators
        """
        opers = operators[:]
        random.shuffle(opers)
        return opers

    def __generate_not_subexpression(self) -> tuple:
        """ Generate a subexpression of a single NOT around a variable (this
            will depend on precedence)
        """
        not_variable = random.choice(self.variables)
        not_precedence = random.randint(0, 1)

        return (not_variable, not_precedence)


def main() -> None:
    """
    Main entry to the program. Generates the expressions, and prints them.
    """
    for _ in range(10):
        expression = ExpressionBuilder(["A", "B", "C"], ["AND", "OR"], 2)
        expression.build()

        evaluator = Evaluator(str(expression), expression.variables)
        evaluator.eval()

        table = TruthTable(evaluator)
        print(table, "\n")


if __name__ == "__main__":
    main()
