#!/usr/bin/env python

import json
import sys
import ROOT
import optparse
import LatinoAnalysis.Gardener.hwwtools as hwwtools
import logging
import os.path


# Common Tools & batch
from LatinoAnalysis.Tools.commonTools import *
from LatinoAnalysis.Tools.manipDataCard import card as cardTools

def DC2EFT(dc,iDim,iScan,iCut,iVar,datacard_dir_sm,datacard_root_sm,inputFile):


   print '******************* DOING : ',iScan,iCut,iVar

   datacard_dir_ac = datacard_dir_sm+'_'+iScan.replace(":","_")
   datacard_eft_ac = datacard_dir_ac+'/eftparam.txt'
   os.system ("rm -rf "+datacard_dir_ac)
   os.mkdir(datacard_dir_ac)
   f = open(datacard_eft_ac,'w')
  
   # [Global] Section

   f.write('[Global] \n')

   # ... Parameters 
   if iDim == '1D' : f.write('model = par1_TF1\n')
   if iDim == '2D' : f.write('model = par1par2_TF2\n')
   if iDim == '3D' : f.write('model = par1par2par3_TF3\n')
   nParam=0
   for iParam in iScan.split(":"):
     nParam+=1
     operatorValues = sorted(set([x.split(":")[nParam-1] for x in acoupling['Scans'][iDim][iScan].keys()]),key=float)
     operatorValuesFloat = [float(x) for x in operatorValues] 
     idxSM  = operatorValuesFloat.index(0.)
     binWOp = operatorValuesFloat[idxSM+1]-operatorValuesFloat[idxSM]
     nBinOp = len(operatorValuesFloat)
     xMinOp = operatorValuesFloat[0]-binWOp/2.
     xMaxOp = operatorValuesFloat[nBinOp-1]+binWOp/2.
     f.write('par'+str(nParam)+'Name = ' + iParam + '\n')
     f.write('par'+str(nParam)+'Low  = ' + str(xMinOp) + '\n')
     f.write('par'+str(nParam)+'High = ' + str(xMaxOp) + '\n')
     f.write('par'+str(nParam)+'PlotName = ' + acoupling['operatorLatex'][iParam] + '\n')

   # ... Path
   f.write('basepath = ./ \n')
   f.write('\n')

   # ... Find Signal and Backgrounds
   iPos=0
   Nbkg=0
   BkgNames=[]
   BkgPos=[]
   Nsig=0
   SigName=''
   for iProc in dc.content['block2']['processId']:
     if float(iProc)>0: 
        if 'Higgs' not in dc.content['block2']['process'][iPos]:
           Nbkg+=1
           BkgNames.append(dc.content['block2']['process'][iPos])
           BkgPos.append(iPos)
     else: 
        Nsig+=1
        SigName=dc.content['block2']['process'][iPos]
        SigPos=iPos
     iPos+=1
   
   # ... Find Histograms
   for iDesc in dc.content['header2']:
     if dc.content['header2'][iDesc][1] == 'data_obs' :
       DataFile=dc.content['header2'][iDesc][3]
       DataHist=dc.content['header2'][iDesc][4]
   #  if dc.content['header2'][iDesc][1] == '*' and dc.content['header2'][iDesc][2] == '*' :
     if dc.content['header2'][iDesc][1] == '*' and '.root' in dc.content['header2'][iDesc][3] :
       MCFile=dc.content['header2'][iDesc][3]
       MCHist = dc.content['header2'][iDesc][4]
       if len(dc.content['header2'][iDesc]) == 6 : MCHisSyst = dc.content['header2'][iDesc][5]
       else: MCHisSyst ='None'
   
   print DataFile, DataHist
   print MCFile  , MCHist , MCHisSyst
   print 'Backgrounds= ',BkgNames
   print 'Signal     = ',SigName

   # ... lnN systematics
   if 'lnN' in dc.content['systs']:
     NlnN = len(dc.content['systs']['lnN'])
     f.write('NlnN = ' + str(NlnN) + '\n')
     counter = 1
     #print dc.content['systs']
     #print NlnN
     for systName,systVal in dc.content['systs']['lnN'].items():
       f.write('lnN'+ str(counter) + '_name = ' + systName + '\n')
       # get non-zero names and values
       syst = [[ systVal[i],dc.content['block2']['process'][i] ] for i in range(len(systVal)) if systVal[i] != '-' and 'Higgs' not in dc.content['block2']['process'][i] ]
       #print syst
       f.write('lnN'+ str(counter) + '_value = ')
       for j,s in enumerate(syst) :
         if j != 0 : 
           f.write(',')
         f.write(s[0])
       f.write('\n')
       
       f.write('lnN'+ str(counter) + '_for = ')
       for j,s in enumerate(syst) :
         if j != 0 : 
           f.write(',')
         if s[1] == SigName :
           f.write(iCut + '_signal')
         else :
           f.write(iCut + '_background_' + s[1])  
       f.write('\n')
       
       counter+=1
   else:
     f.write('NlnN = 0\n')

   # [iCut] Section
   f.write('\n')
   f.write('['+iCut+']\n')
   
   # ... Find Signal and Backgrounds
   f.write('Nbkg='+str(Nbkg)+'\n')
   
   # ... Signal Name
   f.write('sm_name='+SigName+' \n')
   # ... Data Name
   f.write('data_name=data_obs \n') 

   # Signal shape syst
   SYST=[]
   for iSystType in dc.content['systs']: 
     if 'shape' in iSystType:
       for iSyst in dc.content['systs'][iSystType]:
         if not dc.content['systs'][iSystType][iSyst][SigPos] == '-' :
           SYST.append('signal_'+SigName+'_'+iSyst)
   if len(SYST)>0 :
     f.write('signal_shape_syst=')  
     for i in range (0,len(SYST)) : 
       f.write(SYST[i])
       if i < len(SYST)-1 : f.write(',')
     f.write('\n')
   
   # Bkgd Shape syst
   for iBkg in range(0,len(BkgPos)) : 
     iPos=BkgPos[iBkg]
     SYST=[]
     for iSystType in dc.content['systs']:
       if 'shape' in iSystType:
         for iSyst in dc.content['systs'][iSystType]:
           if not dc.content['systs'][iSystType][iSyst][iPos] == '-' :
             SYST.append('background_'+BkgNames[iBkg]+'_'+iSyst)
     f.write('bkg'+str(iBkg+1)+'_name=background_'+BkgNames[iBkg]+'\n')
     if len(SYST)>0 :
       f.write('bkg'+str(iBkg+1)+'_shape_syst=')
       for i in range (0,len(SYST)) :
         f.write(SYST[i])
         if i < len(SYST)-1 : f.write(',')
       f.write('\n')

   f.write('NSigBkg_corr_unc = 0 \n')

   # Close TEXT file 
   f.close()

   # AND NOW HISTOGRAMS
   rootFile = os.path.dirname(datacard_eft_ac) + '/' + iCut + '.root' # necessary for EFT framework
   print 'RootFile  : ',rootFile 
   fOut = ROOT.TFile.Open(rootFile,'RECREATE')

   # ... Data
   fIn = ROOT.TFile.Open(datacard_dir_sm+'/'+DataFile,'READ')
   fOut.cd()
   hTmp = fIn.Get(DataHist).Clone("data_obs")
   hTmp.Write()
   fIn.Close()

   # ... Signal
   fIn = ROOT.TFile.Open(datacard_dir_sm+'/'+MCFile,'READ')
   fOut.cd()
   hTmp = fIn.Get(MCHist.replace('$PROCESS',SigName)).Clone(SigName)
   hTmp.SetName('diboson')
   hTmp.Write()
   for iSystType in dc.content['systs']:
     if 'shape' in iSystType:
       for iSyst in dc.content['systs'][iSystType]:
         if not dc.content['systs'][iSystType][iSyst][SigPos] == '-' :
           hTmp = fIn.Get(MCHisSyst.replace('$PROCESS',SigName).replace('$SYSTEMATIC',iSyst)+'Up').Clone('signal_'+SigName+'_'+iSyst+'Up')
           hTmp.Write()       
           hTmp = fIn.Get(MCHisSyst.replace('$PROCESS',SigName).replace('$SYSTEMATIC',iSyst)+'Down').Clone('signal_'+SigName+'_'+iSyst+'Down')
           hTmp.Write()       
   fIn.Close()


   # ... Background
   
   fIn = ROOT.TFile.Open(datacard_dir_sm+'/'+MCFile,'READ')
   fOut.cd()
   for iBkg in range(0,len(BkgPos)) :
     iPos=BkgPos[iBkg]
     hTmp = fIn.Get(MCHist.replace('$PROCESS',BkgNames[iBkg])).Clone('background_'+BkgNames[iBkg])
     hTmp.Write()
     for iSystType in dc.content['systs']:
       if 'shape' in iSystType:
         for iSyst in dc.content['systs'][iSystType]:
           if not dc.content['systs'][iSystType][iSyst][iPos] == '-' :
             hTmp = fIn.Get(MCHisSyst.replace('$PROCESS',BkgNames[iBkg]).replace('$SYSTEMATIC',iSyst)+'Up').Clone('background_'+BkgNames[iBkg]+'_'+iSyst+'Up')
             hTmp.Write() 
             hTmp = fIn.Get(MCHisSyst.replace('$PROCESS',BkgNames[iBkg]).replace('$SYSTEMATIC',iSyst)+'Down').Clone('background_'+BkgNames[iBkg]+'_'+iSyst+'Down')
             hTmp.Write() 
   fIn.Close()
   
   # close Files
   fOut.Close()

   ### AND THE SIGNAL PARMAETRISATION
   #print 'RootFile  : ',inputFile
   fIn = ROOT.TFile.Open(inputFile,'READ')

   rootFile = os.path.dirname(datacard_eft_ac) + '/signal_proc_' + iCut + '.root' # necessary for EFT framework
   print 'RootFile  : ',rootFile
   fOut = ROOT.TFile.Open(rootFile,'RECREATE')

   fIn.cd(iCut+'/'+iVar+'/'+iScan) 
   keyList = ROOT.gDirectory.GetListOfKeys()
   fOut.cd() 
   for key in keyList:
     obj = key.ReadObj()
     if 'TF' in  obj.ClassName() : 
      objCopy = obj.Clone()
      objCopy.Write()
  
   # close Files
   fIn.Close()
   fOut.Close()


if __name__ == '__main__':
    print '''
--------------------------------------------------------------------------------------------------
           ___
   / \    / __|  __ \          |                                 |       \  |         |                
  / __\  | |     |   |   _` |  __|   _` |   __|   _` |   __|  _` |      |\/ |   _` |  |  /   _ \   __| 
  ___  | | |__   |   |  (   |  |    (   |  (     (   |  |    (   |      |   |  (   |    <    __/  |    
 |   |_|  \___|  ____/  \__,_| \__| \__,_| \___| \__,_| _|   \__,_|     _|  _| \__,_| _|\_\ \___| _|    
                                                                                
--------------------------------------------------------------------------------------------------
'''

    usage = 'usage: %prog [options]'
    parser = optparse.OptionParser(usage)

    parser.add_option('--tag'            , dest='tag'            , help='Tag used for the shape file name'           , default=None)
    parser.add_option('--inputFile'      , dest='inputFile'      , help='input file with histograms'                 , default='DEFAULT')
    parser.add_option('--outputDirDatacard'  , dest='outputDirDatacard' , help='output directory'                           , default='./')
    parser.add_option('--accfg'          , dest='accfg'          , help='AC coupling dictionary' , default='acoupling.py' , type='string' )
    parser.add_option('--cutList'        , dest='cutList'        , help='cut list to process' , default=[], type='string' , action='callback' , callback=list_maker('cutList',','))
    parser.add_option('--varList'        , dest='varList'        , help='var list to process' , default=[], type='string' , action='callback' , callback=list_maker('varList',','))

    # read default parsing options as well
    hwwtools.addOptions(parser)
    hwwtools.loadOptDefaults(parser)
    (opt, args) = parser.parse_args()

    print " outputDirDatacard  = ", opt.outputDirDatacard
    print " AC config          = ", opt.accfg
    print " Cuts               = ", opt.cutList 
    print " Variables          = ", opt.varList 


    # Set Input file
    print " inputFile      =          ", opt.inputFile


    # Create Needed dictionnary

    variables = {}
    if os.path.exists(opt.variablesFile) :
      handle = open(opt.variablesFile,'r')
      exec(handle)
      handle.close()
    if len(opt.varList)>0:
      var2del=[]
      for iVar in variables:
        if not iVar in opt.varList : var2del.append(iVar)
      for iVar in var2del : del variables[iVar]

    cuts = {}
    if os.path.exists(opt.cutsFile) :
      handle = open(opt.cutsFile,'r')
      exec(handle)
      handle.close()
    if len(opt.cutList)>0:
      cut2del=[]
      for iCut in cuts:
        if not iCut in opt.cutList : cut2del.append(iCut)
      for iCut in cut2del : del cuts[iCut]


    # acoupling = {}     
    h=open(opt.accfg,'r')
    exec(h)

    AC_cmd='python '+os.environ['CMSSW_BASE']+'/src/CombinedEWKAnalysis/CommonTools/test/buildWorkspace_AC.py' 


    for iCut in cuts:
      for iVar in variables:
        datacard_dir_sm  = opt.outputDirDatacard+'/'+iCut+'/'+iVar 
        datacard_txt_sm  = opt.outputDirDatacard+'/'+iCut+'/'+iVar+'/datacard.txt'
        datacard_root_sm = opt.outputDirDatacard+'/'+iCut+'/'+iVar+'/shapes/histos_'+iCut+'.root'
        acoupling_root   = opt.inputFile
        # Open SM data card
        dc=cardTools(datacard_txt_sm)
        # Now loop on AC
        if '1D' in acoupling['ScanConfig'] and len(acoupling['ScanConfig']['1D']) > 0 :
          for iScan in acoupling['Scans']['1D']:
            # Create Inputs
            DC2EFT(dc,'1D',iScan,iCut,iVar,datacard_dir_sm,datacard_root_sm,opt.inputFile)
            # Prepare AC Workspace and datacards
            datacard_dir_ac = datacard_dir_sm+'_'+iScan.replace(":","_")
            datacard_eft_ac = datacard_dir_ac+'/eftparam.txt'
            command=AC_cmd+' --config='+datacard_eft_ac+' --basepath='+datacard_dir_ac
            command+=' ; mv aC_'+iCut+'.txt '+datacard_dir_ac
            command+=' ; mv '+iCut+'_ws.root '+datacard_dir_ac
            os.system(command)
            print command
            # Prepare COMBINE Workspace
            command='cd '+datacard_dir_ac+' ; '  
            command+='text2workspace.py -m 125 aC_'+iCut+'.txt -P CombinedEWKAnalysis.CommonTools.ACModel:par1_TF1_Model \
                      --PO channels='+iCut+' --PO poi='+iScan.replace(":",",")+' --PO basepath=.'
            print iScan , iScan.split(":")
            for iOp in iScan.split(":") : 
              command+=' --PO range_'+iOp+'='+str(acoupling['operatorRange'][iOp][0])+','+str(acoupling['operatorRange'][iOp][1])
            print command
            os.system(command)


 
