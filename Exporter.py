'''
Created on Nov 5, 2012

@author: Nishant
'''

import datetime
from google.appengine.ext import db
from google.appengine.tools import bulkloader
#import AnnotationGame
#import AnnotationGame.Relationship
class DiseaseGroup(db.Model):
    #key_name = DBID
    DBID = db.StringProperty() #id given by DO
    DBName = db.StringProperty() #name of the disease
    DBAlt_ids = db.StringListProperty() #list of alternate ids
    DBDef = db.StringProperty() #definition given by DO
    DBSyns = db.StringListProperty() #list of synonyms
    DBSubset = db.StringProperty() #subset
    DBXrefs = db.StringListProperty() #list of cross-references
    DBParent = db.StringProperty() #parent disease group (multiple records for disease if more than one parent)
    DBChildren = db.StringListProperty() #list of children disease groups
    DBLevel = db.IntegerProperty() #level in diseases tree
    
class Relationship(db.Model):
    DBName = db.StringProperty() #user.nickname()
    DBGene = db.StringProperty() #db.IntegerProperty() #id of the gene
    DBDisease = db.StringProperty() #db.IntegerProperty() #id of the disease
    DBLevel = db.IntegerProperty() #level in diseases tree of DBDisease
    DBTime = db.IntegerProperty() #time elapsed while answering prompt
    DBFinal= db.BooleanProperty() #true if final relationship submitted for specific prompt
    DBDate = db.DateTimeProperty(auto_now_add = True) #time when it was added

class Player(db.Model):
    #key_name = same as DBName
    DBName = db.StringProperty() #user.nickname() 
    DBPoints = db.IntegerProperty() #Number of points player has earned 
    DBGames = db.IntegerProperty() #Number of games to the game
    DBRelationships = db.IntegerProperty() #Number of relationships established
    DBCancerCount = db.IntegerProperty() #The DBOrder of the last gene answered
    DBChallengeCount = db.IntegerProperty() #Number of cancer genes answered.
    
class AnimalRelationship(db.Model):
    DBName = db.StringProperty() #user.nickname()
    DBAnimal = db.StringProperty() #ID of animal
    DBLevel = db.IntegerProperty() #level in classification tree 
    DBTime = db.IntegerProperty() #time elapsed while answering prompt
    DBFinal = db.BooleanProperty() #true if final relationship submitted for specific prompt
    DBDate = db.DateTimeProperty(auto_now_add = True) #time when it was added
    
class RelationshipExporter(bulkloader.Exporter):
    def __init__(self):
        bulkloader.Exporter.__init__(self, 'Relationship',
                                   [('DBGene', str, None),
                                    ('DBDisease', str, None),
                                    ('DBLevel', int, None),
                                    ('DBFinal', str, None),
                                    ('DBName', str, None),
                                    ('DBTime', int, None),
                                    ('DBDate', str, None)])
        
class PlayerExporter(bulkloader.Exporter):
    def __init__(self):
        bulkloader.Exporter.__init__(self, 'Player',
                                     [('DBName', str, None),
                                      ('DBPoints', str, None),
                                      ('DBGames', str, 'None'),
                                      ('DBRelationships', str, 'None'),
                                      ('DBCancerCount', str, 'None'),
                                      ('DBChallengeCount', str, 'None')])
        
class AnimalRelationshipExporter(bulkloader.Exporter):
    def __init__(self):
        bulkloader.Exporter.__init__(self, 'AnimalRelationship',
                                     [('DBName', str, None),
                                      ('DBAnimal', str, None),
                                      ('DBLevel', int, None),
                                      ('DBTime', int, None),
                                      ('DBFinal', str, None),
                                      ('DBDate', str, None)])
        
class DiseaseGroupExporter(bulkloader.Exporter):
    def __init__(self):
        bulkloader.Exporter.__init__(self, 'DiseaseGroup',
                                     [('DBID', str, None),
                                      ('DBXrefs', list, ' - ')])

exporters = [RelationshipExporter,
             PlayerExporter,
             AnimalRelationshipExporter,
             DiseaseGroupExporter]

