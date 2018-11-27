import sys
try:
	MAX_COST # exists
except NameError:
	MAX_COST = 1e16

try :
	trace
except NameError:
	def trace(p, rule, cost, bestcost):
		sys.stdout.write("%s matched %s with cost %d vs. %d\n" % (p,rule.value, cost, bestcost))

MAX_NT = 2;

stmt_NT = 0
reg_NT = 1

nts = {

	0 : "stmt",
	1 : "reg",
}


terms = {

	1 : "EQUALS",
	2 : "PLUS",
	3 : "NAME",
}

class Rule:
	def __init__(self, value, lhs, rhs, nts, number, cost, instructions, return_operand):
		self.value = value # entire rule as a string in its original format
		self.lhs = lhs # ntnumber of lhs
		self.rhs = rhs # string of rhs
		self.nts = nts # all nts in rhs
		self.number = number # Rule number
		self.cost = cost # cost of the rule
		self.instructions = instructions # instructions to be printed
		self.return_operand = return_operand # operand to be assigned to lhs reg if its not given in instructions

class Instruction:
	def __init__(self, opcode, operands):
		self.opcode = opcode # opcode
		self.operands = operands # operands

instructions = [
	Instruction("sw", [1, 2]),
	Instruction("add", [0, 1, 2]),
	Instruction("lw", [0, 1]),
]


rules = {

	1 : Rule("stmt: EQUALS(NAME,reg)", 0, "EQUALS(NAME,reg)", [reg_NT, ] , 1, 2, instructions[0:1], 0),
	2 : Rule("reg: PLUS(reg,reg)", 1, "PLUS(reg,reg)", [reg_NT, reg_NT, ] , 2, 1, instructions[1:2], 0),
	3 : Rule("reg: NAME", 1, "NAME", [] , 3, 1, instructions[2:3], 0),
}

class Node:

	def __init__(self):
		self.value = None # esn
		self.children = [] #child nodes
		self.cost = [ MAX_COST for i in range(MAX_NT)]
		self.rule = [ -1 for i in range(MAX_NT)]

	def label(self):
		for child in self.children:
			assert child, "Bad Child for Node %d in tree\n"% self.value
			child.label()
		self.match()


	def match(self):
		if self.value is None: assert 0, "No value in node\n"

		elif self.value == 1: # EQUALS

			assert len(self.children) == 2, " Invalid arity supplied to %d"%self.value
			assert self.children[0], "self.children[0] is None for %d"%self.value
			assert self.children[1], "self.children[1] is None for %d"%self.value

			if (	# stmt: EQUALS(NAME,reg)
					self.children[0].value == 3  # NAME
				):

				cost = self.children[1].cost[reg_NT] + 2;
				if (cost + 0 < self.cost[stmt_NT]): # stmt: EQUALS(NAME,reg)
					self.cost[stmt_NT] = cost + 0;
					self.rule[stmt_NT] = 1;


		elif self.value == 2: # PLUS

			assert len(self.children) == 2, " Invalid arity supplied to %d"%self.value
			assert self.children[0], "self.children[0] is None for %d"%self.value
			assert self.children[1], "self.children[1] is None for %d"%self.value

			if (	# reg: PLUS(reg,reg)
					True # No terminal checks
				):

				cost = self.children[0].cost[reg_NT] + self.children[1].cost[reg_NT] + 1;
				if (cost + 0 < self.cost[reg_NT]): # reg: PLUS(reg,reg)
					self.cost[reg_NT] = cost + 0;
					self.rule[reg_NT] = 2;


		elif self.value == 3: # NAME

			assert len(self.children) == 0, " Invalid arity supplied to %d"%self.value

			if (	# reg: NAME
					True # No terminal checks
				):

				cost = 1;
				if (cost + 0 < self.cost[reg_NT]): # reg: NAME
					self.cost[reg_NT] = cost + 0;
					self.rule[reg_NT] = 3;

		else: assert 0, "Bad operator %d in match\n" % self.value

# gives the best rule to apply for that non-terminal
def getrule(p, goalnt):
	assert goalnt in nts.keys(), "Bad goal nonterminal %d in getrule\n" % goalnt
	assert p, "Bad Node argument to getrule\n"
	ruleno = p.rule[goalnt];
	assert ruleno in rules.keys(), "Bad rule number %d for non-terminal %d in getrule\n" % (ruleno, goalnt)
	return rules[ruleno]

#  returns nodes to be matched and the non-terminals to which they must be  further to matched based on the rule applied to the current node
def getmatchedkids(p, rule):

	kids = []
	ruleno = rule.number
	assert p, "Bad Node argument tree in kids\n";

	if ruleno is None: assert 0, "No rulenumber associated with rule\n"

	elif(
			ruleno == 3 # reg: NAME
		):

		pass

	elif(
			ruleno == 2 # reg: PLUS(reg,reg)
		):

		kids.append((p.children[0], rule.nts[0]));
		kids.append((p.children[1], rule.nts[1]));

	elif(
			ruleno == 1 # stmt: EQUALS(NAME,reg)
		):

		kids.append((p.children[1], rule.nts[0]));

	else: assert 0, "Bad external rule number %d in getmatchedkids\n"%ruleno

	return kids




class RegAllocator:
	
	def valid(self, regNameList):
		seen = set()
		for name in regNameList:
		    if name not in seen:
		        seen.add(name)
		assert(len(seen)==len(regNameList)), "Error: Duplicate Register Name in the names provided"
		return 1

	def __init__(self, regNameList=[]):
		self.valid(regNameList)
		self.numReg = len(regNameList)
		self.regNameList = regNameList
		self.reglist = [reg for reg in range(self.numReg)]
		self.usedRegQueue = []

	def regNameToNum(self, register):
		assert (register in self.regNameList), "Error: No such Register Found"
		return self.regNameList.index(register)

	def regNumToName(self, reg):
		assert (reg>=0 and reg < self.numReg), "Error: Register Index exceeds bounds"
		return self.regNameList[reg]

	def setNumReg(self,regNameList):
		self.valid(regNameList)
		self.numReg = len(regNameList)
		self.regNameList = regNameList
		self.reglist = [reg for reg in range(self.numReg)]
		self.usedRegQueue = []

	def isFree(self, reg):
		assert (reg is not None) and (reg>=0) and (reg<self.numReg), "Error: Invalid %s argument passed as register"%(reg)
		if reg in self.usedRegQueue:
			return 0
		return 1

	def findFreeReg(self):
		for reg in self.reglist:
			if self.isFree(reg):
				return reg
		return -1

	def assignReg(self):
		reg = self.findFreeReg()
		self.usedRegQueue.append(reg)
		return self.regNumToName(reg)

	def unassignReg(self, register):
		reg = self.regNameToNum(register)
		if self.isFree(reg):
			sys.stdout.write("Error: Trying to free a free Register")
		self.usedRegQueue.remove(reg)
		#  returns nodes to be matched and the non-terminals to which they must be  further to matched based on the rule applied to the current node
def getmatchedleaves(p, rule):

	kids = []
	ruleno = rule.number
	assert p, "Bad Node argument tree in kids\n";

	if ruleno is None: assert 0, "No rulenumber associated with rule\n"

	elif(
			ruleno == 2 # reg: PLUS(reg,reg)
		):

		kids.append((p.children[0], rule.nts[0]));
		kids.append((p.children[1], rule.nts[1]));

	elif(
			ruleno == 1 # stmt: EQUALS(NAME,reg)
		):

		kids.append((p.children[0], None));
		kids.append((p.children[1], rule.nts[0]));

	elif(
			ruleno == 3 # reg: NAME
		):

		kids.append((p, None));

	else: assert 0, "Bad external rule number %d in getmatchedkids\n"%ruleno

	return kids




def printInstructions(p, goalnt=0):
	rule = getrule(p, goalnt) 

	nt_values = {}
	regs_to_free = []
	out_value = None
	termType = 2 # default
	kidTermTypes = {}
	kidnum = 1
	for kid, nt in getmatchedleaves(p, rule):
		if nt is None:
			if kid.value == CONST:
				nt_values[kidnum] = kid.out_value
				kidTermTypes[kidnum]=0
			if kid.value == NAME:
				nt_values[kidnum] = getVariableOffset(kid.out_value)
				kidTermTypes[kidnum]=1
		else:
			# termType is for CONST, NAME, reg are 0,1,2 respectively
			rhsReg,kidTermType = printInstructions(kid, nt)
			nt_values[kidnum] = rhsReg
			kidTermTypes[kidnum]=kidTermType
			if kidTermType==2:
				regs_to_free.append(rhsReg)
		kidnum+=1

	for ins in rule.instructions:
		for operand in ins.operands:
			if operand not in nt_values.keys():
				reg = regAllocator.assignReg()
				nt_values[operand] = reg
				if operand!=0: regs_to_free.append(reg)
				else: out_value = reg

	if out_value is None and rule.return_operand!=0:
		assert rule.return_operand>0, "Return operand is negative(%d) in match %s\n" %(rule.return_operand,rule.value)
		out_value = nt_values[rule.return_operand]
		termType = kidTermTypes[rule.return_operand]
		if out_value in regs_to_free:
			regs_to_free.remove(out_value)
	
	for ins in rule.instructions:
		# print(ins.opcode)
		sys.stdout.write(ins.opcode)
		for operand in ins.operands:
			   sys.stdout.write(" "+str(nt_values[operand]))
		sys.stdout.write("\n")

	for reg in regs_to_free:
		# print("Reg to free: ",reg)
		regAllocator.unassignReg(reg)

	return out_value,termType

def printBlockInstructions(stmtAsts = []):
	for p in stmtAsts:
		printInstructions(p)



"""initializes tree required for labelling from user defined ast tree
user defined ast tree class must contain functions getValue()and getChildren() which return
	value of the root of the tree and the list of children trees respectively"""
def initializeNode(P):
	node = Node()
	node.value = P.getType()
	node.out_value = P.getValue()
	for child in P.getChildren():
		node.children.append(initializeNode(child))
	return node


def dumpcover(p, goalnt = 0, indent = 0):
	rule = getrule(p, goalnt)
	sys.stdout.write("\t"*indent)
	sys.stdout.write("%s\n"% rule.value)

	for kid, nt in getmatchedkids(p, rule):
		dumpcover(kid, nt, indent + 1)

def setEnvironment(registers, variableOffsetFunc):
	global getVariableOffset
	getVariableOffset = variableOffsetFunc
	global regList
	regList = registers
	global regAllocator
	regAllocator = RegAllocator(regList)

####################################################################################################
###############################auto-generated code ends here########################################
####################################################################################################


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

# demonstating connection of pyburg with symbol table through user written getVariableOffset function
# a = b+c+d

astTuple = (EQUALS,'a',(PLUS,(PLUS,'b','c'),'d')) # ast in tuple format
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

