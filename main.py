# No eval function
# No postfix
# No stack/queue
import re
import sys
import operator


class Calc:
    def __init__(self) -> None:

        self.COMMAND_PAT = re.compile(r"^/")
        self.EXIT_PAT = re.compile(r"^/exit$")
        self.HELP_PAT = re.compile(r"^/help$")
        self.FLOAT_PAT = re.compile(r"^/float$")
        self.INT_PAT = re.compile(r"^/int$")
        # pattern includes */ operators that might be helpful in further steps
        self.INVALID_PAT = re.compile(r"""[^.A-Za-z\d+*/ ()-] # latin letters, digits and +*/ ()-                                    
                                    |((\.|\d+|[A-Za-z]+)[ ]+(-?\.|\d+|[A-Za-z]+)) # no operator between numbers or vars
                                    |^[*/] # startswith operator
                                    |[*/]{2,} # more than 2 operators
                                    |\*[ ]*/
                                    |/[ ]*\*
                                    |\.\.
                                    |^\.[ ]
                                    |[ ]\.[ ]
                                    |[ ]\.$  
                                    |[+*/-]$ # endswith operator """, flags=re.VERBOSE)
        # pattern includes floats like 1.5 , .25
        self.NUMBER_PAT = re.compile(r"([+-]*\d+\.?\d*)|([+-]*\d*\.?\d+)")
        self.NUMBER_PAT_CLOSED = re.compile(r"^(([+-]*\d+\.?\d*)|([+-]*\d*\.?\d+))$")
        self.PLUS_MINUS_PAT = re.compile(r"[+-]+")
        self.VALID_VAR_NAME = re.compile(r"[+-]*[A-Za-z]+")
        self.VALID_VAR_NAME_CLOSED = re.compile(r"^ *[A-Za-z]+ *$")
        self.ASSIGNMENT_PAT = re.compile(r"^ *[A-Za-z]+ *= *([A-Za-z]+|([+-]*\d+\.?\d*)|([+-]*\d*\.?\d+))")
        self.BOTH_PAR = re.compile(r"\([\dA-Za-z+*/^. -]+\)")
        self.LEFT_PAR = re.compile(r"\(")
        self.RIGHT_PAR = re.compile(r"\)")
        self.PAR = re.compile(r"[()]")
        self.OPER = re.compile(r"[*/^]")
        self.OPERATORS = {"*": operator.mul, "/": operator.truediv, "^": operator.pow}  # do dodania ^

        self.VARIABLES_BANK = dict()

        self.RESULT_AS_INT = True

    def plus_minus_convert(self, num: str) -> str:
        minus = num.count("-")
        if minus:
            plus = num.count("+")
            balance = minus - plus
            if balance % 2 != 0:
                return self.PLUS_MINUS_PAT.sub("-", num)
        return self.PLUS_MINUS_PAT.sub("", num)

    def float_converter(self, num: str) -> float or str:
        try:
            num = float(num)
        except ValueError as e:
            print(f"Error >> {num} << cannot be converted to float")
            sys.exit(e)
        return num

    def plus_minus_cut_off(self, temp: str) -> tuple[str, str]:
        pluses_minuses = ""
        index = (temp.rfind("+") if temp.rfind("+") >= temp.rfind("-") else temp.rfind("-")) + 1
        if index > 0:
            pluses_minuses += temp[:index]
            temp = temp[index:]
        return pluses_minuses, temp

    def evaluate(self, expression_list: list) -> list:
        """Deals with operations like mul, truediv and pow.
        Add and sub depends on pluses and minuses before numbers.
        Pluses and minuses before numbers become part of numbers during slice_it(expression)
        Add and sub is done within sum(expression_list).
        """
        for oper in self.OPERATORS:
            while oper in expression_list:
                oper_index = expression_list.index(oper)
                l_operand = expression_list[oper_index - 1]
                r_operand = expression_list[oper_index + 1]

                operation = self.OPERATORS.get(oper)(l_operand, r_operand)

                expression_list = expression_list[:oper_index - 1] + [operation] + expression_list[oper_index + 2:]

        expression_list = [sum(expression_list)]
        return expression_list

    def parenthesis(self, expression: str) -> str or bool:
        """If parenthesis are present, the function extracts the expressions inside, slice it, evaluate 
        and then puts the result into expression. Works until no parenthesis are being left.
        """
        while True:
            both = self.BOTH_PAR.search(expression)
            l_par = self.LEFT_PAR.search(expression)
            r_par = self.RIGHT_PAR.search(expression)

            if both:
                temp = both.group()
                result = self.slice_it(temp[1:-1])

                if result == "Unknown variable":
                    return "Unknown variable"

                result = self.evaluate(result)

                expression = expression.replace(temp, str(*result))
                continue

            elif l_par or r_par:
                return "Invalid expression"

            return self.slice_it(expression)

    def slice_it(self, expression: str) -> bool or list:
        """ Transposes expression to a list (or bool if sth goes wrong)
        Pluses and minuses before numbers become part of numbers. Summing is done in the end of main_loop
        Other operators are evaluated by evaluate(expression_list).
        """
        sliced_expression = expression
        expression_list = []

        while sliced_expression:
            num = self.NUMBER_PAT.match(sliced_expression)
            if num:
                temp = num.group()
                temp = self.plus_minus_convert(temp)
                temp = self.float_converter(temp)
                expression_list.append(temp)

                sliced_expression = sliced_expression[num.end():]
                continue

            var = self.VALID_VAR_NAME.match(sliced_expression)
            if var:
                temp = var.group()
                pluses_minuses, temp = self.plus_minus_cut_off(temp)

                temp = self.VARIABLES_BANK.get(temp)
                if not temp:
                    return "Unknown variable"

                temp = self.plus_minus_convert(pluses_minuses + temp)
                temp = self.float_converter(temp)

                expression_list.append(temp)

                sliced_expression = sliced_expression[var.end():]
                continue

            oper = self.OPER.match(sliced_expression)
            if oper:
                temp = oper.group()

                expression_list.append(temp)
                sliced_expression = sliced_expression[oper.end():]
                continue

        return expression_list

    def main_loop(self) -> None:

        while True:
            expression = input()

            if not expression.replace(" ", ""):
                continue

            if self.COMMAND_PAT.match(expression):
                if self.EXIT_PAT.match(expression):
                    print("Bye!")
                    break
                elif self.HELP_PAT.match(expression):
                    print("The program calculates.\nType /float to see the result as a float.\nType /int to go back to default settings")
                    continue
                elif self.FLOAT_PAT.match(expression):
                    self.RESULT_AS_INT = False
                    print("Result as float!")
                    continue
                elif self.INT_PAT.match(expression):
                    self.RESULT_AS_INT = True
                    print("Result as int!")
                    continue
                print("Unknown command")
                continue

            if "=" in expression:
                temp_exp = expression.replace(" ", "").split("=")
                if len(temp_exp) != 2:
                    print("Invalid assignment")
                    continue

                identifier, num_or_var = temp_exp

                num = self.NUMBER_PAT_CLOSED.match(num_or_var)
                var = self.VALID_VAR_NAME_CLOSED.match(num_or_var)

                if not self.VALID_VAR_NAME_CLOSED.match(identifier):
                    print("Invalid identifier")
                    continue

                if not num and not var:
                    print("Invalid assignment")
                    continue

                if num:
                    num = num.group()
                    self.VARIABLES_BANK[identifier] = num
                    continue

                if var:
                    var = var.group()
                    value = self.VARIABLES_BANK.get(var)

                    if value:
                        self.VARIABLES_BANK[identifier] = value
                    else:
                        print("Unknown variable")
                    continue

            var = self.VALID_VAR_NAME_CLOSED.match(expression)
            if var:
                var = self.VARIABLES_BANK.get(var.group().replace(" ", ""))
                print(var if var else "Unknown variable")
                continue

            if self.INVALID_PAT.search(expression):
                print("Invalid expression")
                continue

            # self.INVALID_PAT.search excludes situations when there's no operator between numbers
            expression = expression.replace(" ", "")

            expression_list = self.parenthesis(expression)

            if expression_list == "Unknown variable":
                print("Unknown variable")
                continue
            elif expression_list == "Invalid expression":
                print("Invalid expression - sth wrong with parenthesis")
                continue

            expression_list = self.evaluate(expression_list)

            print(int(sum(expression_list)) if self.RESULT_AS_INT else sum(expression_list))


if __name__ == "__main__":
    calc = Calc()
    calc.main_loop()
  
