import math

class E_BST_root:
    def __init__(self, stat=[0,0,0], data=None, left=None, right=None):
        self.__NTotal = 0
        self.__SigmayTotal = 0
        self.__Sigmay2Total = 0

        self.stat = stat #[N, Sigma y, Sigma y2] <= split_spot
        self.data = data
        self.left = left
        self.right = right
        return

    def getName(self):
        return self.__class__.__name__

    def add(self, data, y): #update the E-BST using current sample
        self.__NTotal += 1
        self.__SigmayTotal += y
        self.__Sigmay2Total += y * y

        if (self.left == None) & (self.right == None): #root or leaf node
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
                        self.left = E_BST_other(stat=[0,0,0])
                        self.left.add(data, y)
                else:
                    self.right = E_BST_other(stat=[0,0,0])
                    self.right.add(data, y)
        else: #internal
            if data <= self.data:
                if self.left == None:
                    self.left = E_BST_other(stat=[0,0,0])
                    self.left.add(data, y)
                else:
                    if data != self.data:
                        self.left.add(data, y)
                self.stat[0] += 1
                self.stat[1] += y
                self.stat[2] += y * y
            else:
                if self.right == None:
                    self.right = E_BST_other(stat=[0,0,0])
                    self.right.add(data, y)
                else:
                    if data != self.data:
                        self.right.add(data, y)
        return

    def computeSDR(self): #find the best split for the current E-BST and return [SDR, split]
        maxSDR = -1
        split_spot = -1
        leftTotal_opt = -1
        leftSigmayTotal_opt = -1
        leftTotal = 0
        leftSigmayTotal = 0
        leftSigmay2Total = 0
        if self.left != None:
            [maxSDR, split_spot, leftTotal_opt, leftSigmayTotal_opt, self.__NTotal, self.__SigmayTotal, self.__Sigmay2Total, leftTotal, leftSigmayTotal, leftSigmay2Total]\
                = self.left.computeSDR(maxSDR, split_spot, leftTotal_opt, leftSigmayTotal_opt, self.__NTotal, self.__SigmayTotal, self.__Sigmay2Total, leftTotal, leftSigmayTotal, leftSigmay2Total)
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
            split_spot = self.data
            leftTotal_opt = leftTotal
            leftSigmayTotal_opt = leftSigmayTotal
        if self.right != None:
            [maxSDR, split_spot, leftTotal_opt, leftSigmayTotal_opt, self.__NTotal, self.__SigmayTotal, self.__Sigmay2Total, leftTotal, leftSigmayTotal, leftSigmay2Total]\
                = self.right.computeSDR(maxSDR, split_spot, leftTotal_opt, leftSigmayTotal_opt, self.__NTotal, self.__SigmayTotal, self.__Sigmay2Total, leftTotal, leftSigmayTotal, leftSigmay2Total)
        leftTotal -= self.stat[0]
        leftSigmayTotal -= self.stat[1]
        leftSigmay2Total -= self.stat[2]
        if maxSDR < SDR:
            maxSDR = SDR
            split_spot = self.data
            leftTotal_opt = leftTotal
            leftSigmayTotal_opt = leftSigmayTotal
        return [maxSDR, split_spot, leftTotal_opt, leftSigmayTotal_opt]

    def sd(self, total, sigmay, sigmay2):
        if total == 0:
            return 0
        else:
            if abs(sigmay2 - sigmay * sigmay / total) < 0.01:
                return 0
            else:
                return math.sqrt((sigmay2 - sigmay * sigmay / total) / total)

class E_BST_other:
    def __init__(self, stat=[0,0,0], data=None, left=None, right=None):
        self.__stat = stat #[N, Sigma y, Sigma y2]
        self.data = data
        self.left = left
        self.right = right
        return

    def add(self, data, y): #update the E-BST using current sample
        if (self.left == None) & (self.right == None): #root or leaf node
            if self.data == None: #root
                self.data = data
                self.__stat[0] += 1
                self.__stat[1] += y
                self.__stat[2] += y * y
            else:
                if data <= self.data:

                    if data != self.data:
                        self.left = E_BST_other(stat=[0,0,0])
                        #self.right = E_BST_other()
                        self.left.add(data, y)
                    self.__stat[0] += 1
                    self.__stat[1] += y
                    self.__stat[2] += y * y
                else:

                    self.right = E_BST_other(stat=[0,0,0])
                    #self.left = E_BST_other()
                    self.right.add(data, y)
        else: #internal
            if data <= self.data:
                if self.left == None:

                    self.left = E_BST_other(stat=[0,0,0])
                    self.left.add(data, y)
                else:

                    if data != self.data:
                        self.left.add(data, y)
                self.__stat[0] += 1
                self.__stat[1] += y
                self.__stat[2] += y * y
            else:
                if self.right == None:

                    self.right = E_BST_other(stat=[0,0,0])
                    self.right.add(data, y)
                else:

                    if data != self.data:
                        self.right.add(data, y)
        return

    def computeSDR(self, maxSDR, split_spot, leftTotal_opt, leftSigmayTotal_opt, NTotal, SigmayTotal, Sigmay2Total, leftTotal, leftSigmayTotal, leftSigmay2Total): #find the best split for the current E-BST and return [SDR, split]
        if self.left != None:
            [maxSDR, split_spot, leftTotal_opt, leftSigmayTotal_opt, NTotal, SigmayTotal, Sigmay2Total, leftTotal, leftSigmayTotal, leftSigmay2Total]\
                = self.left.computeSDR(maxSDR, split_spot, leftTotal_opt, leftSigmayTotal_opt, NTotal, SigmayTotal, Sigmay2Total, leftTotal, leftSigmayTotal, leftSigmay2Total)
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
            split_spot = self.data
            leftTotal_opt = leftTotal
            leftSigmayTotal_opt = leftSigmayTotal
        if self.right != None:
            [maxSDR, split_spot, leftTotal_opt, leftSigmayTotal_opt, NTotal, SigmayTotal, Sigmay2Total, leftTotal, leftSigmayTotal, leftSigmay2Total]\
                = self.right.computeSDR(maxSDR, split_spot, leftTotal_opt, leftSigmayTotal_opt, NTotal, SigmayTotal, Sigmay2Total, leftTotal, leftSigmayTotal, leftSigmay2Total)
        leftTotal -= self.__stat[0]
        leftSigmayTotal -= self.__stat[1]
        leftSigmay2Total -= self.__stat[2]
        if maxSDR < SDR:
            maxSDR = SDR
            split_spot = self.data
            leftTotal_opt = leftTotal
            leftSigmayTotal_opt = leftSigmayTotal
        #return [maxSDR, splitPoint]
        return [maxSDR, split_spot, leftTotal_opt, leftSigmayTotal_opt, NTotal, SigmayTotal, Sigmay2Total, leftTotal, leftSigmayTotal, leftSigmay2Total]

    def sd(self, total, sigmay, sigmay2):
        if total == 0:
            return 0
        else:
            if abs(sigmay2 - sigmay * sigmay / total) < 0.01:
                return 0
            else:
                return math.sqrt((sigmay2 - sigmay * sigmay / total) / total)

class HoeffdingTree:
    delta = 0.1
    Nmin = 100
    tau = 0.1
    def __init__(self, stat=[0,0], attr_num=None, left=None, right=None, resPredict=None,
                attr_type='con', split_dis=None, split_con=None, attr_ind=None, counter=0, attr_tree = []):
        self.stat = stat #(N, Sigma y)
        self.resPredict = resPredict
        self.left = left
        self.right = right
        #self.node_type = node_type #root internal leaf
        self.attr_type = attr_type #discrete continuous
        self.split_dis = split_dis
        self.split_con = split_con #current version not included
        self.attr_ind = attr_ind
        self.counter = 0 #num_of_nodes in Nmin each period
        self.__attr_tree = []
        for x in range (0, attr_num):
            root_node = E_BST_root(stat=[0,0,0])
            self.__attr_tree.append(root_node)
        #for x in range (0, attr_num):
        #    print("current attr_tree = "+str(x)+str(self.attr_tree[x]))
        return

    def train(self, sample):
        LNode = self.update(sample) #return the leaf node where the sample lies in
        # for x in range (0, len(sample)-1):
        #     print(str(x)+str(LNode.__attr_tree[x].stat))
        if LNode.counter == self.Nmin:
            LNode.counter = 0
            LNode.resPredict = LNode.stat[1]/LNode.stat[0]
            LNode.stat = [0,0]
            curMax = -1
            attr1 = -1 #attr index with the highest SDR
            attr2 = -1 #attr index with the second highest SDR
            split_spot = None
            SDR_list = []
            for x in range (0, len(sample)-1): #find the best split of each attribute
                [SDR, split, leftTotal, leftSigmayTotal] = LNode.__attr_tree[x].computeSDR() #return the best split with (SDR, split_spot)
                SDR_list.append(SDR)
                #split_list.append(split)
                if SDR > curMax:
                    curMax = SDR
                    if attr1 == -1 & attr2 == -1:
                        attr1 = x
                        attr2 = x
                    else:
                        attr2 = attr1
                        attr1 = x
                    split_spot = split
            epsilon = math.sqrt(math.log(1/self.delta)/(2*self.Nmin))
            if SDR_list[attr1]/SDR_list[attr2]+epsilon < 1: #criterion_is_satisfied
                LNode.split(attr1, split_spot, sample, leftSigmayTotal/leftTotal, (LNode.stat[1]-leftSigmayTotal)/(LNode.stat[0]-leftTotal))
            elif epsilon < self.tau: #tie -> either is okay
                LNode.split(attr1, split_spot, sample, leftSigmayTotal/leftTotal, (LNode.stat[1]-leftSigmayTotal)/(LNode.stat[0]-leftTotal))
            #reset E-BST for each node
            for x in range (0, len(sample)-1):
                LNode.__attr_tree[x] = E_BST_root(stat=[0,0,0])
        return

    def update(self, sample): #traverse the tree till the leaf node where the sample lies in, return the leaf node
        if (self.left == None) & (self.right == None): #initilized root or leaf node
            for x in range (0, len(sample)-1):
                # print(self.__attr_tree[x].getName())
                # print("current attr_tree before add = "+str(x)+str(self.__attr_tree[x].stat))
                self.__attr_tree[x].add(float(sample[x]), float(sample[-1]))
                # print("current attr_tree after add = "+str(x)+str(self.__attr_tree[x].stat))
            self.counter += 1
            self.stat[0] += 1
            self.stat[1] += float(sample[-1])
            return self
        #else if self.attr_type == 'dis': # internal node
        elif self.attr_type == 'con':
            if sample[self.attr_ind] <= self.split_con: #left node
                return self.left.update(sample)
            else: #right node
                return self.right.update(sample)

    def split(self, attr, split_spot, sample, leftPredict, rightPredict): #split the current leaf node
        self.left = HoeffdingTree(len(sample)-1, resPredict=leftPredict)
        self.right = HoeffdingTree(len(sample)-1, resPredict=rightPredict)
        self.attr_type = 'con'
        self.split_con = split_spot
        self.attr_ind = attr
        for x in range(0, len(sample)-1):
            self.__attr_tree[x] = None
        return

    def predict(self, sample):
        if (self.left == None) & (self.right == None):
            return self.resPredict
        #elif self.attr_type == 'dis':
        elif self.attr_type == 'con':
            if sample[self.attr_ind] <= self.split_con:
                return self.left.predict(sample)
            elif sample[self.attr_ind] > self.split_con:
                return self.right.predict(sample)