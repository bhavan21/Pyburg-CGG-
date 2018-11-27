%term EQUALS=1 PLUS=2 NAME=3 CONST=4

%%
stmt : EQUALS(NAME,reg) {sw $1,$2;} = 1 (2);
reg	: PLUS(reg,reg) {add $$,$1,$2;} = 2 (1);
reg	: PLUS(reg,CONST) {addi $$,$1,$2;} = 2 (1);
reg : NAME {lw $$,$1;} = 3 (1);

%%

EQUALS=1
PLUS=2
NAME=3
CONST=4

offset=0
mem={}

def getVariableOffset(var):
	global offset
	if var not in mem.keys():
		offset += 4;
		mem[var] = offset
	ret = "%d($sp)"%(offset)
	return ret

class tupleToAST:
	def __init__(self,ast):
		self.type = None
		self.value = None
		self.children = []
		if type(ast) == type((0, 0)):
			self.type = ast[0]
			if ast[1]: self.children.append(tupleToAST(ast[1]))
			if ast[2]: self.children.append(tupleToAST(ast[2]))
		else:
			self.value = str(ast)
			if type(ast) == type('s'):
				self.type = NAME
			else:
				self.type = CONST

	def getType(self):
		return self.type

	def getValue(self):
		return self.value

	def getChildren(self):
		return self.children

# a generic example with single statment
# a = b+c+5

astTuple = (EQUALS,'a',(PLUS,(PLUS,'b','c'),'5')) # ast in tuple format
ast = tupleToAST(astTuple) # ast

registers = ["$t0", "$t1", "$t2", "$t3", "$t4", "$t5", "$t6", "$t7", "$t8", "$t9",
 "$s0", "$s1", "$s2", "$s3", "$s4", "$s5", "$s6", "$s7", "$s8", "$s9"]


def main():
		setEnvironment(registers = registers, variableOffsetFunc = getVariableOffset)
		node = initializeNode(ast)
		node.label()
		dumpcover(node)
		printInstructions(node)

if __name__== "__main__":
	main()

