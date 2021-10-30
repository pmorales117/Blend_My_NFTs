import bpy
import os
import sys

dir = os.path.dirname(bpy.data.filepath)
sys.path.append(dir)

import itertools
import time
import copy
import re
import json
import importlib

import config
importlib.reload(config)
from config import *

time_start = time.time()

def returnData():
   '''
   Generates important variables, dictionaries, and lists needed to be stored to catalog the NFTs.
   :return: listAllCollections, attributeCollections, attributeCollections1, hierarchy, variantMetaData, possibleCombinations
   '''

   listAllCollections = []
   scriptIgnore = bpy.data.collections["Script_Ignore"]

   for i in bpy.data.collections:
      listAllCollections.append(i.name)

   listAllCollections.remove(scriptIgnore.name)

   def allScriptIgnore(collection):
      '''
      Removes all collections, sub collections in Script_Ignore" collection from listAllCollections.
      '''
      for coll in list(collection.children):
         listAllCollections.remove(coll.name)
         listColl = list(coll.children)
         if len(listColl) > 0:
            allScriptIgnore(coll)
   allScriptIgnore(scriptIgnore)

   exclude = ["_","1","2","3","4","5","6","7","8","9","0"]
   attributeCollections = copy.deepcopy(listAllCollections)

   def filter_num():
      """
      This function removes items from 'attributeCollections' if they include values from the 'exclude' variable.
      It removes child collections from the parent collections in from the "listAllCollections" list.
      """
      for x in attributeCollections:
         if any(a in x for a in exclude):
            attributeCollections.remove(x)

   for i in range(len(listAllCollections)):
       filter_num()

   attributeVariants = [x for x in listAllCollections if x not in attributeCollections]
   attributeCollections1 = copy.deepcopy(attributeCollections)

   def attributeData(attributeVariants):
      '''
      Creates a dictionary of each attribute
      '''
      allAttDataList = {}
      for i in attributeVariants:

         def getName(i):
            '''
            Returns the name of "i" attribute variant
            '''
            name = re.sub(r'[^a-zA-Z]', "", i)
            return name

         def getOrder_rarity(i):
            '''
            Returns the "order" and "rarity" of i attribute variant in a list
            '''
            x = re.sub(r'[a-zA-Z]', "", i)
            a = x.split("_")
            del a[0]
            return list(a)

         name = getName(i)
         orderRarity = getOrder_rarity(i)
         number = orderRarity[0]
         rarity = orderRarity[1]
         eachObject = {"name": name, "number": number, "rarity": rarity}
         allAttDataList[i] = eachObject
      return allAttDataList

   variantMetaData = attributeData(attributeVariants)

   def getHierarchy():
      '''
      Constructs the hierarchy dictionary from attributeCollections1 and variantMetaData.
      '''
      hierarchy = {}
      for i in attributeCollections1:
         colParLong = list(bpy.data.collections[str(i)].children)
         colParShort = {}
         for x in colParLong:
            colParShort[x.name] = None
         hierarchy[i] = colParShort

      for a in hierarchy:
         for b in hierarchy[a]:
            for x in variantMetaData:
               if str(x) == str(b):
                  (hierarchy[a])[b] = variantMetaData[x]

      return hierarchy

   hierarchy = getHierarchy()

   def numOfCombinations(hierarchy):
      '''
      Returns "combinations" the number of all possible NFT combinations.
      '''
      hierarchyByNum = []
      for i in hierarchy:
         hierarchyByNum.append(len(hierarchy[i]))
      combinations = 1
      for i in hierarchyByNum:
         combinations = combinations*i
      return combinations

   possibleCombinations = numOfCombinations(hierarchy)

   for i in variantMetaData:
      def cameraToggle(i,toggle = True):
         bpy.data.collections[i].hide_render = toggle
         bpy.data.collections[i].hide_viewport = toggle
      cameraToggle(i)

   return listAllCollections, attributeCollections, attributeCollections1, hierarchy, possibleCombinations

listAllCollections, attributeCollections, attributeCollections1, hierarchy, possibleCombinations = returnData()

def generateNFT_DNA(possibleCombinations):
   '''
   Returns batchDataDictionary containing the number of NFT cominations, hierarchy, and the DNAList.
   '''
   batchDataDictionary = {}
   listOptionVari = []

   print("-----------------------------------------------------------------------------")
   print("Generating " + str(possibleCombinations) + " combinations of DNA...")
   print("")


   for i in hierarchy:
      numChild = len(hierarchy[i])
      possibleNums = list(range(1, numChild + 1))
      listOptionVari.append(possibleNums)

   allDNAList = list(itertools.product(*listOptionVari))
   allDNAstr = []

   for i in allDNAList:
      dnaStr = ""
      for j in i:
         num = "-" + str(j)
         dnaStr += num

      dna = ''.join(dnaStr.split('-', 1))
      allDNAstr.append(dna)

   #Data stored in batchDataDictionary:
   batchDataDictionary["numNFTsGenerated"] = possibleCombinations
   batchDataDictionary["hierarchy"] = hierarchy
   batchDataDictionary["DNAList"] = allDNAstr
   return batchDataDictionary

DataDictionary = generateNFT_DNA(possibleCombinations)

# rareDataDictionary = sortRarityWeights(DataDictionary)

def send_To_Record_JSON():
   '''
   Creates NFTRecord.json file and sends "batchDataDictionary" to it. NFTRecord.json is a permanent record of all DNA
   you've generated with all attribute variants. If you add new variants or attributes to your .blend file, other scripts
   need to reference this .json file to gnereate new DNA and make note of the new attributes and variants to prevent
   repeate DNA.
   '''

   ledger = json.dumps(DataDictionary, indent=1, ensure_ascii=True)
   with open(os.path.join(save_path, "NFTRecord.json"), 'w') as outfile:
      outfile.write(ledger + '\n')

   print("")
   print("All possible combinations of DNA sent to NFTRecord.json with " + str(possibleCombinations) + "\nNFT DNA sequences generated in %.4f seconds" % (time.time() - time_start))
   print("")
   print("If you want the number of NFT DNA sequences to be higher, please add more variants or attributes to your .blend file")
   print("")

send_To_Record_JSON()

'''Utility functions:'''

def turnAll(toggle):
   '''
   Turns all renender and viewport cameras off or on for all collections in the scene.
   :param toggle: False = turn all cameras on
                  True = turn all cameras off
   '''
   for i in listAllCollections:
      bpy.data.collections[i].hide_render = toggle
      bpy.data.collections[i].hide_viewport = toggle

#turnAll(False)

# ONLY FOR TESTING, DO NOT EVER USE IF RECORD IS FULL OF REAL DATA
# THIS WILL DELETE THE RECORD:
# Also don't forget to add an empty list when its done to NFTRecord or else this file can't run properly.
def clearNFTRecord(AREYOUSURE):
   if AREYOUSURE == True:
      file_name = os.path.join(save_path, "NFTRecord.json")
      print("Wiping NFTRecord.json of all data...")

      ledger = json.load(open(file_name))

      with open(file_name, 'w') as outfile:
         ledger.clear()
         outfile.close()
#clearNFTRecord()