'''
Created on Sep 1, 2012

@author: Nishant
'''

import webapp2, logging, re
from random import Random
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.api import users
#from django.core import serializers
#from django.utils.safestring import SafeString
from django.utils import simplejson
#import json

from time import time
from math import ceil


class Player(db.Model):
    #key_name = same as DBName
    DBName = db.StringProperty() #user.nickname() 
    DBPoints = db.IntegerProperty() #Number of points player has earned 
    DBGames = db.IntegerProperty() #Number of games to the game
    DBRelationships = db.IntegerProperty() #Number of relationships established
    DBCancerCount = db.IntegerProperty() #The DBOrder of the last gene answered
    DBChallengeCount = db.IntegerProperty() #Number of cancer genes answered. 

class Guest(Player):
    DBDate = db.DateProperty(auto_now_add = True) #date used

class PlayerPreferences(db.Model):
    #key_name = user.nickname()
    DBExpertise = db.StringListProperty() #List of expertise of the player

class Gene(db.Model):
    #key_name = DBID
    DBID = db.StringProperty()
    DBSymbol = db.StringProperty()
    DBName = db.StringProperty()
    DBSummary = db.StringProperty()
    DBRandom = db.FloatProperty() #random float between 0 and 1, used in GamePage.getGene()
    
class CancerGene(db.Model): #primarily just for initial data trials
    DBID = db.StringProperty()
    DBSymbols = db.StringListProperty()
    DBMIM = db.StringProperty()
    DBName = db.StringProperty()
#    DBSummary = db.StringProperty()
    DBSummary = db.TextProperty()
    DBOrder = db.IntegerProperty() #number indicating which number in the sequence this gene is
    
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
    
class Animal(db.Model):
    #key_name = DBID
    DBID = db.StringProperty()
    DBName = db.StringProperty() #english name
    DBLatin = db.StringProperty() #latin name
    DBRandom = db.FloatProperty()
    
class AnimalClassification(db.Model):
    #key_name = DBID
    DBID = db.StringProperty()
    DBName = db.StringProperty() #latin name
    DBEnglish = db.StringProperty() #english name
    DBLevel = db.StringProperty()
    DBLevelName = db.StringProperty()
    DBParent = db.StringProperty()
    DBChildren = db.StringListProperty()
    
class AnimalRelationship(db.Model):
    DBName = db.StringProperty() #user.nickname()
    DBAnimal = db.StringProperty() #ID of animal
    DBLevel = db.IntegerProperty() #level in classification tree 
    DBTime = db.IntegerProperty() #time elapsed while answering prompt
    DBFinal = db.BooleanProperty() #true if final relationship submitted for specific prompt
    DBDate = db.DateTimeProperty(auto_now_add = True) #time when it was added
    
class Comment(db.Model):
    DBComment = db.StringProperty(required=True, multiline=True)
    DBTime = db.DateTimeProperty(auto_now_add=True)
    DBName = db.StringProperty()

#TODO: Add sound effects

    
class Page():
    '''
    Handles ubiquitous processes that must be called for each page
    '''
    def getPlayerData(self):
        '''
        Checks if user is logged in. If not, returns None.
        If so, checks database for record of the current player.
        If one exists, returns (player.DBName, player.DBPoints, player.DBGames, player.DBRelationships, player.DBCancerCount).
        Else returns user.nickname()
        '''
        user = users.get_current_user()
        if user:
            name = user.nickname()
            query = 'SELECT * FROM Player WHERE DBName = :1'
            player = db.GqlQuery(query, name).get()
            if player:
#               TODO: change to dictionary
                return (player.DBName, 
                        player.DBPoints, 
                        player.DBGames, 
                        player.DBRelationships, 
                        player.DBCancerCount,
                        player.DBChallengeCount)
            else:
                return name
        else:
            return None
    
    def getPlayer(self):
        '''
        Returns None if user is not logged in or if there is no record for this username.
        Else returns the player. 
        '''
        user = users.get_current_user()
        if user:
            name = user.nickname()
            player = db.GqlQuery('SELECT * FROM Player WHERE DBName = :1', name).get()
            return player
        else:
            return None
        
    def getLeaders(self):
        leaders = db.GqlQuery('SELECT * FROM Player '
                              'ORDER BY DBPoints DESC').fetch(10)
        return leaders
    
    def getLeadersJSON(self):
        leaders = self.getLeaders()
        JSON = []
        for leader in leaders:
            domain_search = re.search('(.+)@(.+)', leader.DBName)
            if domain_search is None:
                name = leader.DBName
            else:
                name = domain_search.group(1)
            JSON.append((name, int(leader.DBPoints)))
            
        return JSON
    
    def getComments(self):
        comments = db.GqlQuery('select * from Comment '
                               'order by DBTime desc')
        return comments
        
class Board(webapp2.RequestHandler): #'/'
    def get(self):        
        playerData = Page().getPlayerData()
        if playerData is None:
            player = None
        elif type(playerData) == type(''):
            name = playerData
            player = Player(key_name = name,
                            DBName = name,
                            DBPoints = 0,
                            DBGames = 0,
                            DBRelationships = 0,
                            DBCancerCount = 0)
        else:
            if playerData[2]:
                games = int(playerData[2])    
                games += 1
            else:
                games = 1        
            player = Player(key_name = playerData[0],
                            DBName = playerData[0],
                            DBPoints = playerData[1],
                            DBGames = games,
                            DBRelationships = playerData[3],
                            DBCancerCount = playerData[4],
                            DBChallengeCount = playerData[5])
            player.put()
        
        values = self.getValues(player)
        
        self.response.out.write(template.render('LeaderBoard.html', values, debug=True))
        
    def getValues(self, player):
        leaders = Page().getLeaders()
        comments = Page().getComments()
        values = {'player' : player, 
                  'leaders' : leaders,
                  'comments' : comments}
        
        return values
        
    def post(self):
        name = self.request.get('name')
        comment = Comment(
                    DBName = name,
                    DBComment = self.request.get('comment'))
        comment.put()
        self.get()


#TODO: add 'from' argument -> subtract points from players who click home button while playing
class GamePage(webapp2.RequestHandler): #'/game'
    '''
    Game page of the game. Player is prompted with a random gene and instructed to find the phenotype associated 
    with it. 
    '''
#    start = 0
#    current_player = None
    cancer = False
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
        
        self.response.out.write(template.render('GamePageAJAX.html', self.getValues(player), debug=True))
        
                
    def getValues(self, player):
        player_key = player.key()
        logging.info('player_key = %s' % player_key)
#        geneID = self._getGene() 
#        gene = db.GqlQuery('select * from Gene where DBID = :1', geneID).get()
#        gene = db.GqlQuery('select * from Gene where DBRandom > :1 order by DBRandom limit 1', Random().random()).get()
        gene = self._getCancerGene(player.DBCancerCount)
        if gene is None:
            gene = db.GqlQuery('select * from CancerGene where DBOrder >= :1', 0).get()
#            self.response.out.write('''
#                                    <html><body>
#                                    Congratulations! You have completed all of the challenges!
#                                    </body></html>
#                                    ''')
#            return
        gene_key = gene.key()
        start_time = time()
        args = ['4', 'DiseaseGroup', player_key] #parentID, data_type, player_key, prompt_key, start_time
        JSON = RPCMethods().getChildren(args, initial = True)
        values = {'player': player,
                  'isGuest' : isinstance(player, Guest),
                  'player_key' : player_key,
                  'gene' : gene,
                  'gene_key' : gene_key,
                  'json' : simplejson.dumps(JSON),
                  'start_time' : start_time,
                  'start_points' : player.DBPoints}        
        if self.cancer:
            if player.DBChallengeCount is None:
                values['challenge'] = 1
            else:
                values['challenge'] = player.DBChallengeCount + 1
#        self.response.out.write(template.render('AnnotationGamePage.html', 
#                                                values, debug=True))
        
        return values
                        
   
#TODO: eventually add difficulties for genes, possibly add option to only answer new gene prompts for more points
#TODO: eventually use player preferences to narrow number of genes to pick from
    def _getGene(self):
        genes = db.GqlQuery('select DBID from Gene').fetch(35000)
        rand = Random()
        gene = rand.choice(genes)
        return gene.DBID
    
    def _getCancerGene(self, cancerCount):
#        if cancerCount > 152:
#            return None
        self.cancer = True
        if cancerCount is None:
            cancerCount = 0
        cancerQuery = 'select * from CancerGene where DBOrder >= :1 order by DBOrder asc limit 1'
        gene = db.GqlQuery(cancerQuery, cancerCount).get()
        return gene
        

class RPCHandler(webapp2.RequestHandler):
        
    def get(self, *args):        
        func = None
        self.methods = RPCMethods()
        
        action = self.request.get('action')
        if action:
            if action[0] == '_': #attempting to access private methods
                self.error(403) #access denied
                return
            else:
                func = getattr(self.methods, action, None)
            
        if not func: #function not in RPCMethods
            self.error(404) #file not found
            return
        
        args = []
        while True:
            key = 'arg%d' % len(args)
            val = self.request.get(key)
            if val:
                args.append(simplejson.loads(val))
            else:
                break
           
        result = func(args)
        self.response.out.write(simplejson.dumps(result))
        
class RPCMethods:
    '''
    Defines the methods that can be RPCed.
    NOTE: Do not allow remote callers access to private/protected "_*" methods.
    '''
    
    def getChildren(self, args, initial = False):
        parentID = args[0].rstrip()
        data_type = args[1]
        player_key = args[2]
        try:
            player = Player.get(player_key)
        except db.BadKeyError:
            player = Guest.get(player_key)
        query = 'select * from {0} where DBID = :1'.format(data_type)
        parentQ = db.GqlQuery(query, parentID)
        parent = parentQ.get()
        
        if initial:
            points = player.DBPoints
            correct, addedPoints, percent = None, 0, None
        else:
            if len(args) > 3: #if extra information provided, child was clicked
                prompt_key = args[3]
                
                timeElapsed = int(time() - float(args[4].encode('ascii', 'ignore')))
                addedPoints, percent, correct = self._getPoints(data_type = data_type,
                                                              player = player,
                                                              timeElapsed = timeElapsed,
                                                              prompt_key = prompt_key,
                                                              answerID = parentID)
                points = player.DBPoints #+ addedPoints
#                if percent:
#                    percent = percent[1]
            else: #parent clicked, don't store relationship or award points
                if data_type == 'DiseaseGroup':
                    #remove half of number of points earned
                    level = parent.DBLevel
                    addedPoints = -(level * 10)
                else:
                    addedPoints = -20
                correct, percent  = None, None
                points = addedPoints + player.DBPoints
                if points < 0:
                    points = 0
                player.DBPoints = points
                player.put() #_getPoints updates player
                if data_type == 'DiseaseGroup' and parentID != '4': #remove last relationship
                    delete_query = 'select __key__ from Relationship where DBName = :1 order by DBDate desc limit 1'
                    rship = db.GqlQuery(delete_query, player.DBName).get()
                    db.delete(rship)
            
        JSON = {}
        if data_type == 'DiseaseGroup':
            JSON['diseases'] = self._createJSONchildren(data_type, parent, parentQ)
        else:
            JSON['classifications'] = self._createJSONchildren(data_type, parent, parentQ)
        JSON['points'] = points
        JSON['addedPoints'] = addedPoints
        logging.info('added points = %s' % addedPoints)
        JSON['correct'] = correct
        JSON['percent'] = str(percent)
#        logging.info('percent = %s' % percent)
        JSON['leaders'] = Page().getLeadersJSON()
        
#        logging.info('leaders = %s' % str(JSON['leaders']))
        return JSON
    
    def _getPoints(self, data_type, player, timeElapsed, prompt_key, answerID):
        import tutorial
        if data_type == 'AnimalClassification':
            animal = Animal.get(prompt_key)
            answer = db.GqlQuery('select * from AnimalClassification where DBID = :1', answerID).get()
            feedback = tutorial.TutorialFeedback().getFeedback(player = player, 
                                                               timeElapsed = timeElapsed,
                                                               animal = animal, 
                                                               classification = answer, 
                                                               final = False)
            addedPoints = feedback[0]
            correct = feedback[-1]
            percent = None
        elif data_type == 'DiseaseGroup':
            try:
                gene = Gene.get(prompt_key)
            except db.KindError:
                gene = CancerGene.get(prompt_key)
            answer = db.GqlQuery('select * from DiseaseGroup where DBID = :1', answerID).get()
            addedPoints, average, percents = Feedback().getFeedback(player = player, 
                                                                    timeElapsed = timeElapsed, 
                                                                    gene = gene, 
                                                                    disease = answer, 
                                                                    final = False)
#            addedPoints = feedback[0]
#            percents = feedback[2]
            percent = percents[0][1]
            correct = None
        else:
            raise Exception('invalid data type')
        
        return (addedPoints, percent, correct)
    
    def _createJSONchildren(self, data_type, parent, parentQ):
        '''
        Returns the parent and its children in JSON format
        '''
        JSON = {}
        JSON['name'] = parent.DBName
        JSON['id'] = parent.DBID
        JSON['parent'] = parent.DBParent
#        query = 'select * from {0} where DBParent = :1'.format(data_type)
#        children = db.GqlQuery(query, parent.DBID.rstrip())
#        logging.info('children = %s' % str(children))
        children = parent.DBChildren
        childrenJSON = []
        for childID in children:
            parentQ.bind(childID)
            child = parentQ.get()
            childJSON = {}
            childJSON['name'] = child.DBName
            childJSON['id'] = child.DBID
            childJSON['parent'] = parent.DBID
            childJSON['hasChildren'] = (len(child.DBChildren) != 0)
            
            childrenJSON.append(childJSON)
            
        JSON['children'] = childrenJSON
        
        return JSON
            
            
class Feedback(webapp2.RequestHandler): #'/feedback'
    def get(self):
        #get all values from form
        current_time = time()
        start_time = float(self.request.get('start_time').encode('ascii', 'ignore'))
        t = int(ceil(current_time - start_time))
        
        start_points = int(self.request.get('start_points').encode('ascii', 'ignore'))
        
        gene_key = self.request.get('gene_key').encode('ascii', 'ignore')
#        try:
#            g = Gene.get(gene_key)
#        except db.KindError:
        g = CancerGene.get(gene_key)
        
        dis = self.request.get('disease').encode('ascii', 'ignore')
        d = db.GqlQuery('select * from DiseaseGroup where DBName = :1', dis).get()
        
        player_key = self.request.get('player_key').encode('ascii', 'ignore')
        try:
            p = Player.get(player_key)
        except db.BadKeyError:
            p = Guest.get(player_key)
        if p is None:
            self.response.out.write('<html><body> Player is None. player_key = {} </body></html>'.format(player_key))
            return
        
        addedPoints, averageTime, percents = self.getFeedback(timeElapsed = t, 
                                                              gene = g, 
                                                              disease = d, 
                                                              player = p, 
                                                              final = True) 
        
        leaders = Page().getLeaders()
        total_points = p.DBPoints - start_points
        values = {'player' : p,
                  'isGuest' : isinstance(p, Guest),
                  'player_key' : p.key(),
                  'gene' : g.DBName,
                  'disease' : d,
                  'points' : addedPoints,
                  'total_points' : total_points,
                  'time' : t, 
                  'averageTime' : averageTime,
                  'percents' : percents,
                  'leaders': leaders}
        
        if isinstance(g, CancerGene):
            values['challenge'] = p.DBChallengeCount - 1
        
        self.response.out.write(template.render('Feedback.html', values, debug=True)) 
               
        
    def getFeedback(self, **kwargs): 
        timeElapsed = kwargs.get('timeElapsed')
        gene = kwargs.get('gene')
        disease = kwargs.get('disease')
        player = kwargs.get('player')
        final = kwargs.get('final')
        
        if isinstance(player, Guest):
            isGuest = True
        else:
            isGuest = False
        if not isGuest: #only store relationships if not a guest
            rship = Relationship(DBName = player.DBName,
                             DBGene = gene.DBID,
                             DBDisease = disease.DBID,
                             DBLevel = disease.DBLevel,
                             DBTime = timeElapsed,
                             DBFinal = final)
            rship.put()
#       percents = [] #(disease answered, percent agree, level) at each level
        percents = {} # disease answered : (percent agree, level)        
        if final and not isGuest:
            count_query = 'select * from Relationship where DBGene = :1 and DBName != :2'
            previous = db.GqlQuery(count_query, gene.DBID, player.DBName)
            total_previous = previous.count()
            other_answers = previous.fetch(10**6)
#            logging.info('total_previous = %s' % total_previous)
            
            pquery = 'select * from Relationship where DBGene = :1 and DBName = :2 order by DBLevel asc'
            levels = db.GqlQuery(pquery, gene.DBID, player.DBName).fetch(100)
            
            disq = db.GqlQuery('select DBName from DiseaseGroup where DBID = :1')            
            total_time = 0
            totalfn = 0
            if total_previous > 0: #not first relationship
                #calculate percentages at each level
                for level in levels:
                    disID = level.DBDisease
#                    logging.info('disID = %s' % disID)
                    #get other answers at same level
                    previous_at_level = []
                    for other in other_answers:
                        if int(other.DBLevel) == level.DBLevel:
                            previous_at_level.append(other)
                    if previous_at_level:
                        answer_count = 0
                        for level_rship in previous_at_level:
                            if level_rship.DBDisease == disID:
                                answer_count += 1
#                            if level_rship.DBFinal:
##                                logging.info('final reached')
#                                total_time += level_rship.DBTime
#                                totalfn += 1
                            
                        percent = 100 * answer_count/len(previous_at_level)
                    else:
                        percent = 0
                    disq.bind(disID)
                    dis = disq.get()
                    percents[dis.DBName] = (percent, level.DBLevel)
#                    percents.append((dis.DBName, percent, level.DBLevel))
                #calculate total time
                rships = db.GqlQuery('select * from Relationship where DBGene = :1 and DBFinal = :2', '9077', True).fetch(10**6)
                totalfn = len(rships)
                for rship in rships:
                    total_time += rship.DBTime
                if totalfn == 0:
                    totalfn = 1
                average = total_time/totalfn
                diff = average - timeElapsed
                average_percent = 100 * sum([percent for percent,lev in percents.values()])/len(percents)               

            else: #first relationship
                average = None
                diff = 0
                average_percent = 100
                
            #calculate points
            if isinstance(gene, CancerGene):
    #            mim = gene.MIM
                try:
                    points = 100 + 10 * player.DBChallengeCount
                except TypeError:
                    points = 100
#                logging.info('points = %s' % points)
            else:
                points = 100
            points += 10 * disease.DBLevel
#            logging.info('points = %s' % points)
            points += diff
#            logging.info('points = %s' % points)
            points += average_percent
#            logging.info('points = %s' % points)

        elif final and isGuest:
            count_query = 'select * from Relationship where DBGene = :1'
            previous = db.GqlQuery(count_query, gene.DBID)
            total_previous = previous.count()
            previous_answers = previous.fetch(10**6)
            if total_previous > 0:
                total_time = sum([rship.DBTime for rship in previous_answers])
                average = total_time/total_previous
                diff = average - timeElapsed
            else: #first relationship
                average = None
                diff = 0
                
            average_percent = 100
            #calculate points
            if isinstance(gene, CancerGene):
#            mim = gene.MIM
                try:
                    points = 100 + 10 * player.DBChallengeCount
                except TypeError:
                    points = 100
#                logging.info('points = %s' % points)
            else:
                points = 100
            points += 10 * disease.DBLevel
#            logging.info('points = %s' % points)
            points += diff
#            logging.info('points = %s' % points)
            points += average_percent
#            logging.info('points = %s' % points)
            
        else: #not final
            level = disease.DBLevel
            levelq_string = 'select * from Relationship where DBGene = :1 and DBLevel = :2 and DBName != :3'
            levelq = db.GqlQuery(levelq_string, gene.DBID, level, player.DBName)
            level_rships = levelq.fetch(1000)
            if len(level_rships) == 0:
                percent = None
            else:
                count = 0
                for rship in level_rships:
                    if rship.DBDisease == disease.DBID:
                        count += 1
                percent = 100 * count/len(level_rships)       
#            percents = [(disease.DBName, percent)]
            percents[disease.DBName] = (percent, level)
            
            points = 20 * level + 200
            logging.info('points = %s' % points)
            average = None
            totalfn = 0

        if points < 0:
            points = 0
        #round points to greatest 10
        addedPoints = int(10 * ceil(points/10.0))
        logging.info('addedPoints = %s' % addedPoints)
        #update player
        current_points = player.DBPoints + addedPoints
        if player.DBRelationships is None:
            rships = 0
        else:
            rships = player.DBRelationships + 1
        if isinstance(gene, CancerGene) and final:
            if player.DBChallengeCount is None:
                challengeCount = 1
            else:
                challengeCount = player.DBChallengeCount + 1
            cancerCount = gene.DBOrder + 1                
        else:
            challengeCount = player.DBChallengeCount
            cancerCount = player.DBCancerCount
            
        player.DBCancerCount = cancerCount
        player.DBChallengeCount = challengeCount
        player.DBRelationships = rships
        player.DBPoints = current_points
        player.put()
        
        #check if relationships greater than 8 to switch out sufficiently answered prompts
        try:
            if totalfn >= 9:
                gene.DBOrder += 1000
                gene.put()
        except UnboundLocalError:
            pass
        
        percentsList = []
        for name, tup in percents.items():
            perc = tup[0]
            lev = tup[1]
            percentsList.append((name, perc, lev))
            
        #sort percentsList by level
        percentsList.sort(key = self._sortList)

        feedback = {'points' : addedPoints,
                    'average' : average,
                    'percents' : percentsList}
        
        return (addedPoints, average, percentsList)
    
    def _getLevel(self, disease):
        level = 1
        parent = disease.DBID
        disq = db.GqlQuery('select DBParent from DiseaseGroup where DBID = :1')
        while parent != '4':
            disq.bind(parent)
            parent = disq.get()
            level += 1
            
        return level
    
    def _sortList(self, tup):
        return tup[2]
    
class GuestGame(webapp2.RequestHandler): #'/guest?game=[&guest_key=]'
    def get(self):
        from tutorial import TutorialGamePage
        
        guest_key = self.request.get('guest_key')
        logging.info('guest_key = %s' % guest_key)
        try:
            guest = Guest.get(guest_key) 
        except db.BadKeyError:
            last_guest = db.GqlQuery('select DBName from Guest order by DBDate desc limit 1').get()
            if last_guest is None:
                last_name = 'Guest_0'
            else:
                last_name = last_guest.key().name()
    #        try:
    #            last_name = last_guest.key().name()
    #        except AttributeError:
    #            last_name = 'Guest_0'
            count = int(last_name[6:])
            name = 'Guest_{}'.format(str(count + 1))
            guest = Guest(key_name = name,
                          DBName = 'Guest',
                          DBPoints = 0,
                          DBGames = 0,
                          DBRelationships = 0,
                          DBCancerCount = 0,
                          DBChallengeCount = 0)
            guest.put()
        game = self.request.get('game')
        
        if game == 'gene':
            values = GamePage().getValues(guest)
            self.response.out.write(template.render('GamePageAJAX.html', values, debug=True))
        elif game == 'animal':
            values = TutorialGamePage().getValues(guest)
            self.response.out.write(template.render('TutorialGamePageAJAX.html', values, debug=True))
            
        
#class GuestAnimalGame(webapp2.RequestHandler): #'/guestAnimalGame
#    def get(self):
#        pass
                    
class Change(webapp2.RequestHandler): #'/change'
    def get(self):
        self.redirect(users.create_login_url('/'))    

class SignOut(webapp2.RequestHandler): #'/signout'
    def get(self):
        self.redirect(users.create_logout_url('/'))
        
class About(webapp2.RequestHandler): #'/about'
    def get(self):
        player = Page().getPlayer()
        values = {'player' : player}
        self.response.out.write(template.render('About.html', values, debug = True))
        
class Skip(webapp2.RequestHandler): #'/skip'
    def get(self):
        calledFrom = self.request.get('calledFrom')
        player_key = self.request.get('player_key')
        logging.info('calledFrom = %s, player_key = %s' % (calledFrom, player_key))
        try:
            player = Player.get(player_key)
        except db.BadKeyError:
            player = Guest.get(player_key)
        if player.DBCancerCount is None:
            cancerCount = 0
        else:
            cancerCount = player.DBCancerCount
        if player.DBChallengeCount is None:
            challengeCount = 0
        else:
            challengeCount = player.DBChallengeCount
        points = player.DBPoints - 200
        if points < 0:
            points = 0
        
        player.DBCancerCount = cancerCount + 1
        player.DBChallengeCount = challengeCount + 1
        player.DBPoints = points
        player.put()
        self.redirect(calledFrom)
  
#TODO: update preferences page  
class Preferences(webapp2.RequestHandler): #'/preferences'
    calledfrom=''
    def get(self, calledfrom):
        self.calledfrom = self.request.get('calledfrom')
        playerData = Page().getPlayerData() #(player.DBName, player.DBPoints, player.DBGames, player.DBRelationships)
        player = None
        dquery = 'SELECT * FROM DiseaseGroup where DBParent = :1 limit 8'
        groups = db.GqlQuery(dquery, '4')
        
        values = {'player': player,
                  'groups': groups,
                  'calledfrom': self.calledfrom}
        self.response.out.write(template.render('preferences.html', values, debug=True))
    
    def post(self, expertise):
        expertise = self.request.get_all('expertise') 
        PP = PlayerPreferences(
                             key_name = users.get_current_user().nickname(),
                             DBExpertise = expertise)
        PP.put()
        
        if self.calledfrom == 'G':
            self.redirect('/game')
        else:
            self.redirect('/')
        

app = webapp2.WSGIApplication([(r'/', Board),
                               (r'/game', GamePage),
                               (r'/guest.*', GuestGame),
                               (r'/change', Change),
                               (r'/signout', SignOut),
                               (r'/skip', Skip),
                               (r'/feedback', Feedback),
                               (r'/preferences(?:\?calledfrom=(.))?', Preferences),
                               (r'/rpc.*', RPCHandler),
                               (r'/about', About)],
                              debug=True)

