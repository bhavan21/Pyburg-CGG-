import sys

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
