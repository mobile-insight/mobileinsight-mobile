from hoeffding import HoeffdingTree
from hoeffding import E_BST_root
from hoeffding import E_BST_other
import math

file = open("../skype-regression-train.txt", 'r')
line = file.readline()
regress_tree = HoeffdingTree(attr_num=4)
while line:
    sample = []
    list = line.split('\t')
    #print(list)
    lastWord = list[-1]
    if lastWord[-1] == '\n':
        if lastWord[:-1] == 'NaN':
            line = file.readline()
            continue
    else:
        if lastWord == 'NaN':
            line = file.readline()
            continue

    for word in list:
        if word[-1] == '\n':
            sample.append(word[:-1])
        else:
            sample.append(word)

    regress_tree.train(sample)
    line = file.readline()

file.close()
#print(sample)
file = open("../skype-regression-test.txt", 'r')
line = file.readline()
while line:
    sample = []
    list = line.split('\t')
    lastWord = list[-1]
    if lastWord[-1] == '\n':
        if lastWord[:-1] == 'NaN':
            line = file.readline()
            continue
    else:
        if lastWord == 'NaN':
            line = file.readline()
            continue

    for word in list:
        if word[-1] == '\n':
            sample.append(word[:-1])
        else:
            sample.append(word)

    predict = regress_tree.predict(sample)
    err = predict - float(sample[-1])
    print(str(err) + " ")
    line = file.readline()

file.close()


