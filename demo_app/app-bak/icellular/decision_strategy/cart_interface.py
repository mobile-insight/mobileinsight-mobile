
import json,tree

def getTree():
    return tree.result
    #return json.loads(open('tree.json', 'r').read())

def predict(tree, x):
    if not tree.has_key('V'):
        return tree['M']
    if x[tree['V']] <= 1e-10 + tree['S']:
        return predict(tree['L'], x)
    return predict(tree['R'], x)
