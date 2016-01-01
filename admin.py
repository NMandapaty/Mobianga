#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Created on Sep 25, 2012

@author: Nishant
'''

from google.appengine.ext import db
from google.appengine.api.datastore import Key
import webapp2, os, logging, re
from random import random
import Parsers
from AnnotationGame import Gene, CancerGene, DiseaseGroup
from AnnotationGame import Relationship
from tutorial import Animal, AnimalClassification

#TODO: create interface where frontend instances can trigger backend ones
#taskqueue.add('/admin/*', 'updates')
class UpdateAnimals(webapp2.RequestHandler):
    def get(self):
        old = Animal.all().fetch(10**6)
        for a in old:
            a.delete()
        
        added = 0
        errorsCaught = []
        p = 'animal_list.csv'
        path = os.path.join(os.path.split(__file__)[0], p)
        
        parser = Parsers.AnimalParser(path)
        terms = parser.parse()
        
        for name in terms:
            attrs = terms[name]
            try:
                an = Animal(key_name = name,
                            DBID = attrs[1], #don't include newline
                            DBName = name,
                            DBLatin = attrs[0],
                            DBRandom = random())
                an.put()
                added += 1
            except UnicodeDecodeError:
                errorsCaught.append(name)
                
        self.response.out.write('''
                                <html>
                                <body>
                                Animals added:''' + str(added)
                                + '<br> length of terms:' + str(len(terms))
                                + '<br> errors caught:' + str(errorsCaught))
        self.response.out.write('''
                                <form action='/' method = 'get'>
                                <div><input type='submit' value='Done'></div>
                                </form>
                                ''')
        self.response.out.write('''
                                </body>
                                </html>
                                ''')
        
        
class UpdateClassifications(webapp2.RequestHandler):
    def get(self):
        old = AnimalClassification.all().fetch(10**6)
        for c in old:
            c.delete()
        
        added = 0
        errorsCaught = []
        p = 'classification_list.csv'
        path = os.path.join(os.path.split(__file__)[0], p)
        
        parser = Parsers.ClassificationParser(path)
        terms = parser.parse()
        #terms = {'ID': ('name', 'English name', 'levelID', 'level of classification', 'parent')}
        parents = 0
        for ID, attrs in terms.items():
            if str(ID) == 'ID': 
                logging.info('first line of terms = {%s: %s}' % (str(ID), str(attrs)))
                continue #first line
            children = self.getChildren(ID, terms)
            if len(children) > 0: parents += 1
            try:
                ac = AnimalClassification(key_name = ID,
                                          DBID = ID, 
                                          DBName = attrs[0],
                                          DBEnglish = attrs[1],
                                          DBLevel = attrs[2],
                                          DBLevelName = attrs[3],
                                          DBParent = attrs[4],
                                          DBChildren = children)
                ac.put()
                added += 1
            except UnicodeDecodeError:
                errorsCaught.append(ID)
                
        self.response.out.write('''
                                <html>
                                <body>
                                Classifications added:''' + str(added)
                                + '<br> length of terms:' + str(len(terms))
                                + '<br> errors caught:' + str(errorsCaught)
                                + '<br> parents: ' + str(parents)
                                + '<br> YAYAYAYAYAYAYAY')
        self.response.out.write('''
                                <form action='/' method = 'get'>
                                <div><input type='submit' value='Done'></div>
                                </form>
                                ''')
        self.response.out.write('''
                                </body>
                                </html>
                                ''')
        
    def getChildren(self, classificationID, terms):
        ''' 
        searches through classificationTerms and returns the ones 
        that are children of classificationID
        '''
        #terms = {'ID': ('name', 'English name', 'levelID', 'level of classification', 'parent')}
        children = []
        for ID, attrs in terms.iteritems():
            parent = attrs[4]  
            if str(parent) == 'parent': continue #first line              
            if parent == classificationID:
                children.append(ID)
            
        return children

class UpdateRelationshipLevels(webapp2.RequestHandler):
    def get(self):
        rshipsq = Relationship.all()
        rships = rshipsq.fetch(10**6)
        
        disq = db.GqlQuery('select DBLevel from DiseaseGroup where DBID = :1')
        added = 0
        errorsCaught = []
        for rship in rships:
            disID = rship.DBDisease
            disq.bind(disID)
            dis = disq.get()
            rship.DBLevel = dis.DBLevel
            try:
                rship.put()
                added += 1
            except Exception:
                errorsCaught.append('disID = %s, dis = %s' % (disID, dis))
            
        self.response.out.write('''
                                <html> <body>
                                added = %s <br>
                                errorsCaught = %s        
                                ''' % (added, str(errorsCaught)))
        
        
#TODO: make genes much less intensive. Only store ID and get rest of data only when needed
class UpdateGenes(webapp2.RequestHandler): #'/updateGenes'
    def get(self):
        old = Gene.all().fetch(10**6)
        for g in old:
            g.delete()
        
        added = 0
        errorsCaught = []
        p = 'gene2ensemblHumans.txt'
        path = os.path.join(os.path.split(__file__)[0], p)
        
        parser = Parsers.GeneParser(path)
        length = len(open(path).readlines())
        numLine = 0
        while numLine < length: #length of genes file
            try:
                terms, numLine = parser.parse(start = numLine)
            except TypeError:
                break
#            logging.info('numLine = %s' % numLine)
            if terms is None or terms == {}:
                break
            for ID in terms:
                attrs = terms[ID]
                summary = attrs[2]
                if summary is not None and len(summary) > 500:
                    summary = attrs[2][:500] #500 character limit cutoff
                try:
                    gene = Gene(key_name = ID,
                                DBID = ID,
                                DBSymbol = attrs[0],
                                DBName = attrs[1],
                                DBSummary = summary,
                                DBRandom = random())
                    gene.put()
                    added += 1
                except UnicodeDecodeError:
                    errorsCaught.append(ID)
                
            logging.info('Batch complete,  numLine = %s' % numLine)
         
                
        self.response.out.write('''
                                <html>
                                <body>
                                Genes added:''' + str(added)
                                + '<br> length of terms:' + str(len(terms))
                                + '<br> errors caught:' + str(errorsCaught))
        self.response.out.write('''
                                <form action='/' method = 'get'>
                                <div><input type='submit' value='Done'></div>
                                </form>
                                ''')
        self.response.out.write('''
                                </body>
                                </html>
                                ''')
            
class UpdateCancerGenes(webapp2.RequestHandler):
    def get(self):
        genes = CancerGene.all().fetch(500)
        for gene in genes:
            gene.delete()
        
        added = 0
        errorsCaught = []
        p = 'output.txt'
        path = os.path.join(os.path.split(__file__)[0], p)
        
        parser = Parsers.GeneParser(path)
        terms = parser.parseCancer()
#        self.response.out.write('<html><body> len(terms) = {} </body></html>'.format(len(terms)))
#        return
        if terms is None or terms == {}:
            logging.error('parser not working')
        for ID, attrs in terms.items(): #terms = {'NCBIID':(['symbol'], 'name','summary', 'MIM')}a
            if ID == 'NCBIID': continue #first line
            summary = attrs[2]
#            if summary is not None and len(summary) > 500:
#                summary = attrs[2][:500] #500 character limit cutoff
            try:
                gene = CancerGene(key_name = ID,
                                  DBID = ID,
                                  DBSymbols = attrs[0],
                                  DBMIM = attrs[3],
                                  DBName = attrs[1],
                                  DBSummary = summary,
                                  DBOrder = added)
                gene.put()
                added += 1
            except UnicodeDecodeError:
                errorsCaught.append(ID)
            
                
        self.response.out.write('''
                                <html>
                                <body>
                                Genes added:''' + str(added)
                                + '<br> length of terms:' + str(len(terms))
                                + '<br> errors caught:' + str(errorsCaught))
        self.response.out.write('''
                                <form action='/' method = 'get'>
                                <div><input type='submit' value='Done'></div>
                                </form>
                                ''')
        self.response.out.write('''
                                </body>
                                </html>
                                ''')

class UpdateDiseases(webapp2.RequestHandler): #'/updateDiseases'
    def get(self):
        old = DiseaseGroup.all().fetch(10**6)
        for d in old:
            d.delete()
        
        
        added = 0
        errorsCaught = []
        DGs = []
        parser = Parsers.DOParser('http://diseaseontology.svn.sourceforge.net/viewvc/diseaseontology/trunk/HumanDO.obo')
        terms = parser.parse() #terms = {'DOID':('name', ['alt_ids'], 'def', ['synonyms'], 'subset', ['xrefs'], 'is_a')}

#        temp = terms.copy()
#        levels = self.getLevels(temp)
#        raise Exception('# levels = %s' % len(levels))
        
#        for i in xrange(len(levels)):
#           level = levels[i]
        for DOID, attrs in terms.items():
            defi = attrs[2]
            if defi is not None and len(defi) > 500:
                defi = attrs[2][:500] #500 character limit cutoff
                
            parents = attrs[-1]
#            if level != len(levels) - 1:
            children = self._getChildren(DOID, terms)
#            level = self._getlevel(DOID, terms)
            
            if parents:
#                count = 1
                for parent in parents:
#                    keyName = '{0}_{1}'.format(DOID, count)
                    keyName = '{0}_{1}'.format(DOID, parent)
                    try:
                        DG = DiseaseGroup(key_name = keyName,
                                          DBID = DOID,
                                          DBName = attrs[0],
                                          DBAlt_ids = attrs[1],
                                          DBDef = defi,
                                          DBSyns = attrs[3],
                                          DBSubset = attrs[4],
                                          DBXrefs = attrs[5],
                                          DBParent = parent,
                                          DBChildren = children,
                                          DBLevel = None)
                        DG.put()
                        DGs.append(DG)
                        added += 1
                    except UnicodeDecodeError:
                        errorsCaught.append(DOID)
            else:
                try:
                    DG = DiseaseGroup(key_name = DOID,
                                      DBID = DOID,
                                      DBName = attrs[0],
                                      DBAlt_ids = attrs[1],
                                      DBDef = defi,
                                      DBSyns = attrs[3],
                                      DBSubset = attrs[4],
                                      DBXrefs = attrs[5],
                                      DBParent = parent,
                                      DBChildren = children,
                                      DBLevel = None)
                    DG.put()
                    DGs.append(DG)
                    added += 1
                except UnicodeDecodeError:
                    errorsCaught.append(DOID)
#            if len(parent) == 0:
#                try:
#                    DG = DiseaseGroup(key_name = DOID,
#                                      DBID = DOID,
#                                      DBName = attrs[0],
#                                      DBAlt_ids = attrs[1],
#                                      DBDef = defi,
#                                      DBSyns = attrs[3],
#                                      DBSubset = attrs[4],
#                                      DBXrefs = attrs[5],
#                                      DBParent = None,
#                                      DBChildren = children,
#                                      DBLevel = 1)
#                                    #DBLevel = i+1)
#                    DG.put()
#                    added += 1
#                except UnicodeDecodeError:
#                    errorsCaught.append(DOID)
#                
#            elif len(parents) == 1:
#                try:
#                    parent = parents[0]
#                    level = levels[parent]
#                    DG = DiseaseGroup(key_name = DOID,
#                                      DBID = DOID,
#                                      DBName = attrs[0],
#                                      DBAlt_ids = attrs[1],
#                                      DBDef = defi,
#                                      DBSyns = attrs[3],
#                                      DBSubset = attrs[4],
#                                      DBXrefs = attrs[5],
#                                      DBParent = parent,
#                                      DBChildren = children,
#                                      DBLevel = level)
#                                      #DBLevel = i+1)
#                    DG.put()
#                    added += 1
#                except UnicodeDecodeError:
#                    errorsCaught.append(DOID)
#                    
#            else:
#                for j in xrange(len(parents)):
#                    parent = parents[j]
#                    level = levels[parent]
#                    formatted_id = '{0}_{1}'.format(DOID, str(j))
#                    try:
#                        DG = DiseaseGroup(key_name = formatted_id,
#                                          DBID = DOID,
#                                          DBName = attrs[0],
#                                          DBAlt_ids = attrs[1],
#                                          DBDef = defi,
#                                          DBSyns = attrs[3],
#                                          DBSubset = attrs[4],
#                                          DBXrefs = attrs[5],
#                                          DBParent = parent,
#                                          DBChildren = children,
#                                          DBLevel = level)
#                                          #DBLevel = i+1)
#                        DG.put()
#                        added += 1
#                    except UnicodeDecodeError:
#                        errorsCaught.append(DOID)
        
        
#        errors = self._addLevels(DGs)
        self.response.out.write('''
                                <html>
                                <body>
                                DGs added:''' + str(added)
                                + '<br> length of terms:' + str(len(terms))
                                + '<br> errors caught:' + str(errorsCaught)
                                + '<br> UPDATE DISEASE LEVELS NOW')
#                                + '<br> addLevels errors: ' + str(errors))
        self.response.out.write('''
                                <form action='/' method = 'get'>
                                <div><input type='submit' value='Done'></div>
                                </form>
                                ''')
        self.response.out.write('''
                                </body>
                                </html>
                                ''')
        
        self.redirect('/admin/updateRogueDiseases')
        
    def _addLevels(self, DGs):
        disq = db.GqlQuery('select DBParent from DiseaseGroup where DBID = :1')
        errors = []
        count = 0
        for DG in DGs:
            level = 1
            if count % 100 == 0:
                logging.info('DG.DBID = %s' % DG.DBID)
                logging.info('addLevels still working')
            disq.bind(DG.DBID)
            disease = disq.get()
            if disease is None:
                errors.append(DG.DBID)
                continue
            try:
                while disease.DBParent is not None:
                    disq.bind(disease.DBParent)
                    disease = disq.get()
                    level += 1
            except AttributeError:
                errors.append(DG.DBID)
                continue
            newDG = DiseaseGroup(key_name = DG.DBID + '_' + DG.DBParent,
                                 DBID = DG.DBID,
                                 DBName = DG.DBName,
                                 DBAlt_ids = DG.DBAlt_ids,
                                 DBDef = DG.DBDef,
                                 DBSyns = DG.DBSyns,
                                 DBSubset = DG.DBSubset, 
                                 DBXrefs = DG.DBXrefs,
                                 DBParent = DG.DBParent,
                                 DBChildren = DG.DBChildren,
                                 DBLevel = level)
            newDG.put()
            count += 1
            
        return errors

    def _getChildren(self, diseaseDOID, diseaseTerms):
        ''' 
        searches through diseaseTerms and returns the ones that are children of diseaseDOID
        '''
#        terms = {'DOID':('name', ['alt_ids'], 'def', ['synonyms'], 'subset', ['xrefs'], ['is_a'])}
        children = []
        for DOID, attrs in diseaseTerms.items():
            parents = attrs[6]
            for parent in parents:
                if parent == diseaseDOID:
                    children.append(DOID)
                
        return children
        
        
    def _getLevels(self, diseaseTerms):
#        diseases = db.GqlQuery('select DBID, DBName, DBParent from DiseaseGroup').fetch(7000)
#        query = 'select * from DiseaseGroup where DBParent = :1'
#        orphans = db.GqlQuery(query, None).fetch(7000)
#        self.numDiseases = len(diseaseTerms)
        levels, parentIDs = [], []
        
        while True:
            level = self.findChildren(parentIDs, diseaseTerms)
            parentIDs = level
            levels.append(level)
            for DOID in level:
                diseaseTerms.pop(DOID)
                
            added = 0
            for level in levels: added += len(levels)
            if len(diseaseTerms) == 0 or len(parentIDs) == 0 or added >= self.numDiseases:
                break
            
        return levels
            
    def _getlevel(self, termID, diseaseTerms):
        '''
        Gets the level of term.
        '''
#        terms = {'DOID':('name', ['alt_ids'], 'def', ['synonyms'], 'subset', ['xrefs'], 'is_a')}

#        parents = diseaseTerms[termID]
#        if parents is None or parents == []: #not sure which is true for 'disease'
#            return 1
#        elif parents == ['4']:
#            return 2
#        if len(parents) == 1:
#            return 1 + self._getlevel(parents[0], diseaseTerms)
#        else:
#            for parent in parents:
#                return self._getlevel(parent, diseaseTerms, *parents)

        level = 1
        parent = termID
        while parent != '4':
            
            term = diseaseTerms[parent]
            parent = term[6]
            level += 1
            
        return level
            

    def _findChildren(self, parentIDs, diseaseTerms):
        '''
        searches diseaseTerms to check if their parents are in parentIDs
        '''
        level = []
        for DOID in diseaseTerms:
            attrs = diseaseTerms[DOID]
            parent = attrs[6]
            if parent == [] or parent in parentIDs:
                level.append(DOID)
            
        return level
        
class UpdateDiseaseLevelsBottomUp(webapp2.RequestHandler):
    def get(self):  
#        diseases = db.GqlQuery('select * from DiseaseGroup where DBLevel = :1 order by DBID asc', None).fetch(10**6)
        diseases = db.GqlQuery('select * from DiseaseGroup order by DBID asc').fetch(10**6)
        #set all levels to None first
        logging.info('len diseases = %s' % len(diseases))
        for dis in diseases:
            dis.DBLevel = None
            dis.put()
        errorsCaught = []
        added = 0
        for disease in diseases:
            log = False
            if added % 50 == 0:
                logging.info('still updating levels')
                log = True
            try:
                level = self._getLevel(disease, log)
#                DG = DiseaseGroup(key_name = disease.DBID + '_' + disease.DBParent,
#                                 DBID = disease.DBID,
#                                 DBName = disease.DBName,
#                                 DBAlt_ids = disease.DBAlt_ids,
#                                 DBDef = disease.DBDef,
#                                 DBSyns = disease.DBSyns,
#                                 DBSubset = disease.DBSubset, 
#                                 DBXrefs = disease.DBXrefs,
#                                 DBParent = disease.DBParent,
#                                 DBChildren = disease.DBChildren,
#                                 DBLevel = level)
#                DG.put()
                disease.DBLevel = level
                disease.put()
                added += 1
            except Exception:
                errorsCaught.append(disease.DBID)
            
        self.response.out.write('''
                                <html>
                                <body>
                                DGs added:''' + str(added)
                                + '<br> errors caught:' + str(errorsCaught))                                
        self.response.out.write('''
                                <form action='/' method = 'get'>
                                <div><input type='submit' value='Done'></div>
                                </form>
                                ''')
        self.response.out.write('''
                                </body>
                                </html>
                                ''')
            
    def _getLevel(self, disease, log):
        level = 1
        parent = disease.DBID
#        if log:
#            logging.info('disease.DBID = %s' % disease.DBID)
        disq = db.GqlQuery('select DBParent, DBLevel from DiseaseGroup where DBID = :1')
        while parent != '4':
            disq.bind(parent)
            dis = disq.get()
            if dis and dis.DBLevel:
                level += dis.DBLevel
                break
            if dis is None:
                logging.info('parent = %s' % parent) 
            parent = dis.DBParent
            level += 1
            
        return level
    
class UpdateDiseaseLevelsTopDown(webapp2.RequestHandler):
    def get(self):
        #set all levels to None first
        diseases = DiseaseGroup.all()
        for dis in diseases.fetch(10**6):
            dis.DBLevel = None
            dis.put()
        #update level of 'disease'
        disease = db.GqlQuery('select * from DiseaseGroup where DBID = :1', '4').get()
        disease.DBLevel = 1
        disease.put()
        
        added = 0
        errorsCaught = []
        level = 1
        
        parentq = db.GqlQuery('select * from DiseaseGroup where DBLevel = :1')
        childq = db.GqlQuery('select * from DiseaseGroup where DBID = :1 and DBParent = :2')
        while True:
            parentq.bind(level)
            parents = parentq.fetch(10**6)
            if parents is None or len(parents) == 0:
                break
#            children = []
            for disease in parents:
#                children.extend(disease.DBChildren)
                for childID in disease.DBChildren:
                    childq.bind(childID,disease.DBID)
                    child = childq.get()
                    try:
                        child.DBLevel = level + 1
                        child.put()
                        added += 1
                    except Exception:
                        errorsCaught.append((childID, disease.DBID))      
                    if added % 50 == 0:
                        logging.info('still updating levels')
            level += 1
    
        self.response.out.write('''
                                <html>
                                <body>
                                DGs added:''' + str(added)
                                + '<br> errors caught:' + str(errorsCaught))                                
        self.response.out.write('''
                                <form action='/' method = 'get'>
                                <div><input type='submit' value='Done'></div>
                                </form>
                                ''')
        self.response.out.write('''
                                </body>
                                </html>
                                ''')
    
class UpdateRogueDiseases(webapp2.RequestHandler):
    def get(self):
#        diseases = db.GqlQuery('select * from DiseaseGroup where DBID in :1', ['9455', '4236']).fetch(2)
#        diseases = db.GqlQuery('select * from DiseaseGroup where DBID in :1', ['4236']).fetch(2)
        def1 = u'A lysosomal storage disease that involves the accumulation of harmful amounts of lipids (fats) in some of the body’s cells and tissues.'
        rogue1 = DiseaseGroup(key_name = u'9455_3211',
                              DBID = u'9455',
                              DBName = u'lipid storage disorder',
                              DBAlt_ids = [],
                              DBDef = def1,
                              DBSyns = [],
                              DBSubset = None,
                              DBXrefs = [],
                              DBParent = u'3211',
                              DBChildren = [],
                              DBLevel = 5)
        rogue1.put()
        def2 = u'A mullerian mixed tumor that is composed_of carcinoma of different müllerian types and composed_of homologous or heterologous sarcoma-like components.'
        rogue2 = DiseaseGroup(key_name = u'4236_154',
                              DBID = u'4236',
                              DBName = u'carcinosarcoma',
                              DBAlt_ids = [],
                              DBDef = def2,
                              DBSyns = [],
                              DBSubset = None,
                              DBXrefs = [],
                              DBParent = u'4236',
                              DBChildren = [],
                              DBLevel = 6)
        rogue2.put()
        diseases = [rogue1, rogue2]
        pq = db.GqlQuery('select DBID from DiseaseGroup where DBParent = :1')
        added = 0
        for disease in diseases:
            pq.bind(disease.DBID)
            children = pq.fetch(100)
            IDs = [child.DBID for child in children]
#            DG = DiseaseGroup(key_name = disease.DBID + '_' + disease.DBParent,
#                                DBID = disease.DBID,
#                                DBName = disease.DBName,
#                                DBAlt_ids = [],
#                                DBDef = disease.DBDef,
#                                DBSyns = [],
#                                DBSubset = None,
#                                DBXrefs = [],
#                                DBParent = disease.DBParent,
#                                DBChildren = IDs,
#                                DBLevel = disease.DBLevel)
#        
#            DG.put()
        
            disease.DBChildren = IDs
            disease.put()
            added += 1
        
        logging.info('added = %s' % added)
        self.response.out.write('''
        
        <html><body>
        DONE
        </body></html>
        ''')
        
        self.redirect('/admin/updateDiseaseLevels')
    
app = webapp2.WSGIApplication([(r'/admin/updateRelationshipLevels', UpdateRelationshipLevels), 
                               (r'/admin/updateDiseases', UpdateDiseases),
                               (r'/admin/updateDiseaseLevelsBottomUp', UpdateDiseaseLevelsBottomUp),
                               (r'/admin/updateDiseaseLevels', UpdateDiseaseLevelsTopDown),
                               (r'/admin/updateRogueDiseases', UpdateRogueDiseases),
                               (r'/admin/updateGenes', UpdateGenes),
                               (r'/admin/updateCancerGenes', UpdateCancerGenes),
                               (r'/admin/updateAnimals', UpdateAnimals),
                               (r'/admin/updateClassifications', UpdateClassifications)],
                              debug = True)




