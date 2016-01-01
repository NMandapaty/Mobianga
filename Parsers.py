'''
Created on Sep 15, 2012

@author: Nishant
'''
import re, json#, urllib
from google.appengine.api import urlfetch
import logging

class DOParser(object):
    '''
    Parses disease-ontology.org's OBO file containing a list of disease ontologies 
    and organizes the information into a dictionary with key = DOID, value = tuple 
    containing other attributes
    '''
    
    #DOsrc = path to disease-ontology OBO source file

    def __init__(self, DOsrc):
        '''
        Constructor
        '''
        self.DOsrc = DOsrc
        
    def parse(self):
        terms = {'DOID':('name', ['alt_ids'], 'def', ['synonyms'], 'subset', ['xrefs'], ['is_a'])}
        if self.DOsrc[:7] == 'http://':
            DOuf = urlfetch.fetch(self.DOsrc)
            DOdata = DOuf.content
        else:
            DOf = open(self.DOsrc)
            DOdata = DOf.read()
            DOf.close()
            
        raw_terms = re.findall(r'\[Term\]\n(.+?)\n\n', DOdata, re.DOTALL) #finds cannot overlap --> will miss every other term 
        for term in raw_terms:
            if re.search('is_obsolete:', term) is not None: #check if term is obsolete
                continue
            DOID, name, defi, subset = None, None, None, None
            alt_ids = []
            synonyms = []
            xrefs = []
            parents = [] 
            attrs = re.split('\n', term)
            for attr in attrs:
                tag = re.search('(.+?):', attr).group(1)
                if tag is None:
                    continue
                elif tag == 'id':
                    DOID = re.search('\d+', attr).group()
                elif tag == 'name':
                    name = re.search('name: (.+)', attr).group(1)
                elif tag == 'alt_id':
                    alt_id = re.search('alt_id: DOID:(\d+)', attr).group(1)
                    alt_ids.append(alt_id)
                elif tag == 'def':
                    defi = re.search('def: (.+)', attr).group(1)
                elif tag == 'synonym':
                    syn = re.search('synonym: (.+)', attr).group(1)
                    synonyms.append(syn)
                elif tag == 'subset':
                    subset = re.search('subset: (.+)', attr).group(1)
                elif tag == 'xref':
                    xrefm = re.search('xref: (.+?):(.+)', attr)
                    xrefs.append(xrefm.group(1) + ':' + xrefm.group(2))
                elif tag == 'is_a':
                    parentm = re.search('is_a: DOID:(\d+) ! (.+)', attr)
                    parents.append(parentm.group(1))# + ':' + parentm.group(2))
                elif tag == 'created_by' or tag == 'creation_date': None
                elif tag == 'comment': None #might be useful/important
                elif tag == 'relationship': None #Not useful, only used for DOID:6457, Cowden disease
                else:
                    raise Exception('unhandled tag: ' + tag)
                
                terms[DOID] = (name, alt_ids, defi, synonyms, subset, xrefs, parents) #separate terms for different parents
                
            
        return terms
                
         
            
class GeneParser(object):
    
    GeneSrc = ''
    
    def __init__(self, GSrc):
        '''
        Constructor
        '''
        self.GeneSrc = GSrc
        
    
    def parse(self, start=0, *topics):
        '''
        Parses self.GeneSrc starting at line number start, and returning once the number of terms added is 500. 
        If any topics are provided, only genes whose name contains one of the specified topics can be returned.
        '''
        terms = {'NCBIID':('symbol', 'name','summary')}
        errorsCaught = 0
        Gf = open(self.GeneSrc)
        Gfdata = Gf.readlines()
        Gf.close()
        numLine = start
        
        for line in Gfdata[start:] :
            fields = re.split('\t', line)
            if len(fields) == 1: 
                continue #first line
            if [re.search(topic, fields[4]) for topic in topics] == [None] * len(topics):
                continue
            ID = fields[1]
            if ID in terms:
                continue #repetitions
            try:
                geneinfoHTML = urlfetch.fetch('http://mygene.info/gene/{}?filter=name,summary,symbol,MIM'.format(ID))
            except urlfetch.DeadlineExceededError:
                errorsCaught += 1
                continue
            geneinfo = json.loads(geneinfoHTML.content)
            symbol, name, summary = [geneinfo.get(field) for field in terms['NCBIID']]
            
            terms[ID] = (symbol, name, summary)
            numLine += 1
            
            if len(terms) == 501:                    
                return (terms, numLine)
            
    def parseCancer(self):
        '''
        Parses self.GeneSrc and returns only the genes that have the word topic in the name
        '''        
        terms = {'NCBIID':(['symbols'], 'name','summary', 'MIM')}
        errorsCaught = 0
        Gf = open(self.GeneSrc)
        Gfdata = Gf.readlines()
        Gf.close()
        count = 0
        
        for line in Gfdata:
            fields = re.split('\t', line)
            if len(fields) == 1 or fields[0] == 'ncbi_gene_id': #first line or last line
                continue
            #
            dis = fields[-1]
            cancer = re.search('cancer|neoplasm|carcinoma', dis) is not None
            notSus = re.search('susceptibility', dis) is None
            valid = cancer and notSus or count % 6 == 0
            if not valid:
                continue
            ID = fields[0]
            if ID in terms: #repetitions
                continue
            MIM = fields[1]
            symbols = re.split('\|', fields[2])
#            symbol = symbols[0]
            try:
                geneinfoHTML = urlfetch.fetch('http://mygene.info/gene/{}?filter=name,summary'.format(ID))
            except urlfetch.DeadlineExceededError:
                errorsCaught += 1
                continue
            try:
                geneinfo = json.loads(geneinfoHTML.content)
            except ValueError:
                errorsCaught += 1
                logging.info(ID)
                continue
            summary = geneinfo.get('summary')
            name = geneinfo.get('name')
            
            invalid = 'E\. coli|avian|Drosophila|elegans|yeast|cerevisiae'
            if re.search(invalid, name) is None:
                terms[ID] = (symbols, name, summary, MIM)
                count += 1
            
        return terms
    
class AnimalParser(object):
    AnimalScr = ''
    
    def __init__(self, ASrc):
        self.AnimalScr = ASrc
        
    def parse(self):
        terms = {'Family ID': ('latin name', 'name')}       
        Af = open(self.AnimalScr)
        Afdata = Af.readlines()
        Af.close()
        for line in Afdata:
            fields = re.split(',', line)
            name = fields[0]
            latin_name = fields[1]
            FID = fields[2][:-1] #don't include newline
            terms[name] = (latin_name, FID)
        
        return terms
    
    
class ClassificationParser(object):
    
    ClassScr = ''
    
    def __init__(self, CSrc):   
        self.ClassScr = CSrc
        
    def parse(self):
        terms = {'ID': ('latin name', 'name', 'levelID', 'level of classification', 'parent')}
        Cf = open(self.ClassScr)
        Cdata = Cf.readlines()
        Cf.close()
        for line in Cdata:
            fields = re.split(',', line)
            '''
            ID = fields[0]
            latin_name = fields[1]
            name = fields[2]
            levelID = fields[3]
            level = fields[4]
            parent = fields[5]
            '''
            
            
            ID, latin_name, name, levelID, level, parent = [fields[i] for i in range(len(fields))]
            
            terms[ID] = (latin_name, name, levelID, level, parent[:6]) #don't include newline
            
            
        return terms