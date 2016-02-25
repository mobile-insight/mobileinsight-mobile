import math

class E_BST_Root:
    def __init__(self, stat = [0,0,0], data = None, left = None, right = None):
        self.__NTotal = 0
        self.__SigmayTotal = 0
        self.__Sigmay2Total = 0

        self.stat = stat # [N, Sigma y, Sigma y2] <= split_spot
        self.data = data
        self.left = left
        self.right = right
        return

    def getName(self):
        return self.__class__.__name__

    def add(self, data, y): # update the E-BST using current sample
        self.__NTotal += 1
        self.__SigmayTotal += y
        self.__Sigmay2Total += y * y

        if (self.left == None) & (self.right == None): # root or leaf node
            if self.data == None: #initialized root
                self.data = data
                self.stat[0] += 1
                self.stat[1] += y
                self.stat[2] += y * y
            else:
                if data <= self.data:
                    self.stat[0] += 1
                    self.stat[1] += y
                    self.stat[2] += y * y
                    if data != self.data:
                        self.left = E_BST_Other(stat = [0,0,0])
                        self.left.add(data, y)
                else:
                    self.right = E_BST_Other(stat = [0,0,0])
                    self.right.add(data, y)
        else: #internal
            if data <= self.data:
                if self.left == None:
                    self.left = E_BST_Other(stat = [0,0,0])
                    self.left.add(data, y)
                else:
                    if data != self.data:
                        self.left.add(data, y)
                self.stat[0] += 1
                self.stat[1] += y
                self.stat[2] += y * y
            else:
                if self.right == None:
                    self.right = E_BST_Other(stat = [0,0,0])
                    self.right.add(data, y)
                else:
                    self.right.add(data, y)
        return

    def computeSDR(self): # find the best split for the current E-BST and return [SDR, split]
        maxSDR = -1
        splitSpot = -1
        leftTotalOpt = -1
        leftSigmayTotalOpt = -1
        leftTotal = 0
        leftSigmayTotal = 0
        leftSigmay2Total = 0
        if self.left != None:
            [maxSDR, splitSpot, leftTotalOpt, leftSigmayTotalOpt, leftTotal, leftSigmayTotal, leftSigmay2Total]\
                = self.left.computeSDR(maxSDR, splitSpot, leftTotalOpt, leftSigmayTotalOpt, self.__NTotal, self.__SigmayTotal, self.__Sigmay2Total, leftTotal, leftSigmayTotal, leftSigmay2Total)
        leftTotal += self.stat[0]
        leftSigmayTotal += self.stat[1]
        leftSigmay2Total += self.stat[2]
        rightTotal = self.__NTotal - leftTotal
        rightSigmayTotal = self.__SigmayTotal - leftSigmayTotal
        rightSigmay2Total = self.__Sigmay2Total - leftSigmay2Total
        SDR = self.sd(self.__NTotal, self.__SigmayTotal, self.__Sigmay2Total) \
              - leftTotal / self.__NTotal * self.sd(leftTotal, leftSigmayTotal, leftSigmay2Total) \
              - rightTotal / self.__NTotal * self.sd(rightTotal, rightSigmayTotal, rightSigmay2Total)
        if maxSDR < SDR:
            maxSDR = SDR
            splitSpot = self.data
            leftTotalOpt = leftTotal
            leftSigmayTotalOpt = leftSigmayTotal
        if self.right != None:
            [maxSDR, splitSpot, leftTotalOpt, leftSigmayTotalOpt, leftTotal, leftSigmayTotal, leftSigmay2Total]\
                = self.right.computeSDR(maxSDR, splitSpot, leftTotalOpt, leftSigmayTotalOpt, self.__NTotal, self.__SigmayTotal, self.__Sigmay2Total, leftTotal, leftSigmayTotal, leftSigmay2Total)
        leftTotal -= self.stat[0]
        leftSigmayTotal -= self.stat[1]
        leftSigmay2Total -= self.stat[2]
        return [maxSDR, splitSpot, leftTotalOpt, leftSigmayTotalOpt]

    def sd(self, total, sigmay, sigmay2):
        if total == 0:
            return 0
        else:
            if abs(sigmay2 - sigmay * sigmay / total) < 0.01:
                return 0
            else:
                return math.sqrt((sigmay2 - sigmay * sigmay / total) / total)

class E_BST_Other:
    def __init__(self, stat = [0,0,0], data = None, left = None, right = None):
        self.__stat = stat # [N, Sigma y, Sigma y2]
        self.data = data
        self.left = left
        self.right = right
        return

    def add(self, data, y): # update the E-BST using current sample
        if (self.left == None) & (self.right == None): # root or leaf node
            if self.data == None: # root
                self.data = data
                self.__stat[0] += 1
                self.__stat[1] += y
                self.__stat[2] += y * y
            else:
                if data <= self.data:
                    if data != self.data:
                        self.left = E_BST_Other(stat = [0,0,0])
                        self.left.add(data, y)
                    self.__stat[0] += 1
                    self.__stat[1] += y
                    self.__stat[2] += y * y
                else:
                    self.right = E_BST_Other(stat = [0,0,0])
                    self.right.add(data, y)
        else: # internal
            if data <= self.data:
                if self.left == None:
                    self.left = E_BST_Other(stat = [0,0,0])
                    self.left.add(data, y)
                else:
                    if data != self.data:
                        self.left.add(data, y)
                self.__stat[0] += 1
                self.__stat[1] += y
                self.__stat[2] += y * y
            else:
                if self.right == None:
                    self.right = E_BST_other(stat = [0,0,0])
                    self.right.add(data, y)
                else:
                    self.right.add(data, y)
        return

    def computeSDR(self, maxSDR, splitSpot, leftTotalOpt, leftSigmayTotalOpt, NTotal, SigmayTotal, Sigmay2Total, leftTotal, leftSigmayTotal, leftSigmay2Total): # find the best split for the current E-BST and return [SDR, split]
        if self.left != None:
            [maxSDR, splitSpot, leftTotalOpt, leftSigmayTotalOpt, leftTotal, leftSigmayTotal, leftSigmay2Total]\
                = self.left.computeSDR(maxSDR, splitSpot, leftTotalOpt, leftSigmayTotalOpt, NTotal, SigmayTotal, Sigmay2Total, leftTotal, leftSigmayTotal, leftSigmay2Total)
        leftTotal += self.__stat[0]
        leftSigmayTotal += self.__stat[1]
        leftSigmay2Total += self.__stat[2]
        rightTotal = NTotal - leftTotal
        rightSigmayTotal = SigmayTotal - leftSigmayTotal
        rightSigmay2Total = Sigmay2Total - leftSigmay2Total
        SDR = self.sd(NTotal, SigmayTotal, Sigmay2Total) \
              - leftTotal / NTotal * self.sd(leftTotal, leftSigmayTotal, leftSigmay2Total) \
              - rightTotal / NTotal * self.sd(rightTotal, rightSigmayTotal, rightSigmay2Total)
        if maxSDR < SDR:
            maxSDR = SDR
            splitSpot = self.data
            leftTotalOpt = leftTotal
            leftSigmayTotalOpt = leftSigmayTotal
        if self.right != None:
            [maxSDR, splitSpot, leftTotalOpt, leftSigmayTotalOpt, leftTotal, leftSigmayTotal, leftSigmay2Total]\
                = self.right.computeSDR(maxSDR, splitSpot, leftTotalOpt, leftSigmayTotalOpt, NTotal, SigmayTotal, Sigmay2Total, leftTotal, leftSigmayTotal, leftSigmay2Total)
        leftTotal -= self.__stat[0]
        leftSigmayTotal -= self.__stat[1]
        leftSigmay2Total -= self.__stat[2]
        return [maxSDR, splitSpot, leftTotalOpt, leftSigmayTotalOpt, leftTotal, leftSigmayTotal, leftSigmay2Total]

    def sd(self, total, sigmay, sigmay2):
        if total == 0:
            return 0
        else:
            if abs(sigmay2 - sigmay * sigmay / total) < 0.01:
                return 0
            else:
                return math.sqrt((sigmay2 - sigmay * sigmay / total) / total)

class HoeffdingTree:
    # node split
    DELTA = 0.01
    N_MIN = 200
    TAU = 0.05
    # change adaption
    T_MIN = 150
    ALPHA = 0.005
    LAMBDA = 50
    def __init__(self, stat=[0,0], attrNum=None, left=None, right=None, resPredict=None,
                attrType='con', splitDis=None, splitCon=None, attrInd=None, counter=0, attrTree = []):
        self.stat = stat #(N, Sigma y)
        self.resPredict = resPredict
        self.left = left
        self.right = right
        self.attrNum = attrNum
        self.attrType = attrType # discrete/continuous
        self.splitDis = splitDis
        self.splitCon = splitCon # current version not included
        self.attrInd = attrInd
        self.counter = 0 # num_of_nodes in each period (T = Nmin)
        self.__attrTree = []
        for x in range (0, attrNum):
            rootNode = E_BST_Root(stat = [0,0,0])
            self.__attrTree.append(rootNode)
        return

    def train(self, sample):
        lNode = self.update(sample) # return the leaf node where the sample lies in
        if lNode.counter == self.N_MIN:
            lNode.counter = 0
            lNode.resPredict = lNode.stat[1] / lNode.stat[0]
            curMax = -1
            attr1 = -1 # attr index with the highest SDR
            attr2 = -1 # attr index with the second highest SDR
            splitSpot = None
            SDRList = []
            for x in range (0, len(sample)-1): # find the best split of each attribute
                [SDR, split, leftTotal, leftSigmayTotal] = LNode.__attr_tree[x].computeSDR() #return the best split
                SDRList.append(SDR)
                if SDR > curMax:
                    curMax = SDR
                    if attr1 == -1 & attr2 == -1:
                        attr1 = x
                        attr2 = x
                    else:
                        attr2 = attr1
                        attr1 = x
                    splitSpot = split
            epsilon = math.sqrt(math.log(1 / self.delta)/(2 * self.N_MIN))
            if SDRList[attr2] / SDRList[attr1] + epsilon < 1: # criterion_is_satisfied
                lNode.split(attr1, splitSpot, sample, leftSigmayTotal / leftTotal, (lNode.stat[1] - leftSigmayTotal) / (lNode.stat[0] - leftTotal))
            elif SDRList[attr2] / SDRList[attr1] + self.TAU >= 1: # tie -> either is okay
                lNode.split(attr1, splitSpot, sample, leftSigmayTotal / leftTotal, (lNode.stat[1] - leftSigmayTotal) / (lNode.stat[0] - leftTotal))
            # reset E-BST for each node
            lNode.stat = [0,0]
            for x in range (0, len(sample)-1):
                lNode.__attrTree[x] = E_BST_Root(stat = [0,0,0])
        return

    def update(self, sample): # traverse the tree till the leaf node where the sample lies in, return the leaf node
        if (self.left == None) & (self.right == None): # initilized root or leaf node
            for x in range (0, len(sample)-1):
                self.__attrTree[x].add(float(sample[x]), float(sample[-1]))
            self.counter += 1
            self.stat[0] += 1
            self.stat[1] += float(sample[-1])
            return self
        #elif self.attr_type == 'dis': # internal node
        elif self.attr_type == 'con':
            if sample[self.attrInd] <= self.splitCon: #left node
                return self.left.update(sample)
            else: #right node
                return self.right.update(sample)

    def split(self, attr, splitSpot, sample, leftPredict, rightPredict): #split the current leaf node
        self.left = HoeffdingTree(attrNum = len(sample)-1, resPredict=leftPredict)
        self.right = HoeffdingTree(attrNum = len(sample)-1, resPredict=rightPredict)
        self.attrType = 'con'
        self.splitCon = splitSpot
        self.attrInd = attr
        for x in range(0, len(sample)-1):
            self.__attrTree[x] = None
        return

    def predict(self, sample):
        if (self.left == None) & (self.right == None):
            return self.resPredict
        #elif self.attr_type == 'dis':
        elif self.attr_type == 'con':
            if sample[self.attrInd] <= self.splitCon:
                return self.left.predict(sample)
            elif sample[self.attrInd] > self.splitCon:
                return self.right.predict(sample)