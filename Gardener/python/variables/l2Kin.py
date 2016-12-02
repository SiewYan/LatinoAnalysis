#
#
#     | ___ \   |  / _)        
#     |    ) |  ' /   |  __ \  
#     |   __/   . \   |  |   | 
#    _| _____| _|\_\ _| _|  _| 
#                                                         
#
#


from LatinoAnalysis.Gardener.gardening import TreeCloner
import numpy
import ROOT
import math
import sys
import optparse
import re
import warnings
import os.path
from collections import OrderedDict
from array import array;

class L2KinFiller(TreeCloner):
    def __init__(self):
       pass

    def help(self):
        return '''Calculate kinematic variables, event base and not single object based. They are all simple float variables like mll, dphill, ... '''

    def addOptions(self,parser):
        description = self.help()
        group = optparse.OptionGroup(parser,self.label, description)
        group.add_option('-c', '--cmssw', dest='cmssw', help='cmssw version (naming convention may change)', default='763', type='string')
        parser.add_option_group(group)
        return group

    def checkOptions(self,opts):

        self.cmssw = opts.cmssw
        print " cmssw = ", self.cmssw

                    
    def process(self,**kwargs):
        tree  = kwargs['tree']
        input = kwargs['input']
        output = kwargs['output']

        # does that work so easily and give new variable itree and otree?
        self.connect(tree,input)

        nentries = self.itree.GetEntries()
        print 'Total number of entries: ',nentries 
        savedentries = 0

        #
        # create branches for otree, the ones that will be modified!
        # These variables NEED to be defined as functions in WWVar.C
        # e.g. mll, dphill, ...
        # if you add a new variable here, be sure it IS defined in WWVar.C
        #
        self.namesOldBranchesToBeModifiedSimpleVariable = [
           'mll',
           'dphill',
           'yll',
           'ptll',
           'pt1',
           'pt2',
           'mth',
           'mcoll',
           'mcollWW',
           'mTi',
           'mTe',
	   'choiMass',
	   'mR',
           'channel',


           'drll',
           'dphilljet',
           'dphilljetjet',
           'dphillmet',
           'dphilmet',
           'dphilmet1',
           'dphilmet2',
           'mtw1',
           'mtw2',
           
           'mjj',
           'detajj',
           'njet',
           
           'mllThird',
           'mllOneThree',
           'mllTwoThree',
           'drllOneThree',
           'drllTwoThree',
           
           'dphijet1met',  
           'dphijet2met',  
           'dphijjmet',    
           'dphilep1jet1', 
           'dphilep1jet2', 
           'dphilep2jet1', 
           'dphilep2jet2', 
           
           'ht',
           'vht_pt',
           'vht_phi',
           
           'projpfmet',
           'dphiltkmet',
           'projtkmet',
           'mpmet',
           
           'pTWW',

           'recoil',
           'jetpt1_cut',
           'dphilljet_cut',
           'dphijet1met_cut',
           'PfMetDivSumMet',
           'upara',
           'uperp',
           'm2ljj20',
           'm2ljj30'

           
           ]
        
        # clone the tree
        self.clone(output, self.namesOldBranchesToBeModifiedSimpleVariable)

        self.oldBranchesToBeModifiedSimpleVariable = {}
        for bname in self.namesOldBranchesToBeModifiedSimpleVariable:
          bvariable = numpy.ones(1, dtype=numpy.float32)
          self.oldBranchesToBeModifiedSimpleVariable[bname] = bvariable

        # now actually connect the branches
        for bname, bvariable in self.oldBranchesToBeModifiedSimpleVariable.iteritems():
            #print " bname   = ", bname
            #print " bvariable = ", bvariable
            self.otree.Branch(bname,bvariable,bname+'/F')

        # input tree and output tree
        itree     = self.itree
        otree     = self.otree


        # change this part into correct path structure... 
        cmssw_base = os.getenv('CMSSW_BASE')
        try:
            ROOT.gROOT.LoadMacro(cmssw_base+'/src/LatinoAnalysis/Gardener/python/variables/WWVar.C+g')
        except RuntimeError:
            ROOT.gROOT.LoadMacro(cmssw_base+'/src/LatinoAnalysis/Gardener/python/variables/WWVar.C++g')


        #----------------------------------------------------------------------------------------------------
        print '- Starting eventloop'
        step = 5000

        #for i in xrange(2000):
        for i in xrange(nentries):

            itree.GetEntry(i)

            if i > 0 and i%step == 0.:
                print i,'events processed :: ', nentries

            pt1  = itree.std_vector_lepton_pt[0]
            pt2  = itree.std_vector_lepton_pt[1]
            phi1 = itree.std_vector_lepton_pt[0]
            phi2 = itree.std_vector_lepton_pt[1]
            eta1 = itree.std_vector_lepton_eta[0]
            eta2 = itree.std_vector_lepton_eta[1]

            if self.cmssw == '74x' :
  
              met = itree.pfType1Met          # formerly pfType1Met
              metphi = itree.pfType1Metphi    # formerly pfType1Metphi
              metsum = 0.1 
 
            else : 
              met    = itree.metPfType1
              metphi = itree.metPfType1Phi
              metsum = itree.metPfType1SumEt

            jetpt1   = itree.std_vector_jet_pt[0]
            jetpt2   = itree.std_vector_jet_pt[1]
            jeteta1  = itree.std_vector_jet_eta[0]
            jeteta2  = itree.std_vector_jet_eta[1]
            jetphi1  = itree.std_vector_jet_phi[0]
            jetphi2  = itree.std_vector_jet_phi[1]
            jetmass1 = itree.std_vector_jet_mass[0]
            jetmass2 = itree.std_vector_jet_mass[1]

            WW = ROOT.WW(pt1, pt2, eta1, eta2, phi1, phi2, met, metphi, metsum, jetpt1, jetpt2, jeteta1, jeteta2, jetphi1, jetphi2, jetmass1, jetmass2)
 
            # now fill the variables like "mll", "dphill", ...
            for bname, bvariable in self.oldBranchesToBeModifiedSimpleVariable.iteritems():
              bvariable[0] = getattr(WW, bname)()
              
            otree.Fill()
            savedentries+=1

        self.disconnect()
        print '- Eventloop completed'
        print '   Saved: ', savedentries, ' events'


