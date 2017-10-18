from google.appengine.ext import ndb
from google.net.proto.ProtocolBuffer import ProtocolBufferDecodeError
import datetime
import logging
import webapp2
import json

#getSlipCount function is used increment and return a value for a new slip 
def getSlipCount():
    query = Slip.query()
    returnValues = query.fetch(limit=200) #get at most 200 results 
    value = 0; #create temp value 

    #get highest number that is being returned
    for vals in returnValues:
        if vals.number > value:
            value = vals.number
    #set our return value to the number we jsut got
    slipNumber = value
    slipNumber = slipNumber + 1  #increment
    return slipNumber

#use to debug code and log errors
class BaseHandler(webapp2.RequestHandler):
    def handle_exception(self, exc, debug):
        logging.exception(exc) #log the error
        response.write("An error occurrred") #write message

        if isinstance(exc, webapp2.HTTPException):
            response.set_status(exc.code)
        else:
            response.set_status(500)

class HomeHandler(BaseHandler):
    def get(self):
        self.response.write('This is the HomeHandler.')

#define error handler when page is not found
def handle_404(req, res, exc):
    logging.exception(exc)
    res.write("Weird, something went wrong and PAGE NOT FOUND! Check URL.")
    res.headers["Status"] = "404 Not Found"
    res.set_status(404)

#define error handler when server error
def handle_500(req, res, exc):
    logging.exception(exc)
    res.write("A server error took place! URL not found.")
    res.headers["Status"] = "500 Internal Server Error"
    res.set_status(500)

#create the boat Boat class with given properties
class Boat(ndb.Model):
    id = ndb.StringProperty()
    name = ndb.StringProperty()
    type = ndb.StringProperty()
    length = ndb.IntegerProperty()
    at_sea = ndb.BooleanProperty()

#boat handler
class BoatHandler(webapp2.RequestHandler):
    def post(self):
        parent_key = ndb.Key(Boat, "parent_boat") #key is of kind 'Boat' and id (name) is parent_boat
        boat_data = json.loads(self.request.body) #put request body into json object
        
        #create a new boat and assign it the values from the boat_data. Set 'at_sea' to true and set
        #    parent_key to the parent_key value we created earlier
        new_boat = Boat(id=None, name=boat_data["name"], type=boat_data["type"], length=boat_data["length"], 
            at_sea=True, parent=parent_key)
        
        new_boat.put()
        new_boat.id = new_boat.key.urlsafe()
        new_boat.put()
        boat_dict = new_boat.to_dict() #use to_dict() function to convert new_boat    
        self.response.headers["Status"] = "201 Created"
        self.response.write(json.dumps(boat_dict)) #write the new boat that was made
    
    def get(self, id=None):
        if id:  #if an id exists
            b = ndb.Key(urlsafe=id).get() #get key value
            b_d = b.to_dict()
            self.response.headers["Status"] = "200 OK"
            self.response.write(json.dumps(b_d)) #write 

    #Deleting a ship should empty the slip the boat was previously in
    def delete(self, id=None):
        if id:
            b = ndb.Key(urlsafe=id).get()

            #check if boat is at_sea, if it isn't 
            if b.at_sea == False:
                #query slips for current boat equal to the id we just got
                query = Slip.query(Slip.current_boat == b.id)
                value = query.fetch(limit=1) 
                
                #empty the slip the boat was previously in
                for i in value:
                    i.current_boat == None 
                    i.arrival_date == None
                    i.put() 
                b.key.delete()
                self.response.headers["Status"] = "204 No Content"
                self.response.write("Boat deleted.")
            else:
                b.key.delete()
                self.response.headers["Status"] = "204 No Content"
                self.response.write("Boat deleted.")

    def patch(self, id=None):
        if id:
            b = ndb.Key(urlsafe=id).get()
            boat_data = json.loads(self.request.body)

            #check the data to see if it matches any values in boat values
            if "name" in boat_data:
                b.name = boat_data["name"]
            if "type" in boat_data:
                b.type = boat_data["type"]
            if "length" in boat_data:
                b.length = boat_data["length"]
            b.put()
            b_d = b.to_dict()
            self.response.headers["Status"] = "200 OK"
            self.response.write(json.dumps(b_d))
    
    def put(self, id=None):
        if id:
            b = ndb.Key(urlsafe=id).get()
            boat_data = json.loads(self.request.body)
            
            #check if name variable exists
            if "name" in boat_data:
                b.name = boat_data["name"]
            else:
                b.name = None

            #check if type variable exists
            if "type" in boat_data:
                b.type = boat_data["type"]
            else:
                b.type = None
            
            #check if length variable exists in data
            if "length" in boat_data:
                b.length = boat_data["length"]
            else:
                b.length = None
            
            b.put()
            b_d = b.to_dict()
            self.response.headers["Status"] = "200 OK"
            self.response.write(json.dumps(b_d))
                
class getEveryBoat(webapp2.RequestHandler):
    def get(self):
        query = Boat.query()

        #get at most 200 boats
        values = query.fetch(limit=200)
        boats = [] #create empty list to store boat dicts

        for i in values:
            boats.append({"id": i.id, "name": i.name, "type": i.type, "length": i.length, "at_sea": i.at_sea})
        #write the entire array 
        self.response.headers["Status"] = "200 OK"
        self.response.write(json.dumps(boats))

         

#create Slip class with given properties             
class Slip(ndb.Model):
    id = ndb.StringProperty()
    number = ndb.IntegerProperty()
    current_boat = ndb.StringProperty()
    arrival_date = ndb.StringProperty()
    departure_history = ndb.StringProperty()
    departure_date = ndb.StringProperty()
    departed_boat = ndb.StringProperty()

class SlipHandler(webapp2.RequestHandler):
    def post(self):
        parent_key = ndb.Key(Slip, "parent_slip") #Key is of type Slip, and key name is parent_slip
        slip_data = json.loads(self.request.body)
        list = [] 

        new_slip = Slip(id=None, number=getSlipCount(), current_boat=None, arrival_date=None,
            departure_history=None, departure_date=None, departed_boat=None, parent=parent_key)
        new_slip.put()
        new_slip.id = new_slip.key.urlsafe()
        new_slip.put()
        s_d = new_slip.to_dict()

        #create a nested dictionary inside of our dict we just created 
        s_d['departure_history'] = {}
        s_d['departure_history']['departure_date'] = new_slip.departure_date
        s_d['departure_history']['departed_boat'] = new_slip.departed_boat

        #use del to delete those places leaving them empty
        del s_d['departure_date']
        del s_d['departed_boat']
        self.response.headers["Status"] = "201 Created"
        self.response.write(json.dumps(s_d)) #write

    def get(self, id=None):
        if id:
            s = ndb.Key(urlsafe=id).get()
            s_d = s.to_dict()
            
            #create nested dict and stored the data into it
            s_d['departure_history'] = {}
            s_d['departure_history']['departure_date'] = s.departure_date
            s_d['departure_history']['departed_boat'] = s.departed_boat

            #delete 
            del s_d['departed_boat']
            del s_d['departure_date']
            self.response.headers["Status"] = "200 OK"
            self.response.write(json.dumps(s_d))

    def delete(self, id=None):
        if id:
            s = ndb.Key(urlsafe=id).get()

            #check if a boat is docked in the slip. If there is
            #then the boat needs to be set to "at_sea": true, then delete slip
            if s.current_boat != None:
                b_d = None
                query = Boat.query(Boat.at_sea == False) #get boats that aren't at sea
                values = query.fetch(limit = 200)
                for i in values:
                    if i.current_boat == i.id:
                        i.at_sea = True
                        i.put()
                s.key.delete()
                self.response.headers["Status"] = "204 No Content"
                self.response.write("Slip Deleted")

            #no boat at sea we can just delete slip
            else: 
                s.key.delete()
                self.response.headers["Status"] = "204 No Content"
                self.response.write("Slip Deleted")

    def patch(self, id=None):
        if id:
            s = ndb.Key(urlsafe=id).get()
            s_d = json.loads(self.request.body)

            #check if a number var exists in the reqest
            if "number" in s_d:
                #check if number is in use, if it is ,give new number
                #   else, set the number equal to the request
                query = Slip.query()
                values = query.fetch(limit=200)
                if s.number in values:
                    s.number = getSlipCount() #if found set it equal to new slipCount
                else:
                    s.number = s_d["number"]

            #check if current_boat is in the data    
            if "current_boat" in s_d:
                #check if the slip has a current boat, if it doesnt give the one passed
                if s.current_boat == None:
                    s.current_boat = s_d["current_boat"]
                else:
                    #check 
                    query = Boat.query(Boat.id == s_d["current_boat"])
                    value = query.fetch(limit=1) #get a single result if mathced
                    if "at_sea" in value:
                        value.at_sea = False #set boat to not at sea (false)
                    s.current_boat = s_d["current_boat"] #set the slips current boat
            
            #check if these are specified in request, if not leave the same
            if "arrival_date" in s_d:
                s.arrival_date = s_d["arrival_date"]    
            if "departed_boat" in s_d:
                s.departed_boat = s_d["departed_boat"]
            if "departure_date" in s_d:
                s.departure_date = s_d["departure_date"]
            s.put()
            s_dict = s.to_dict()
            del s_dict["departure_history"]
            self.response.headers["Status"] = "200 OK"
            self.response.write(json.dumps(s_dict))
    
    def put(self, id=None):
        s = ndb.Key(urlsafe=id).get()
        s_d = json.loads(self.request.body)

        #check if request specified a number
        if "number" in s_d:
            query = Slip.query()
            values = query.fetch(limit=200)
            for i in values:
                #if the number is contained inside of the query, we need to get a new one
                if s_d["number"] == s.number:
                    s.number = getSlipCount()
                else:
                    s.number = s_d["number"]
        
        if "current_boat" in s_d:
            if s.current_boat == None: #if no boat assigned to slip
                s.current_boat = s_d["current_boat"]
            else:
                #get id of the boat to put into slip
                query.Boat.query(Boat.id == s_d["current_boat"])
                value = query.fetch(limit=1) #get the 1 result
                if "at_sea" in value:
                    #set the value to false (they are in slip)
                    value.at_sea = False 
                s.current_boat = s_d["current_boat"]
        #no boat assigned in req, so put current to none
        else:
            s.current_boat = None
        
        #check for arrival date in request
        if "arrival_date" in s_d:
            s.arrival_date = s_d["arrival_date"]
        else:
            s.arrival_date = None
        
        #check for departed boat in request
        if "departed_boat" in s_d:
            s.departed_boat = s_d["departed_boat"]
        else:
            s.departed_boat = None
        
        #check for departure date in request
        if "departure_date" in s_d:
            s.departure_date = s_d["departure_date"]
        else:
            s.departure_date = None
        
        s.put()
        s_dict = s.to_dict()
        del s_d["departure_history"]
        self.response.headers["Status"] = "200 OK"
        self.response.write(json.dumps(s_d))

class getEverySlip(webapp2.RequestHandler):
    def get(self):
        query = Slip.query()
        values = query.fetch(limit=200)
        slipList = []
        counter = 0
        for i in values:
            slipList.append({"id": i.id, "number": i.number, "current_boat":i.current_boat, "arrival_date": i.arrival_date,
                    "departure_history": i.departure_history})
            #access the inner json
            slipList[counter]["departure_history"] = ({"departure_date": i.departure_date, "departed_boat": i.departed_boat})
        #write data (list)
        counter += 1
        self.response.headers["Status"] = "200 OK"
        self.response.write(json.dumps(slipList))

class BoatArrival(webapp2.RequestHandler):
    def put(self, id=None):        
        if id:
            toDockBoat = ndb.Key(urlsafe=id).get()
            request = json.loads(self.request.body)
            #query for the slip number that was in request
            query = Slip.query(Slip.number == request["number"])
            value = query.fetch()
            for i in value:
                #if no boat in slip set boat
                if i.current_boat == None:
                    i.current_boat = toDockBoat.id
                    i.arrival_date = datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y")
                    i.put()
                    s_d = i.to_dict()
                    toDockBoat.at_sea = False
                    toDockBoat.put()
                    self.response.headers["Status"] = "200 OK"
                    self.response.write(json.dumps(s_d))
                #slip is currently in use, cant dock boat
            else:
                self.response.headers["Status"] = "200 OK"
                self.response.write("Error: 403 Forbidden. Slip is currently occupied.")
    
    def patch(self, id=None):
        if id:
            #Boat departure that leaves slip, and returns slip details
            boatDepart = ndb.Key(urlsafe=id).get()
            request = json.loads(self.request.body)
            boatDepart.at_sea = True #set at_sea to True (left slip)
            boatDepart.put()
            query = Slip.query(Slip.number == request["number"])
            value = query.fetch(limit=1)
            
            #remove the boat and set other values
            for i in value:     
                i.current_boat = None
                i.arrival_date = None
                i.departure_date = datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y")
                i.departed_boat = boatDepart.id 
                i.put()
                s_d = i.to_dict()
                del s_d["departure_history"]
                self.response.headers["Status"] = "200 OK"                    
                self.response.write(json.dumps(s_d))

      

class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.headers["Status"] = "200 OK"
        self.response.write("Boats 'N Slips")

#used to allow 'patch' requests
allowed_methods = webapp2.WSGIApplication.allowed_methods
new_allowed_methods = allowed_methods.union(('PATCH',))
webapp2.WSGIApplication.allowed_methods = new_allowed_methods

app = webapp2.WSGIApplication([
    
    ('/', MainPage),
    ('/boat', BoatHandler),
    ('/boat/', BoatHandler),
    ('/boat/(.*)', BoatHandler),
    ('/allboats', getEveryBoat),
    ('/slip', SlipHandler),
    ('/slip/', SlipHandler),
    ('/slip/(.*)', SlipHandler),
    ('/allslips', getEverySlip),
    ('/boatarrival/boat/(.*)', BoatArrival),

    webapp2.Route("/", handler="handlers.HomeHandler", name="home")
], debug=True)
app.error_handlers[404] = handle_404
app.error_handlers[500] = handle_500