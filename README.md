# Pyburg (Python BURG)
Welcome to Pyburg documentation. Pyburg is an implementation of IBURG in python with extra functionalities. It is a  code generater generater which produces a python code for assembly language code generation from non control-flow ASTs (Abstract Syntax Trees).

Pyburg is compatible with both Python 2 and Python 3. If you are using Python 2, you have to use Python 2.6 or newer.
## 1.Introduction
Pyburg is a pure-Python implementation of IBURG which is originally impementes in C. IBURG is a AST tree writer which matches an AST with AST grammar incurring minimum cost. Pyburg goes a step further and generates assembly code from instructions specified with AST grammar rules from AST along with minimum cost matching matching of AST with AST grammar.

## 2.Pyburg Overview
Pyburg  consists of four modules `pyburg.py`, `gram.py`, `globals.py` ,`util.py` and `RegAllocator.py` which are found in a Python package called Pyburg.  `pyburg.py` is the core module, `gram.py` is a grammar file for matching code writted in burg file and `RegAllocator.py` takes care of register allocation while generating the assembly language code. `util.py` and `globals.py` are the supportive modules.

`pyburg.py`	 takes a burg file as an input and produces a python file as output which when run again generates assembly code for the AST mentioned in burg file. However, this is entirely up to the user. If desired, `pyburg.py` can also be used for finding out the minimum cover tree match of the AST with tree grammr and it can be used later for manual assembly code generation. 

## 3.burg file specification
Burg file is in a file type with `.brg` file extension.

### 3.1 Terminals specification
The terminals of the AST grammar have to be defined on the first line of the burg file in a purticular format as below. All the terminals should be assigned an unique integer greater than zero which will help later for comparison between the terminals in the generated python code.

Example: ` %term EQUALS=1 PLUS=2 SUB=3 NAME=4 CONST=5`

Here `EQUALS`, `PLUS`, `SUB`, `NAME`, `CONST` are the terminals and 1,2,3,4 5 are the unique integers assigned to them

### 3.2 Tree grammar rule specification
After the terminals are specified, the grammar rules have to be specified in a block enclosed with `%%` lines

Example: 

    %%
    stmt: EQUALS(NAME,reg) {sw $1, $2;} = 1 (1);
    reg: PLUS(reg,reg) {add $$,$1,$2;} = 2 (1);
    reg: SUB(reg,reg) {sub $$,$1,$2;} = 3;
    reg: CONST {} <$1> = 4;
    reg: NAME {lw $$, $1;} = 5;
    %%

The lhs of the first grammar rule will be the start symbol of the grammar and it is generally a stmt (i.e the AST grammar is for a single code statement)

Consider the grammar rule line:

**Each line is a combination of:** 

 1. A grammar rule
 2. Corresponding assembly instructions to be generated when that rule is reduced
 3. unique rule number,
 4. cost incurred when that grammar rule is reduced. This is optional.


Consider the example :

     reg: PLUS(reg,reg) {add $$,$1,$2;} = 2 (1);

 - Here the grammar rule is `reg: PLUS(reg,reg)`  . The lhs of the grammar rule is a non terminal `reg` and rhs is a tree `PLUS(reg,reg)`.  A tree can be a non-terminal or a terminal with arity (number of arguments) >=0. Each argument is again a tree.
 - It is followed by the corresponding assembly instructions to be generated  enclosed in the flower brackets `{}`. Here it is `{add $$,$1,$2;}`. Multiple instructions can be specified inside the `{}` with each instruction ending with a `;`. The number of instructions can be >=0. Each assembly instruction is of the form  `opcode <operand list>`. The operand can be `$$` or `$n` where n is an integer.  `$1, $2,...` represents the non terminals or the terminals  with arity zero in the order from left to right in the rhs. For the above grammar rule, `$1` represents the first `reg` in the rhs and `$2` represents the second `reg`. `$$` corresponds to the lhs of the grammar rule(the return value of the grammar rule).  
 - The  `$$` and `$n` represents a register if the corresponding element of it in grammar rule is a non-terminal. It represents address of the variable if the corresponding element is a `NAME`.
 - In `$n`, n can be negative negative staring from `$-1,$-2,...` which can be used by the user, if he needs an extra register as a temperary register while writing set of instructions for a grammar rule
 - If for any grammar rule, if there is no `$$` in the set of instructions, the user can still specify the return value of the grammar rule as $n. Then $n will be passes as the return value of the grammar rule. Eg.`reg: CONST {} <$1>`. Here `$1` (the value of the CONST) will be passed as the return value of the grammar rule with allocating new register for return value (i.e specifying `$$`)
	

 - After the instructions, the unique rule number is specified with an `=` symbol. For the above rule number is 2.  
 - The cost incurred when the above grammar rule is reduced is specified as 1
 
 ### 3.3 APIs Usage and user written code
After the grammar rules are specified, user can write any code in Python language. The user can  use a list of APIs for labelling the AST, printing the assembly instructions, to print the dump covel of the minimum cost matched ast tree
   The list of APIs available to the user are:
   
 - setEnvironment(registers, variableOffsetFunc)
 - node = initializeNode(ast)
 - node.label()
 - dumpcover(node)
 - printInstructions(node)
 - printBlockInstructions(list of nodes)

User must specify what are the registers available to use while generating the assembly code and also the address locations of the the variables to be used while generating load and store assembly instructions. This can be done by calling the setEnvironment function
`setEnvironment(registers = registers, variableOffsetFunc = getVariableOffset)`

The first argument should be a list of strings specifying the registers available to use. The second argument should be the function (argument can be a function in python :) )  which takes the variable name as the input and returns the offset of the variable in memory in a string format eg. The function takes  variable `"a"` as the input and gives say `"4($sp)"` as the output

initializeNode(ast) takes an AST of a statement  as an input and returns an burg tree node which is later is later matched with the tree grammar to generate assembly code or minimum cost match cover with the AST grammar. 
The input AST may have generated using lex and yacc tools or may be written manually. For pyburg to create the burg tree node from the AST, the input AST tree must contain functions:
 -  getType() which must return terminal number of the root of the tree which is the Terminal number 
 - getValue()  which must return the value of the tree node if it is a leaf node  eg. returns  variable name if the ast tree node is a `NAME `or returns constant value if the ast tree node is a `CONST` 
 - getChildren() returns the list of children which are  also AST tree nodes.

node.label() has to be called on the burg tree node for finding the best grammar rule to use for the node to match with minimum cost and  for labelling it with that minimum cost. This should be called on the node before using any of the dumpcover(node), printInstructions(node), printBlockInstructions(list of nodes).

dumpcover(node) gives the matched AST grammar with minimum cost for the burg node

printInstructions(node) generates the assembly instructions for the code statement represented by for the burg node

printBlockInstructions(list of nodes) generates the assembly code for all the burg nodes in the list of nodes, with out using the register of the result of the  previous nodes while allocating registers for instructions of every burg node.

## 4.Usage
	python|python pyburg.py [-p prefix | -maxcost=ddd ]... input.brg output.py 
prefix can be specified with `-p prefix` as an optional argument which will append the specified prefix for all the generated functions in `output.py`
maxcost can be specified as the optional argument, otherwise it is default set to 32767
The last two arguments are the input burg file and the outpu python file.
Executing the above command generates a python code, which contains all the functions for tree labelling, dumpcover, printInstructionsts..etc along with the user written code in burg file.	

## 5.Example
### Input

### Output

do changes for prefix, rule number position, block instructions


