"""
cyburg -- A python 3 implementation of iburg which is originally written in c
This is the root file
Usage: python3 cyburg.py [-T | -I | -p prefix | -maxcost=ddd ]... [ [ input ] output
"""

import sys
import math
import globals
from util import *
from gram import *

table =globals.table
nts = globals.nts
terms = globals.terms
rules = globals.rules
TERM = globals.TERM
NONTERM = globals.NONTERM


infp = None
outfp = None
Iflag = 0
Tflag = 0
maxcost = 32767
prefix = "p"
errcnt = 0



def yywarn(msg, *args):
	"""
	prints warnings to the stdout along with the lineno
	"""
	print("line %d: warning: " % globals.yylineno + msg % args)

def yyerror(msg, *args):
	"""
	prints errors to the stdout along with the lineno
	"""
	print("line %d: " % globals.yylineno +msg % args)
	global errcnt
	errcnt += 1

def copyheader():
	"""
	copy the header of the input file to output file
	"""
	prev_pos = infp.tell()
	buf = infp.readline()
	if not buf:
		return
	while (buf == "%{\n" or buf == "%{\r\n"):
		globals.yylineno += 1
		while True:
			buf = infp.readline()
			if not buf:
				print("unterminated %{...%}")
				return
			globals.yylineno += 1
			if (buf == "%}\n" or buf == "%}\r\n"):
				break
			outfp.write(buf)
		prev_pos = infp.tell()
		buf = infp.readline()
		if not buf:
			return
	infp.seek(prev_pos)

def yyparse():
	"""
	parses the tree grammar and stores all the terms, nts and rules
	"""
	globals.yylineno += 1
	ppercent = 0
	data = ""
	while True:
		buf = infp.readline()
		if not buf:
			break
		# %% should be in a single line
		if "%%" in buf:
			if (buf == "%%\n" and buf == "%%\n" and buf == "%%\r\n" and buf == "%%\r\n"):
				print("Other characters in %% line will be ignored")
			if ppercent:
				break
			else:
				ppercent += 1
		data += buf
	import ply.lex as lex
	import ply.yacc as yacc
	lexer = lex.lex()
	globals.parser = yacc.yacc()
	# print(data)
	globals.parser.parse(data)

def copyfooter():
	"""
	copy the footer of the input file to output file
	"""
	global yylineno
	outfp.write("\n")
	while True:
		buf = infp.readline()
		if not buf:
			return
		globals.yylineno += 1
		outfp.write(buf)

def getntnumber():
	globals.ntnumber += 1
	return globals.ntnumber

def declared(name):
	if name in table.keys():
		return table[name]
	else:
		return None

def term(name,esn):
	"""create a new terminal name with external symbol number esn"""
	p = declared(name)
	if p:
		yyerror("redefinition of terminal '%s'", name)
	else:
		p = Term(name)
	p.esn = esn
	p.kind = TERM
	p.arity = -1
	table[name] = p
	for term in terms:
		if term.esn == esn:
			yyerror("duplicate external symbol number '%s=%d'\n",p.name, p.esn)
	terms.append(p)
	return p

def nonterm(name):
	"""create a new terminal name, if necessary"""
	p = declared(name)
	if p:
		p = table[name]
		if p.kind == NONTERM:
			return p
		elif p.kind == TERM:
			yyerror("'%s' is a terminal",name)
	else:
		p = Nonterm(name)
	p.number = getntnumber()
	p.kind = NONTERM
	table[name] = p
	if (p.number == 1):
		# global start
		globals.start = p;
	nts.append(p)
	return p

def tree(name,children):
	"""create & initialize a tree node with the given fields"""
	arity = len(children)

	if not declared(name):
		if arity > 0:
			yyerror("undefined terminal '%s'", name)
			p = term(name, -1)
		elif arity == 0:
			p = nonterm(name)
	else:
		p = table[name]
		if (p.kind == NONTERM and arity > 0):
			yyerror("`%s' is a non-terminal and arity > 0", name)
			p = term(name, -1)
	if (p.kind == TERM and p.arity == -1):
		p.arity = arity
	if (p.kind == TERM and arity != p.arity):
		yyerror("inconsistent arity for terminal '%s'", name)
	t = Tree()
	t.op = p
	t.children = children

	t.nterms = (p.kind == TERM)
	for child in children:
		t.nterms += child.nterms

	return t

def rule(lhs,rhs,ern,cost, instructionlist, return_operand):
	"""create & initialize a rule with the given fields"""
	r = Rule()
	p = rhs.op
	nt = nonterm(lhs)
	r.lhs = nt
	nt.rules.append(r);

	r.packed = len(nt.rules)
	r.rhs = rhs
	r.ern = ern
	r.cost = cost
	r.instructions = instructionlist
	r.return_operand = return_operand

	if (p.kind == TERM):
		p.rules.append(r)
	elif (p.kind == NONTERM and len(rhs.children)==0):
		p.chain.append(r)
	for rule in rules:
		if (rule.ern == r.ern):
			yyerror("duplicate external rule number '%d'", r.ern);
	rules.append(r)
	return r

def printf(msg, *args):
	"""prints formatted output"""
	# print(msg)
	class Count:
		counter=-1
	counter = Count()
	def getArg(counter = counter):
		counter.counter += 1
		# print(counter.counter)
		return args[counter.counter]
	i=0
	while i < len(msg):
		if msg[i] == '~':
			i += 1
			if msg[i] == 'd':
				outfp.write(str(getArg()))
			elif msg[i] == 's':
				outfp.write(getArg())
			elif msg[i] == 'P':
				# outfp.write(prefix+'_')
				pass
			elif msg[i] == 'T':
				t = getArg()
				printf("~S", t.op)
				if len(t.children)>0:
					printf("(~T", t.children[0])
					for j in range(1,len(t.children)):
						printf(",~T", t.children[j])
					printf(")")

			elif msg[i] == 'R':
				r = getArg()
				printf("~S: ~T", r.lhs, r.rhs)
			elif msg[i] == 'S':
				p = getArg()
				outfp.write(p.name)
			elif (msg[i] == '1' or msg[i] == '2' or msg[i] == '3' or msg[i] == '4' or msg[i] == '5'):
				count = int(msg[i])
				for j in range(0,count):
					outfp.write('\t')
			else:
				outfp.write("~"+msg[i])
		else:
			outfp.write(msg[i])
		i += 1


def reach(t):
	""" mark all non-terminals in tree t as reachable"""
	p = t.op
	if p.kind == NONTERM:
		if not p.reached:
			ckreach(p)
	for child in t.children:
		reach(child)

def ckreach(p):
	"""mark all non-terminals reachable from p"""
	p.reached = 1
	for r in p.rules:
		reach(r.rhs)


def emitheader():
	"""emit initial definitions"""
	printf('''import sys
try:
	MAX_COST # exists
except NameError:
	MAX_COST = 1e16\n\n''')

	printf('''try :
	trace
except NameError:
	def trace(p, rule, cost, bestcost):
		sys.stdout.write("%s matched %s with cost %d vs. %d\\n" % (p,rule.value, cost, bestcost))\n\n''')

def emitdefs():
	"""emit non-terminal defines and data structures"""
	printf("~PMAX_NT = ~d;\n\n", globals.ntnumber)
	for p in nts:
		printf("~P~S_NT = ~d\n", p, p.number-1)

	# if Iflag:
	# 	printf("\n~Pntname[] = [")
	# 	for p in nts:
	# 		printf("~1\"~S\",\n", p)
	# 	printf("\n];\n\n")


def emitnts():
	printf("\n~Pnts = {\n\n")
	for p in nts:
		printf("~1~d : \"~S\",\n", p.number-1, p)
	printf("}\n\n")

def emitterms():
	printf("\n~Pterms = {\n\n")
	for p in terms:
		printf("~1~d : \"~S\",\n", p.esn, p)
	printf("}\n\n")


def computents(t):
	"""fill in ret with burm_nts vector for tree t"""
	ret = ""
	if t:
		p = t.op;
		if p.kind == NONTERM:
			ret += "%s_NT, "%(p.name)
		for child in t.children:
			ret += computents(child)
	return ret



def emitrules():
	printf('''class Rule:
	def __init__(self, value, lhs, rhs, nts, number, cost, instructions, return_operand):
		self.value = value # entire rule as a string in its original format
		self.lhs = lhs # ntnumber of lhs
		self.rhs = rhs # string of rhs
		self.nts = nts # all nts in rhs
		self.number = number # Rule number
		self.cost = cost # cost of the rule
		self.instructions = instructions # instructions to be printed
		self.return_operand = return_operand # operand to be assigned to lhs reg if its not given in instructions\n\n''')

	printf('''class Instruction:
	def __init__(self, opcode, operands):
		self.opcode = opcode # opcode
		self.operands = operands # operands\n''')

	ins_starts = {}
	ins_ends = {}
	ins_count = 0
	printf("\n~Pinstructions = [\n")
	for r in rules:
		ins_starts[r.ern] = ins_count
		for ins in r.instructions:
			printf("~1Instruction(\"~s\", ~s),\n", ins.opcode, str(ins.operands))
			ins_count+=1
		ins_ends[r.ern] = ins_count
	printf("]\n\n")


	printf("\n~Prules = {\n\n")
	for r in rules:
		nts = "["+computents(r.rhs)+ "]"
		if ins_starts[r.ern]!=ins_ends[r.ern]:
			printf("~1~d : Rule(\"~R\", ~d, \"~T\", ~s , ~d, ~d, ~Pinstructions[~d:~d], ~d),\n", r.ern, r, r.lhs.number-1, r.rhs, nts, r.ern, r.cost, ins_starts[r.ern], ins_ends[r.ern],r.return_operand)
		else:
			printf("~1~d : Rule(\"~R\", ~d, \"~T\", ~s , ~d, ~d,[], ~d),\n", r.ern, r, r.lhs.number-1, r.rhs, nts, r.ern, r.cost, r.return_operand)

	printf("}\n\n")

def emitfuncs():
	printf('''# gives the best rule to apply for that non-terminal
def getrule(p, goalnt):
	assert goalnt in nts.keys(), "Bad goal nonterminal %d in getrule\\n" % goalnt
	assert p, "Bad Node argument to getrule\\n"
	ruleno = p.rule[goalnt];
	assert ruleno in rules.keys(), "Bad rule number %d for non-terminal %d in getrule\\n" % (ruleno, goalnt)
	return rules[ruleno]\n\n''')


def emitnode():
	"""emit the definition of the state structure"""
	printf('''class Node:

	def __init__(self):
		self.value = None # esn
		self.children = [] #child nodes
		self.cost = [ MAX_COST for i in range(MAX_NT)]
		self.rule = [ -1 for i in range(MAX_NT)]

	def label(self):
		for child in self.children:
			assert child, "Bad Child for Node %d in tree\\n"% self.value
			child.label()
		self.match()\n\n''')


def emitrecord(prefix, r, cost):
	"""emit code that tests for a winning match of rule r"""
	if Tflag: printf("~s~Ptrace(self, rules[~d], cost + ~d, self.cost[~P~S_NT])\n",prefix, r.ern, cost, r.lhs)

	printf("~sif (", prefix);

	printf("cost + ~d < self.cost[~P~S_NT]): # ~R\n", cost, r.lhs, r)
	printf("~s~1self.cost[~P~S_NT] = cost + ~d;\n",prefix, r.lhs, cost)
	printf("~s~1self.rule[~P~S_NT] = ~d;\n",prefix, r.lhs, r.ern);
	if len(r.lhs.chain):printf("~s~1self.closure_~S(cost + ~d);\n", prefix, r.lhs, cost);
	printf("\n");

def emitclosure():
	"""emit the closure functions"""
	for p in nts:
		if len(p.chain):
			printf("~1def closure_~S(self, cost):\n", p);
			for r in p.chain:
				emitrecord("\t\t", r, r.cost)
	printf("\n")

def emitstate():
	printf('''\tdef match(self):
		if self.value is None: assert 0, "No value in node\\n"\n''')

	for p in terms:
		emitcase(p)

	printf('''\t\telse: assert 0, "Bad operator %d in match\\n" % self.value\n\n''')



def emitcase(p):
	"""emit one case in function state"""
	if p.kind==NONTERM:
		print("Internal Error: emitcase being called for a non terminal %s"%p.name)
		return

	printf("\n~2elif self.value == ~d: # ~S\n", p.esn, p)

	printf('''\n~3assert len(self.children) == ~d, " Invalid arity supplied to %d"%self.value\n''', p.arity)
	if p.arity == 0 or p.arity == -1: pass
	else:
		for i in range(0,p.arity):
			printf('''~3assert self.children[~d], "self.children[~d] is None for %d"%self.value\n''',i,i)
	printf("\n")

	for r in reversed(p.rules):
		if r.rhs.nterms <= 1:
			printf("~3if (~1# ~R\n", r);
			printf("~5True # No terminal checks\n")
			printf("~4):\n\n~4cost = ");
		else:
			printf("~3if (~1# ~R\n", r);
			if len(r.rhs.children)>0:
				for i in range(0,len(r.rhs.children)-1):
					emittest(r.rhs.children[i], "self.children[%d]"%i, "and" if r.rhs.children[i+1] and r.rhs.children[i+1].nterms else "");
				emittest(r.rhs.children[len(r.rhs.children)-1], "self.children[%d]"%(len(r.rhs.children)-1), "");
			printf("~4):\n\n~4cost = ");
		for i in range(0,len(r.rhs.children)):
			 emitcost(r.rhs.children[i],  "self.children[%d]"%i);
		printf("~d;\n", r.cost);
		emitrecord("\t\t\t\t", r, 0);


def emitcost(t, v):
	"""emit cost computation for tree t"""
	p = t.op
	if p.kind == TERM:
		for i in range(0,len(t.children)):
			emitcost(t.children[i], "%s.children[%d]" % (v,i))
	else:
		printf("~s.cost[~P~S_NT] + ", v, p)


def emittest(t, v, suffix):
	"""emit clause for testing a match"""
	if t is None:
		print("Internal Error, Empty Tree Passed to emittest\n")
		return

	p = t.op
	if p.kind == TERM:
		printf("~5~s.value == ~d ~s # ~S\n", v, p.esn, "and" if t.nterms>1 else suffix, p);
		if len(t.children)>0:
			for i in range(0,len(t.children)-1):
				emittest(t.children[i],"%s.children[%d]"%(v,i), "and" if t.children[i+1] and t.children[i+1].nterms else suffix)
			emittest(t.children[len(t.children)-1],"%s.children[%d]"%(v,len(t.children)-1), suffix)




# def emitstate(terms, start, ntnumber):
# 	"""emit state function"""
# 	printf("STATE_TYPE %Pstate(int op, STATE_TYPE left, STATE_TYPE right) {\n%1int c;\n"
# "%1struct %Pstate *p, *l = (struct %Pstate *)left,\n"
# "%2*r = (struct %Pstate *)right;\n\n%1assert(sizeof (STATE_TYPE) >= sizeof (void *));\n%1");
# 	printf("{\n%2p = ALLOC(sizeof *p);\n"
# "%2%Passert(p, PANIC(\"ALLOC returned NULL in %Pstate\\n\"));\n"
# "%2p->op = op;\n%2p->left = l;\n%2p->right = r;\n%2p->rule.%P%S = 0;\n", start);
# 	for i in range(1,ntnumber+1):
# 		printf("%2p->cost[%d] =\n", i);
# 	printf("%3%d;\n%1}\n%1switch (op) {\n", maxcost);
# 	for p in terms:
# 		emitcase(p)
# 	printf("%1default:\n"
# "%2%Passert(0, PANIC(\"Bad operator %%d in %Pstate\\n\", op));\n%1}\n"
# "%1return (STATE_TYPE)p;\n}\n\n")




def computekids(t, v, kidnum):
	"""compute paths to kids in tree t"""
	p = t.op;
	ret = ""
	if p.kind == NONTERM:
		ret += "\t\tkids.append((%s, rule.nts[%d]));\n"% (v, kidnum.count)
		kidnum.count+=1
	elif p.arity > 0:
		for i in range(0,len(t.children)):
			ret += computekids(t.children[i], "%s.children[%d]" % (v,i), kidnum);
	return ret

def emitkids():
	"""emit burm_kids"""
	class KidCount:
		count=0
	existing = {}
	for r in rules:
		out = computekids(r.rhs, "p", KidCount())
		if existing.get(out) is None:
			existing[out] = [r]
		else:
			existing[out].append(r)

	printf('''#  returns nodes to be matched and the non-terminals to which they must be  further to matched based on the rule applied to the current node
def getmatchedkids(p, rule):\n
	kids = []
	ruleno = rule.number
	assert p, "Bad Node argument tree in kids\\n";\n
	if ruleno is None: assert 0, "No rulenumber associated with rule\\n"\n\n''')

	for out,rulesList in existing.items():
		printf('''~1elif(\n''')
		for i, r in enumerate(rulesList):
			if i < len(rulesList)-1: printf("~3ruleno == ~d or # ~R\n", r.ern, r)
			elif i == len(rulesList)-1: printf("~3ruleno == ~d # ~R\n", r.ern, r)
		printf("~2):\n")
		printf("\n~s\n", out if out != "" else "\t\tpass\n")
	printf('''~1else: assert 0, "Bad external rule number %d in getmatchedkids\\n"%ruleno

	return kids\n\n''')

def computeleaves(t, v, kidnum):
	"""compute paths to leaves in tree t"""
	p = t.op;
	ret = ""
	if p.kind == NONTERM:
		ret += "\t\tkids.append((%s, rule.nts[%d]));\n"% (v, kidnum.count)
		kidnum.count+=1
	elif p.arity == 0:
		ret += "\t\tkids.append((%s, None));\n"% (v)
	elif p.arity > 0:
		for i in range(0,len(t.children)):
			ret += computeleaves(t.children[i], "%s.children[%d]" % (v,i), kidnum);
	return ret

def emitleaves():
	"""emit leafs"""
	class KidCount:
		count=0
	existing = {}
	for r in rules:
		out = computeleaves(r.rhs, "p", KidCount())
		if existing.get(out) is None:
			existing[out] = [r]
		else:
			existing[out].append(r)

	printf('''#  returns nodes to be matched and the non-terminals to which they must be  further to matched based on the rule applied to the current node
def getmatchedleaves(p, rule):\n
	kids = []
	ruleno = rule.number
	assert p, "Bad Node argument tree in kids\\n";\n
	if ruleno is None: assert 0, "No rulenumber associated with rule\\n"\n\n''')

	for out,rulesList in existing.items():
		printf('''~1elif(\n''')
		for i, r in enumerate(rulesList):
			if i < len(rulesList)-1: printf("~3ruleno == ~d or # ~R\n", r.ern, r)
			elif i == len(rulesList)-1: printf("~3ruleno == ~d # ~R\n", r.ern, r)
		printf("~2):\n")
		printf("\n~s\n", out if out != "" else "\t\tpass\n")
	printf('''~1else: assert 0, "Bad external rule number %d in getmatchedkids\\n"%ruleno

	return kids\n\n''')

def emitregallocator():
	printf('''\n\n
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
		''')

def emitPrintInstructions():
	printf('''\n\n
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
		assert rule.return_operand>0, "Return operand is negative(%d) in match %s\\n" %(rule.return_operand,rule.value)
		out_value = nt_values[rule.return_operand]
		termType = kidTermTypes[rule.return_operand]
		if out_value in regs_to_free:
			regs_to_free.remove(out_value)
	
	for ins in rule.instructions:
		# print(ins.opcode)
		sys.stdout.write(ins.opcode)
		for operand in ins.operands:
			   sys.stdout.write(" "+str(nt_values[operand]))
		sys.stdout.write("\\n")

	for reg in regs_to_free:
		# print("Reg to free: ",reg)
		regAllocator.unassignReg(reg)

	return out_value,termType

def printBlockInstructions(stmtAsts = []):
	for p in stmtAsts:
		printInstructions(p)
''')

def emitExtras():
	printf('''\n\n
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
	sys.stdout.write("\\t"*indent)
	sys.stdout.write("%s\\n"% rule.value)

	for kid, nt in getmatchedkids(p, rule):
		dumpcover(kid, nt, indent + 1)

def setEnvironment(registers, variableOffsetFunc):
	global ~PgetVariableOffset
	~PgetVariableOffset = variableOffsetFunc
	global ~PregList
	~PregList = registers
	global regAllocator
	regAllocator = RegAllocator(~PregList)

''')


def main():
	"""main function"""
	global infp,outfp,Iflag,Tflag
	for i in range(1,len(sys.argv)):
		arg = sys.argv[i]
		if sys.argv[i] == "-I":
			Iflag = 1
		elif sys.argv[i] == "-T":
			Tflag = 1
		elif sys.argv[i][0:9] == "-maxcost=":
			maxcost = int(sys.argv[i][9:])
		elif sys.argv[i][0:2] == "-p" and len(sys.argv[i])>2:
			prefix = sys.argv[i][2:]
		elif sys.argv[i][0:2] == "-p" and i+1 < len(sys.argv):
			i = i+1
			prefix = sys.argv[i]
		elif sys.argv[i][0] == '-' and len(sys.argv[i])>1:
			print("usage: python3 %s [-T | -I | -p prefix | -maxcost=ddd ]... [ [ input ] output " % (sys.argv[0]))
			exit(1)
		elif infp is None:
			if sys.argv[i] == "-":
				infp = sys.stdin
			else:
				try:
					infp = open(sys.argv[i], "r")
				except:
					print("%s: can't read '%s' " % (sys.argv[0], sys.argv[i]))
					exit(1)
		elif outfp is None:
			if sys.argv[i] == "-":
				outfp = sys.stdout
			else:
				try:
					outfp = open(arg, "w")
				except:
					print("%s: can't write '%s' " % (sys.argv[0], sys.argv[i]))
					exit(1)
	if infp is None:
		infp = sys.stdin
	if outfp is None:
		outfp = sys.stdout

	copyheader()
	yyparse()

	def sortUsingesn(term):
		return term.esn
	def sortUsingntnumber(nt):
		return nt.number
	def sortUsingern(rule):
		return rule.ern
	terms.sort(key = sortUsingesn)
	nts.sort(key = sortUsingntnumber)
	rules.sort(key = sortUsingern)

	if globals.start:
		ckreach(globals.start)

	for p in nts:
		if not p.reached:
			printf("can't reach non-terminal `%s'\n", p.name);

	emitheader();

	emitdefs();

	emitnts();

	emitterms();

	emitrules();

	emitnode();

	emitclosure();

	emitstate();

	emitfuncs();

	emitkids();

	emitregallocator();

	emitleaves();

	emitPrintInstructions();

	emitExtras()

	printf("####################################################################################################\n")
	printf("###############################auto-generated code ends here########################################\n")
	printf("####################################################################################################\n")


	copyfooter()

	return errcnt > 0;

if __name__== "__main__":
	main()