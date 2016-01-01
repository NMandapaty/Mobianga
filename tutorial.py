'''
Created on Oct 8, 2012

@author: Nishant
'''
import webapp2, logging
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from django.utils import simplejson
from AnnotationGame import Player, Guest, Animal, AnimalClassification, AnimalRelationship
from AnnotationGame import RPCHandler, RPCMethods, Page, Skip
from time import time
from math import ceil, fabs
from random import Random
    
#add directions    
class TutorialGamePage(webapp2.RequestHandler):
    '''
    classdocs
    '''
    def get(self):
        playerData = Page().getPlayerData() 
        #(player.DBName, player.DBPoints, player.DBGames, player.DBRelationships, player.DBCancerCount)
        if type(playerData) == type(()):
            name = playerData[0]
            games = playerData[2] + 1
            player = Player(key_name = name,
                            DBName = name,
                            DBPoints = playerData[1],
                            DBGames = games,
                            DBRelationships = playerData[3],
                            DBCancerCount = playerData[4],
                            DBChallengeCount = playerData[5])
        elif type(playerData) == type(''):
            name = playerData
            player = Player.get_or_insert(name)
            player.DBName = name
            player.DBPoints = 0
            player.DBGames = 1
            player.DBRelationships = 0
            player.DBCancerCount = 0
            player.DBChallengeCount = 0
        else:
            self.redirect('/')
            return
        
        player.put()
        values = self.getValues(player)
        
        self.response.out.write(template.render('TutorialGamePageAJAX.html', values, debug=True))
        
    def getValues(self, player):
        player_key = player.key()
        while True:     
            animal = db.GqlQuery('select * from Animal where DBRandom > :1 '
                                 'order by DBRandom limit 1', Random().random()).get()
            if animal != 'Family ID':
                break
        animal_key = animal.key()
        args = ['331030', 'AnimalClassification', player.key()] #parentID, data_type, player_key
        JSON = RPCMethods().getChildren(args, initial = True)
        start_time = time()
        leaders = Page().getLeaders()
        values = {'player': player,
                  'isGuest' : isinstance(player, Guest),
                  'player_key' : player_key,
                  'animal' : animal,
                  'animal_key' : animal_key,
                  'json' : simplejson.dumps(JSON),
                  'start_time' : start_time,
                  'start_points' : player.DBPoints,
                  'leaders': leaders}
        return values
    
#TODO: Add a boolean field "correct" to AnimalRelationship
class TutorialFeedback(webapp2.RequestHandler):
    def get(self):
        current_time = time()
        start_time = float(self.request.get('start_time').encode('ascii', 'ignore'))
        timeElapsed = int(ceil(current_time - start_time))
        
        start_points = int(self.request.get('start_points').encode('ascii', 'ignore'))
        
        animal_key = self.request.get('animal_key').encode('ascii', 'ignore')
        animal = Animal.get(animal_key)
        
        classification_name = self.request.get('classification').encode('ascii', 'ignore')
        classification = db.GqlQuery('select * from AnimalClassification where DBName = :1', classification_name).get()
#        classification = AnimalClassification.gql('where DBName = :1', classification_name).get()
        
        player_key = self.request.get('player_key').encode('ascii', 'ignore')
        player = Player.get(player_key)
#        if player is None:
#            self.response.out.write('<html><body> Player is None. player_key = {} </body></html>'.format(player_key))
#            return
    
        feedback =  self.getFeedback(player = player, 
                                      timeElapsed = timeElapsed, 
                                      animal = animal, 
                                      classification = classification, 
                                      final = True) 
        addedPoints, player, averageTime, answer, correct, almost = feedback
#        agree_path, answer_path, classification_path = self._getPaths(answer, classification)
#        logging.info('agree_path = %s' % str(agree_path))
        
        total_points = player.DBPoints - start_points
        leaders = Page().getLeaders()
        values = {'player' : player,
                  'isGuest' : isinstance(player, Guest),
                  'player_key' : player.key(),
                  'animal' : animal.DBName,
                  'classification_name' : classification_name,
#                  'classification_path' : classification_path,
                  'points' : addedPoints,
                  'total_points' : total_points,
                  'time' : timeElapsed, 
                  'averageTime' : averageTime,
                  'answer' : answer,
#                  'answer_path' : answer_path,
#                  'agree_path' : agree_path,
                  'correct' : correct,
                  'almost' : almost,
                  'leaders': leaders}
        
        self.response.out.write(template.render('TutorialFeedback.html', values, debug=True))        
        
    def getFeedback(self, **kwargs):
        player = kwargs.get('player')
        timeElapsed = kwargs.get('timeElapsed')
        animal = kwargs.get('animal')
        classification = kwargs.get('classification')
        final = kwargs.get('final')
        
        if classification.DBLevel is None:
            logging.info('classification = %s' % classification)
        level = classification.DBLevel#.encode('ascii', 'ignore')
        animal_rship = AnimalRelationship(DBName = player.DBName,
                                          DBAnimal = animal.DBID,
                                          DBLevel = int(level),
                                          DBTime = timeElapsed,
                                          DBFinal = final)
        animal_rship.put()
        
        #Calculate number of points earned
        if final:
            query = 'select DBTime from AnimalRelationship where DBID = :1'
            previous = db.GqlQuery(query, animal.DBID).fetch(10**6)
        else:
            query = 'select DBTime from AnimalRelationship where DBID = :1 and DBLevel = :2'
            previous = db.GqlQuery(query, animal.DBID, classification.DBLevel).fetch(10**6)
        num = len(previous)
        answerID  = animal.DBID.rstrip()
        answer = db.GqlQuery('select * from AnimalClassification where DBID = :1', answerID).get()
        parents = self._getParents(answer)
        if final:
            correct = (classification.DBName == answer.DBName)
            almost = (classification.DBName in parents)
            if num > 1: #not first relationship
                total, player_rships = 0,0
                for rship in previous:
                    if rship.DBName == player.DBName:
                        player_rships += 1
                        continue
                    logging.info('rship.DBName = %s' % rship.DBName)
                    logging.info('player.DBName = %s' % player.DBName)
                    total += rship.DBTime
                average = total/(num - player_rships)
            else: #first relationship
                average = timeElapsed
            
            diff = average - timeElapsed
            if correct:
                points = 100 + diff
            elif almost:
                lev = parents.index(classification.DBName)
                points = 100 - int(lev) + diff
            else:
                points = 50

            if points < 0:
                points = 0
                
        else: #not final 
            correct = (classification.DBName in parents)
            if correct:
                l = parents.index(classification.DBName)
                points = 200 - int(l)
            else:
                points = 50
            
            average, almost = None, None
                
            
        #round points to greatest 10
        points = int(10 * ceil(points / 10))
        
        totalPoints = player.DBPoints + points
        if player.DBRelationships is None:
            rships = 1
        else:
            rships = player.DBRelationships + 1
        
        player.DBPoints = totalPoints
        player.DBRelationships = rships
        player.put()
        
        return (points, player, average, answer, almost, correct)
    
    def _getParents(self, child):
        parents = []
        pquery = db.GqlQuery('select DBName, DBParent from AnimalClassification where DBID = :1')
        classification = child
        while True:
            pquery.bind(classification.DBParent)
            parent = pquery.get()
            if parent is None or parent.DBName == 'Vertebrata':
                break
            else:
                parents.append(parent.DBName)
                classification = parent
                
        parents.append(child.DBName)
        return parents
    
    def _getPaths(self, answer, classification):
        agree_path = []
        answer_path = self._getParents(answer)
        classification_path = self._getParents(classification)
        for i in xrange(len(classification_path)):
            ac = classification_path[i]
            if ac == answer_path[i]:
                agree_path.append(ac)
                classification_path.remove(ac)
                answer_path.remove(ac)               
                
        return (agree_path, answer_path, classification_path)
            
    
app = webapp2.WSGIApplication([(r'/animal/game', TutorialGamePage),
                               (r'/animal/feedback', TutorialFeedback),
                               (r'/rpc.*', RPCHandler),
                               (r'/skip', Skip)],
                              debug = True)
    
