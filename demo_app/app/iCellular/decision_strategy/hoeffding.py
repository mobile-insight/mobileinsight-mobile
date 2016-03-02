import math
# from cart import CARTNode

class E_BST_Root:
    def __init__(self, stat = [0, 0, 0], data = None, left = None, right = None):
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
                        self.left = E_BST_Other(stat = [0, 0, 0])
                        self.left.add(data, y)
                else:
                    self.right = E_BST_Other(stat = [0, 0, 0])
                    self.right.add(data, y)
        else: #internal
            if data <= self.data:
                if self.left == None:
                    self.left = E_BST_Other(stat = [0, 0, 0])
                    self.left.add(data, y)
                else:
                    if data != self.data:
                        self.left.add(data, y)
                self.stat[0] += 1
                self.stat[1] += y
                self.stat[2] += y * y
            else:
                if self.right == None:
                    self.right = E_BST_Other(stat = [0, 0, 0])
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
            [maxSDR, splitSpot, leftTotalOpt, leftSigmayTotalOpt, leftTotal, leftSigmayTotal, leftSigmay2Total] \
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
    def __init__(self, stat = [0, 0, 0], data = None, left = None, right = None):
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
                        self.left = E_BST_Other(stat = [0, 0, 0])
                        self.left.add(data, y)
                    self.__stat[0] += 1
                    self.__stat[1] += y
                    self.__stat[2] += y * y
                else:
                    self.right = E_BST_Other(stat = [0, 0, 0])
                    self.right.add(data, y)
        else: # internal
            if data <= self.data:
                if self.left == None:
                    self.left = E_BST_Other(stat = [0, 0, 0])
                    self.left.add(data, y)
                else:
                    if data != self.data:
                        self.left.add(data, y)
                self.__stat[0] += 1
                self.__stat[1] += y
                self.__stat[2] += y * y
            else:
                if self.right == None:
                    self.right = E_BST_Other(stat = [0, 0, 0])
                    self.right.add(data, y)
                else:
                    self.right.add(data, y)
        return

    def computeSDR(self, maxSDR, splitSpot, leftTotalOpt, leftSigmayTotalOpt, NTotal, SigmayTotal, Sigmay2Total, leftTotal, leftSigmayTotal, leftSigmay2Total): # find the best split for the current E-BST and return [SDR, split]
        if self.left != None:
            [maxSDR, splitSpot, leftTotalOpt, leftSigmayTotalOpt, leftTotal, leftSigmayTotal, leftSigmay2Total] \
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
            [maxSDR, splitSpot, leftTotalOpt, leftSigmayTotalOpt, leftTotal, leftSigmayTotal, leftSigmay2Total] \
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
    N_MIN = 30 # default 200
    TAU = 0.05
    # change adaption
    T_MIN = 20 # default 150
    ALPHA = 0.005
    LAMBDA = 50
    MONITOR = 10 * N_MIN
    F = 0.995
    def __init__(self, stat = [0, 0], resPredict = None, left = None, right = None, attrNum = None,
                attrType = 'con', splitDis = None, splitCon = None, attrInd = None, counterN = 0, counterT = 0, counterG = 0,
                PHStat = [0, 0, 0], altTree = None, sErr = 0, grow = 'false', lastQi = 1):
        self.stat = stat #(N, Sigma y)
        self.resPredict = resPredict
        self.left = left
        self.right = right
        self.attrNum = attrNum
        self.attrType = attrType # discrete/continuous
        self.splitDis = splitDis # current version not included
        self.splitCon = splitCon
        self.attrInd = attrInd
        self.counterN = counterN # #samples in each period (T = Nmin)
        self.counterT = counterT # #samples in each period (T = Tmin)
        self.counterG = counterG # #samples from the initial of sub tree
        self.PHStat = PHStat # mT xT MT
        self.altTree = altTree
        self.sErr = sErr
        self.grow = grow
        self.lastQi = lastQi
        self.__attrTree = []
        for x in range (0, attrNum):
            rootNode = E_BST_Root(stat = [0,0,0])
            self.__attrTree.append(rootNode)
        return

    def getDepth(self):
        if (self.left == None) & (self.right == None):
            return 1
        depthLeft = 0
        depthRight = 0
        if self.left != None:
            depthLeft = self.left.getDepth() + 1
        if self.right != None:
            depthRight = self.right.getDepth() + 1
        return max(depthLeft, depthRight)

    def getNodeNum(self):
        if (self.left == None) & (self.right == None):
            return 1
        nodeNumLeft = 0
        nodeNumRight = 0
        if self.left != None:
            nodeNumLeft = self.left.getNodeNum()
        if self.right != None:
            nodeNumRight = self.right.getNodeNum()
        return nodeNumLeft + nodeNumRight + 1

    # def importCART(self, CARTNode):
    #     if CARTNode.L == None & CARTNode.R == None: # leaf node
    #         self.resPredict = CARTNode.M # to be added
    #         return
    #     else: # internal of root node
    #         self.attrInd = CARTNode.V - 1
    #         self.splitType = 'con'
    #         self.splitCon = CARTNode.S
    #     if CARTNode.L != None:
    #         self.left = HoeffdingTree(stat = [0, 0])
    #         self.left.importCART(CARTNode.L)
    #     if CARTNode.R != None:
    #         self.right = HoeffdingTree(stat = [0, 0])
    #         self.right.importCART(CARTNode.R)
    #     return
    
    def importTree(self, treeNode):
         self.resPredict = treeNode["M"]
         if treeNode.has_key('V'):
             self.left = HoeffdingTree(attrNum = 4)
             self.left.importTree(treeNode["L"])
             self.right = HoeffdingTree(attrNum = 4)
             self.right.importTree(treeNode["R"])
             self.attrType = 'con'
             self.splitCon = treeNode["S"]
             self.attrInd = treeNode["V"]

    def train(self, sample):
        self.update(sample)
        return

    def update(self, sample): # traverse the tree till the leaf node where the sample lies in, return the leaf node
        if (self.left == None) & (self.right == None): # initilized root or leaf node
            for x in range (0, len(sample)-1):
                self.__attrTree[x].add(float(sample[x]), float(sample[-1]))
            self.counterN += 1
            self.counterT += 1
            self.counterG += 1
            self.stat[0] += 1
            self.stat[1] += float(sample[-1])
            # split
            if self.counterN == self.N_MIN:
                self.counterN = 0
                self.resPredict = self.stat[1] / self.stat[0]
                curMax = -1
                attr1 = -1 # attr index with the highest SDR
                attr2 = -1 # attr index with the second highest SDR
                splitSpot = None
                SDRList = []
                for x in range (0, len(sample)-1): # find the best split of each attribute
                    [SDR, split, leftTotal, leftSigmayTotal] = self.__attrTree[x].computeSDR() #return the best split
                    SDRList.append(SDR)
                    if SDR > curMax:
                        curMax = SDR
                        if attr1 == -1:
                            attr1 = x
                            # attr2 = x
                        else:
                            attr2 = attr1
                            attr1 = x
                        splitSpot = split
                    else:
                        if attr2 == -1:
                            attr2 = x
                        else:
                            if SDR > SDRList[attr2]:
                                attr2 = x
                epsilon = math.sqrt(math.log(1 / self.DELTA) / (2 * self.N_MIN))
                if SDRList[attr2] / SDRList[attr1] + epsilon < 1: # criterion_is_satisfied
                    self.split(attr1, splitSpot, sample, leftSigmayTotal / leftTotal, (self.stat[1] - leftSigmayTotal) / (self.stat[0] - leftTotal))
                elif SDRList[attr2] / SDRList[attr1] + self.TAU >= 1: # tie -> either is okay
                    self.split(attr1, splitSpot, sample, leftSigmayTotal / leftTotal, (self.stat[1] - leftSigmayTotal) / (self.stat[0] - leftTotal))
                # reset E-BST for each node
                self.stat = [0,0]
                for x in range (0, len(sample)-1):
                    self.__attrTree[x] = E_BST_Root(stat = [0,0,0])
            ######
            adapt = 0 # default no action
            if self.resPredict != None:
                absErr = abs(float(sample[-1]) - self.resPredict)
            else:
                absErr = float(0)
            if self.grow == 'false':
                PHres = self.PHTest(absErr)
                if PHres == 1:
                    self.grow = 'true'
                    self.altTree = HoeffdingTree(attrNum = len(sample) - 1)
                    self.altTree.subUpdate(sample)
                    adapt = self.adaptTest(absErr, sample)
            else:
                self.altTree.subUpdate(sample)
                adapt = self.adaptTest(absErr, sample)
            return [adapt, absErr]
        #elif self.attr_type == 'dis': # internal node
        elif self.attrType == 'con':
            self.counterT += 1
            self.counterG += 1
            adapt = 0
            if float(sample[self.attrInd]) <= self.splitCon: #left node
                [adaptPre, absErr] = self.left.update(sample)
                if adaptPre == 1:
                    self.left = self.left.altTree
                    self.left.grow = 'false'
                elif adaptPre == -1:
                    self.left.altTree = None
                    self.left.grow = 'false'
            else: #right node
                [adaptPre, absErr] = self.right.update(sample)
                if adaptPre == 1:
                    self.right = self.right.altTree
                    self.right.grow = 'false'
                elif adaptPre == -1:
                    self.right.altTree = None
                    self.right.grow = 'false'
            if self.grow == 'false':
                PHres = self.PHTest(absErr)
                if PHres == 1:
                    self.grow = 'true'
                    self.altTree = HoeffdingTree(attrNum = len(sample) - 1)
                    self.altTree.subUpdate(sample)
                    adapt = self.adaptTest(absErr, sample)
            else:
                self.altTree.subUpdate(sample)
                adapt = self.adaptTest(absErr, sample)
            return [adapt, absErr]

    def PHTest(self, err):
        self.PHStat[1] = (self.PHStat[1] * (self.counterT - 1) + err) / self.counterT
        self.PHStat[0] += err - self.PHStat[1] - self.ALPHA
        if self.counterT == 1:
            self.PHStat[2] = self.PHStat[0]
        else:
            if self.PHStat[0] < self.PHStat[2]:
                self.PHStat[2] = self.PHStat[0]
        PHT = self.PHStat[0] - self.PHStat[2]
        if self.counterT == self.T_MIN:
            self.counterT = 0
            self.PHStat = [0, 0, 0]
        if PHT > self.LAMBDA:
            return 1 # adapt
        else:
            return 0

    # The function is executed every Tmin nodes. It updates the Qi statistic to decide whether or not replace the original tree.
    # When counterT < 10N_MIN, the ori tree will be replaced when Qi > 0
    # When counterT >= 10N_MIN, the ori tree will de replaced when Qi > 0, be dropped when monitering a decreasing pattern.
    def adaptTest(self, err, sample):
        if self.counterG < 10 * self.N_MIN:
            altPredict = self.altTree.predict(sample)
            if altPredict == None:
                return 0
            lAltTree = pow(abs(float(sample[-1]) - altPredict), 2)
            lOriTree = pow(err, 2)
            if self.counterT == self.T_MIN:
                Qi = math.log((lOriTree + self.F * self.sErr) / (lAltTree + self.altTree.sErr))
                self.sErr = 0
                self.altTree.sErr = 0
                self.counterT = 0
                if Qi > 0:
                    self.counterG = 0
                    return 1 # replace
                else:
                    return 0 # no action
            else:
                self.counterT = self.counterT + 1
                self.sErr += lOriTree
                self.altTree.sErr += lAltTree
                return 0
        else:
            altPredict = self.altTree.predict(sample)
            if altPredict == None:
                return 0
            lAltTree = pow(abs(float(sample[-1]) - altPredict), 2)
            lOriTree = pow(err, 2)
            if self.counterT == self.T_MIN:
                Qi = math.log((lOriTree + self.F * self.sErr) / (lAltTree + self.altTree.sErr))
                self.sErr = 0
                self.altTree.sErr = 0
                self.counterT = 0
                if Qi > 0:
                    self.counterG = 0
                    return 1 # replace
                else:
                    if self.altTree.lastQi > 0:
                        self.altTree.lastQi = Qi
                        return 0
                    else:
                        if Qi < self.altTree.lastQi:
                            self.counterG = 0
                            return -1 # drop
                        else:
                            self.altTree.lastQi = Qi
                            return 0
            else:
                self.counterT = self.counterT + 1
                self.sErr += lOriTree
                self.altTree.sErr += lAltTree
                return 0

    def subUpdate(self, sample): # traverse the tree till the leaf node where the sample lies in, return the leaf node
        if (self.left == None) & (self.right == None): # initilized root or leaf node
            for x in range (0, len(sample)-1):
                self.__attrTree[x].add(float(sample[x]), float(sample[-1]))
            self.counterN += 1
            self.stat[0] += 1
            self.stat[1] += float(sample[-1])
            # split
            if self.counterN == self.N_MIN:
                self.counterN = 0
                self.resPredict = self.stat[1] / self.stat[0]
                curMax = -1
                attr1 = -1 # attr index with the highest SDR
                attr2 = -1 # attr index with the second highest SDR
                splitSpot = None
                SDRList = []
                for x in range (0, len(sample)-1): # find the best split of each attribute
                    [SDR, split, leftTotal, leftSigmayTotal] = self.__attrTree[x].computeSDR() #return the best split
                    SDRList.append(SDR)
                    if SDR > curMax:
                        curMax = SDR
                        if attr1 == -1:
                            attr1 = x
                            # attr2 = x
                        else:
                            attr2 = attr1
                            attr1 = x
                        splitSpot = split
                    else:
                        if attr2 == -1:
                            attr2 = x
                        else:
                            if SDR > SDRList[attr2]:
                                attr2 = x
                epsilon = math.sqrt(math.log(1 / self.DELTA) / (2 * self.N_MIN))
                if SDRList[attr2] / SDRList[attr1] + epsilon < 1: # criterion_is_satisfied
                    self.split(attr1, splitSpot, sample, leftSigmayTotal / leftTotal, (self.stat[1] - leftSigmayTotal) / (self.stat[0] - leftTotal))
                elif SDRList[attr2] / SDRList[attr1] + self.TAU >= 1: # tie -> either is okay
                    self.split(attr1, splitSpot, sample, leftSigmayTotal / leftTotal, (self.stat[1] - leftSigmayTotal) / (self.stat[0] - leftTotal))
                # reset E-BST for each node
                self.stat = [0,0]
                for x in range (0, len(sample)-1):
                    self.__attrTree[x] = E_BST_Root(stat = [0,0,0])
            ######
            return
        #elif self.attr_type == 'dis': # internal node
        elif self.attrType == 'con':
            if float(sample[self.attrInd]) <= self.splitCon: #left node
                self.left.subUpdate(sample)
                return
            else: #right node
                self.right.subUpdate(sample)
                return

    def split(self, attr, splitSpot, sample, leftPredict, rightPredict): #split the current leaf node
        self.left = HoeffdingTree(attrNum = len(sample)-1, resPredict = leftPredict)
        self.right = HoeffdingTree(attrNum = len(sample)-1, resPredict = rightPredict)
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
        elif self.attrType == 'con':
            if float(sample[self.attrInd]) <= self.splitCon:
                return self.left.predict(sample)
            elif float(sample[self.attrInd]) > self.splitCon:
                return self.right.predict(sample)