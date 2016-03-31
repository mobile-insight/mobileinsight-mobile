#!/usr/bin/python
# Filename: icellular_strategy_base.py
"""
Base class of decisions strategies.
This defines the common interface for selection decision.

Author: Yuanjie Li
"""
from cart_interface import getTree, predict
from icellular_strategy_base import IcellularStrategyBase
from hoeffding import HoeffdingTree

#import config

class IcellularPredictionStrategy(IcellularStrategyBase):

    def __init__(self):
        print "IcellularStrategyTemp is called"
        IcellularStrategyBase.__init__(self)
        self.fit = getTree()
        self.hoeffdingTree = HoeffdingTree(attrNum = 4)
        self.hoeffdingTree.importTree(self.fit) # import initilized tree
        # self.prediction_metric_type = config.prediction_metric_type

    def selection(self, carrier_network_list):
        """
        Select the target carrier network given the available candidate dict

        :param carrier_network_list: a dict of available carriers
        :returns: the target carrier network, or None if no switch is needed
        """
        best_lantency = 1e10
        best_carrier = None
        try:
            for carrier, data in carrier_network_list.items():
                print "test 1"
                d = [y for x, y in data.items()]
                while (len(d) < 4):
                    d.append(0.0)

                print "test 2", str(d)
                result = self.hoeffdingTree.predict(d)
                print "test 3"
                if result < best_lantency:
                    best_lantency = result
                    best_carrier = carrier
            print 'IcellularStrategyTemp', carrier_network_list, best_carrier
        except Exception as e:
            print "hehehe"
            print e
        return best_carrier

    def training(self,sample):
        """
        Online training sample collection and training.

        Currently this function is for regression tree algorithm only

        :param sample: a sample from serving carrier network
        :type sample: a tuple of (x,y), where x is the feature vector (dictionary), and y is the prediction metric
        """
        #Yuanjie: the following is how you can use this training sample

        
	    
        try:
            #Extract feature vector and prediction metric
            sample_feature = sample.x   # a dictionary of all sample features
            prediction_metric = sample.y

            #learn which type of prediction metric we are using (latency, throughput, etc.)
            #prediction_metric_type = config.prediction_metric_type  #this is a string that indicates the type (defined in config.py)

            #signal_strength = sample_feature['signal_strength']
            #Do your task here
            print  'IcellularStrategyTemp', 'training', sample.x, sample.y
            data = [y for x, y in sample_feature.items()]
            while (len(data) < 4):
                data.append(0.0)
            print "TRAIN_LOG", data + [float(prediction_metric)]
            self.hoeffdingTree.train(data + [float(prediction_metric)])
        except Exception as e:
            print e

if __name__ == '__main__':
    #test = {'att': {'1': 2,'2':-100.8,'3':0,'4': 90},'tmobile':{'1':2, '2':-109.6,'3':0, '4': 99.5 }}
    #tester = IcellularStrategyTemp()
    #tester.training({'x':{'1':2, '2':4, '3':5, '4':6}, 'y':4.3});
    #print tester.selection(test)
    import json
    tester = IcellularPredictionStrategy()
    for line in open('data', 'r'):
       tester.hoeffdingTree.train(json.loads(line))
    tester.training({'x':{'1':2, '2':4, '3':5, '4':6}, 'y':4.3});
    test = {'att': {'1': 2,'2':-100.8,'3':0,'4': 90},'tmobile':{'1':2, '2':-109.6,'3':0, '4': 99.5 }}
    print tester.selection(test)
