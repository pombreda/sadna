"""
Module containing LEX/YACC parsing code for the Layout-variety language.
"""
import re
from ply import lex, yacc
from dsl.ast import (ASTDict, AST, AtomicWidget, Literal, ContainerAST, ExpressionAST, 
    ArithmeticExpression)
from dsl import arithmetic_variety

reserved = {
    'otherwise': 'OTHERWISE'
}

tokens = (
    'NAME',
    'NUMBER',
    'TEXT',
    'HORIZ',
    'VERT',
    'HORIZ_I',
    'VERT_I',
    'LPAREN',
    'RPAREN',
    'LSQUARE',
    'RSQUARE',
    'COMMA',
    'PLUS',
    'MINUS',
    'MULT',
    'DIV',
    'INIT',
    'EQUALS',
    'NOT',
    'AND',
    'OR',
    'LCURLY',
    'RCURLY',
    'THEN',
    'ARROW',
    'CROSS',
    'COLON',
    'THRU',
    'QMARK',
) + tuple(reserved.values())

t_HORIZ   = r'\|'
t_VERT    = r'---+'
t_HORIZ_I = r'\*\|\*'
t_VERT_I  = r'\*---+\*'
t_LPAREN  = r'\('
t_RPAREN  = r'\)'
t_LSQUARE = r'\['
t_RSQUARE = r'\]'
t_COMMA   = r','
t_PLUS    = r'\+'
t_MINUS   = r'-'
t_MULT    = r'\*'
t_DIV     = r'/'
t_INIT    = r'=\?'
t_EQUALS  = r'='
t_NOT     = r'!'
t_AND     = r'&&'
t_OR      = r'\|\|'
t_LCURLY  = r'\{'
t_RCURLY  = r'\}'
t_THEN    = r'=>'
t_ARROW   = r'<-'
t_CROSS   = r'x'
t_THRU    = r'\.\.'
t_COLON   = r':'
t_QMARK   = r'\?'
t_ignore  = ' \t'

tt_NAME = r'[a-zA-Z_][a-zA-Z0-9_]*'
def t_NAME(t):
  r'[a-wy-zA-Z_][a-zA-Z0-9_]*'
  t.type = reserved.get(t.value, 'NAME')
  return t

def t_NUMBER(t):
  r'[0-9]*\.?[0-9]+'
  if "." in t.value:
    t.value = float(t.value)
  else:
    t.value = int(t.value)
  return t

def t_TEXT(t):
  r'("[^"]*")'
  t.value = t.value[1:-1]
  return t

def t_NEWLINE(t):
  r'\n+'
  t.lexer.lineno += t.value.count("\n")

def t_error(t):
  print "Illegal character '%s'" % t.value[0]
  t.lexer.skip(1)

lexer = lex.lex()


#from widgets import atoms
#import expressions


global_variables = {}

sub_programs = {}

precedence = (
    ('left', 'ARROW'),
    ('left', 'VERT'),
    ('left', 'HORIZ'),
    ('left', 'EQUALS'),
    ('left', 'AND', 'OR'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'MULT', 'DIV'),
    ('right', 'NOT'),
)

def p_program(p):
  '''program : program program'''
  p[0] = p[1]
  p[0].update(p[2])

def p_sub_program(p):
  '''program : identifier ARROW composition'''
  p[0] = ASTDict({p[1]: p[3]})
  sub_programs.update(p[0])

def p_composition(p):
  '''composition : LPAREN composition RPAREN
                 | LPAREN composition RPAREN size
                 | LPAREN composition RPAREN parameters
                 | LPAREN composition RPAREN size parameters'''
  p[0] = p[2]
  for modif in p[4:]:
    if isinstance(modif, tuple):  # size -- (width, height)
      p[0].width, p[0].height = modif
    else:  # parameters
      p[0].attributes.update(modif)
  #if len(p) >= 5 and type(p[4]) == tuple:
    #p[0].update_size(*p[4])
  # We can safely ignore parameters here, since they're already evaluated in the
  # parameter rule. (We don't need to store them for farther use...)

def p_composition_from_compositions(p):
  '''composition : composition VERT composition
                 | composition HORIZ composition'''
  desiredDirection = "vertically"
  if re.match("^" + t_HORIZ + "$", p[2]):
    desiredDirection = "horizontally"
  if isinstance(p[1], ContainerAST) and p[1].direction == desiredDirection:
      p[1].subelements.append(p[3])
      p[0] = p[1]
  else:
    p[0] = ContainerAST(desiredDirection, [p[1], p[3]])

def p_composition_iteration(p):
  '''composition : composition iter_token foreach'''
  p[0] = ContainerAST(p[2], [p[1], p[3]])
  
def p_iter_token_vert(p):
  '''iter_token : VERT_I'''
  p[0] = 'vertically*'
  
def p_iter_token_horiz(p):
  '''iter_token : HORIZ_I'''
  p[0] = 'horizontally*'
  
def p_foreach(p):
  '''foreach : NAME EQUALS any_expression THRU any_expression'''
  from_ = to_expression(p[3])
  to_ = to_expression(p[5])
  p[0] = AST('foreach', [p[1], ExpressionAST('..', [from_, to_])])

def p_composition_from_widget(p):
  '''composition : widget'''
  p[0] = p[1]

def create_atom(kind, definitions):
  attributes = {}
  size = ('?', '?')
  for subexpr in definitions:
      if isinstance(subexpr, tuple):
          size = subexpr
      elif isinstance(subexpr, dict):
          attributes = subexpr
  return AtomicWidget(kind, attributes, size)

def p_widget(p):
  '''widget : LPAREN NAME RPAREN
            | LPAREN NAME size RPAREN
            | LPAREN NAME RPAREN parameters
            | LPAREN NAME size RPAREN parameters'''
  p[0] = create_atom(p[2], p[2:])

def p_empty_widget(p):
  '''widget : LPAREN RPAREN
            | LPAREN RPAREN size
            | LPAREN RPAREN parameters
            | LPAREN RPAREN size parameters'''
  p[0] = create_atom("()", p[3:])

def p_size(p):
  '''size : COLON size_part CROSS size_part'''
  p[0] = (p[2], p[4])

def p_size_part_unspecified(p):
  '''size_part : QMARK'''
  p[0] = None
  
def p_size_part(p):
  '''size_part : NUMBER
               | LPAREN expression RPAREN
               | LPAREN conditional RPAREN'''
  if len(p) == 2:
    p[0] = int(p[1])
  else:
    expression = to_expression(p[2])
    if expression is None:
      raise SyntaxError, "Couldn't parse '%s' as a valid expression on line %d." % (p[3], p.lineno(3))
    p[0] = expression

def p_parameters(p):
  '''parameters : LSQUARE paramlist RSQUARE'''
  p[0] = p[2]

def p_paramlist(p):
  '''paramlist : parameter
               | paramlist COMMA parameter'''
  p[0] = p[1]
  if len(p) == 4:
    p[0].update(p[3])

def to_expression(expr):
  "Transform text/expression/condition into Expression type"
  if isinstance(expr, (ExpressionAST, ArithmeticExpression)):
    return expr
  else:
    return ArithmeticExpression(arithmetic_variety.parse_expression(expr))

def p_any_expression(p):
  '''any_expression : expression
                    | boolean_expression
                    | text
                    | conditional'''
  p[0] = p[1]

def p_parameter(p):
  '''parameter : identifier EQUALS expression
               | identifier EQUALS boolean_expression
               | identifier EQUALS conditional
               | identifier INIT LPAREN NUMBER RPAREN'''
  
  if re.match("^" + t_INIT + "$", p[2]):
    p[0] = {p[1]: ExpressionAST('?', [p[4]])}
  else:
      p[0] = {p[1]: to_expression(p[3])}
  return
  
  if re.match("^" + t_INIT + "$", p[2]):
    if p[1] not in global_variables:
      print "Warning: the variable '%s' initialized at line %d is never used" % (p[1], p.lineno(1))
      p[0] = {}
      return
    if global_variables[p[1]].value is not None:
      raise SyntaxError, "Redefinition of variable '%s' at line %d" % (p[1], p.lineno(1))
    global_variables[p[1]].setInitialValue(p[4])
    if type(p[4]) == str:
      global_variables[p[1]].setInitialValue(eval(p[4], {}, {}))
    p[0] = {}
    return
  expression = to_expression(p[3])
  if expression is None:
    raise SyntaxError, "Couldn't parse '%s' as a valid expression on line %d." % (p[3], p.lineno(3))
  p[0] = {p[1]: expression}

def p_parameter_text(p):
  '''parameter : identifier EQUALS text
               | identifier INIT LPAREN text RPAREN'''
    
  if len(p) == 4:
    val = p[3]
  else:
    val = ExpressionAST('?', [p[4]])
  p[0] = {p[1]: val}

def p_text(p):
  '''text : TEXT'''
  p[0] = ExpressionAST('""', [Literal(p[1])])
  
def p_text_expr(p):
  '''text : LPAREN text RPAREN'''
  p[0] = p[2]

def p_boolean_expression(p):
  '''boolean_expression : expression
                        | propositional
                        | comparison'''
  p[0] = to_expression(p[1])

def p_boolean_expression_parens(p):
  '''propositional : LPAREN boolean_expression RPAREN'''
  p[0] = p[2]

def p_boolean_unop(p):
  '''propositional : NOT boolean_expression'''
  p[0] = ExpressionAST(p[1], [p[2]])

def p_boolean_binop(p):
  '''propositional : boolean_expression OR boolean_expression
                   | boolean_expression AND boolean_expression'''
  p[0] = ExpressionAST(p[2], [p[1], p[3]])

def p_boolean_compare(p):
  '''comparison : expression EQUALS expression'''
  p[0] = ExpressionAST(p[2], [to_expression(p[1]), to_expression(p[3])])

def p_conditional(p):
  '''conditional : LCURLY cases RCURLY'''
  if not p[2]:
    raise SyntaxError, "Empty condition bracket on line %d." % p.lineno(1)
  p[0] = ExpressionAST('{?}', p[2])
  

def p_case_condition(p):
  '''condition : expression
               | boolean_expression'''
  p[0] = p[1]

def p_cases(p):
  '''cases : case'''
  p[0] = [p[1]]
  
def p_cases_cons(p):
  '''cases : case COMMA cases'''
  p[0] = [p[1]] + p[3]

def p_case_if(p):
  '''case : LPAREN condition RPAREN THEN LPAREN any_expression RPAREN'''       
  p[0] = ExpressionAST("=>", [to_expression(p[2]), to_expression(p[6])])
    
def p_case_otherwise(p):
  '''case : OTHERWISE LPAREN any_expression RPAREN'''
  p[0] = ExpressionAST('otherwise', [to_expression(p[3])])

def p_expression(p):
  '''expression : identifier
                | NUMBER
                | MINUS expression
                | PLUS expression
                | expression PLUS expression
                | expression MINUS expression
                | expression MULT expression
                | expression DIV expression
                | LPAREN expression RPAREN'''
  p[0] = " ".join(str(x) for x in p[1:])
  # the arithmetic parser will process that later
  # (sacrificing efficiency for modularity)

def p_expression_funcall(p):
  '''expression : NAME LPAREN arglist RPAREN'''
  p[0] = ExpressionAST(p[1], p[3])

def p_expression_index(p):
  '''expression : NAME LSQUARE expression RSQUARE'''
  p[0] = ExpressionAST('[]', [p[1], to_expression(p[3])])

def p_arglist_empty(p):
  '''arglist : '''
  p[0] = []
  
def p_arglist_cons(p):
  '''arglist : expression COMMA arglist'''
  p[0] = [to_expression(p[1])] + p[3]

def p_arglist_single(p):
  '''arglist : expression'''
  p[0] = [to_expression(p[1])]

def p_identifier_name(p):
  '''identifier : NAME'''
  p[0] = p[1]

def p_identifier_x(p):
  '''identifier : CROSS
                | CROSS NUMBER
                | CROSS identifier'''
  p[0] = "".join(map(str, p[1:]))
    

def p_error(p):
  raise SyntaxError, "Syntax error at %s on line %d" % (repr(p.value), p.lineno)

import os.path
here = os.path.dirname(__file__)

parser = yacc.yacc(tabmodule="parser.autogen_layout_parsetab", outputdir=here, debug=0)


def parse(code):
  """Parses the input string as Layout variety language.

  Args:
    code: Code which is valid under the Layout variety specifications.
  Returns:
    Dictionary of windows. Each window is of the Widget type.
    If the first "window" of the code has no assignment into a name, the
    default name "main_window" is assigned to it.
  """
  global sub_programs, global_variables
  sub_programs = {}
  global_variables = {}
  # Check that we have at least one sub_program here. If not, make the only
  # program be "main_window"
  if code.find("<-") == -1 or not re.match(tt_NAME, code.split("<-", 1)[0].strip()):
    code = "main_window <- " + code
  return parser.parse(code.strip(), lexer=lexer)




if __name__ == '__main__':
    test_code = """
    main_window <- (label : 30x30)[a=5+xy9,b={(a) => (f(a)), otherwise (0)}] | 
                   (   (textbox) 
                    --------------
                       ())
    """
    print arithmetic_variety.parse_expression("5*a+9")
    print parse(test_code)
