#imports and stuff

import datefinder
from dateutil.parser import parse
import nltk
from os import listdir

import pandas as pd 
import pickle
nltk.download('punkt')
import spacy
import numpy as np
from datefinder import find_dates
import email

from string import punctuation
import re
import glob
import html2text
from string import punctuation
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.stem import PorterStemmer
from statistics import mode
from copy import deepcopy
from pprint import pprint

import spacy
nltk.download('averaged_perceptron_tagger')
nlp = spacy.load('en')

#email imports
import re
import email
from email import policy
from email.parser import BytesParser
from email.message import EmailMessage
import glob
import html2text
from bs4 import BeautifulSoup

import urllib.request

class LocationDictSetup:
  def __init__(self):
    self.separated_city_list = []
    self.city_country = []
    self.city_dict = {}
    self.country_dict = {}
    self.india_list = []
    self.us_state_list = []
    self.location_setup()

  def location_setup(self):
    #Maybe make a dictonary of city: country so we can just look it up
    massive_city_file = urllib.request.urlopen("https://raw.githubusercontent.com/datasets/world-cities/master/data/world-cities.csv")
    contents = massive_city_file.readlines()
    # print(contents)
    new_list = []
    city_country = []
    city_country.append("Zurich,Switzerland")
    city_country.append("Lodz,Poland")
    for pair in contents:
      new_pair = pair.decode("utf-8")
      no_newlines = new_pair.replace("\n", "")
      no_newlines.strip()
      comma_split = no_newlines.split(",")
      for e in comma_split:
        if not e.isdigit():
          new_list.append(e)
      city_country.append(str(comma_split[0]) + "," + str(comma_split[1]))
      if str(comma_split[0]) not in self.city_dict.keys():
        self.city_dict[str(comma_split[0])] = []
      self.city_dict[str(comma_split[0])].append(str(comma_split[1]))
      if str(comma_split[1]) not in self.country_dict.keys():
        self.country_dict[str(comma_split[1])] = []
      self.country_dict[str(comma_split[1])].append(str(comma_split[0]))

      if str(comma_split[1]).lower() == "india":
        india_tuple = (comma_split[0], comma_split[2], comma_split[1])
        if india_tuple not in set(self.india_list):
          self.india_list.append(india_tuple)
          if str(comma_split[2]) == "NCT":
            india_tuple = (comma_split[0], "NCR", comma_split[1])
            self.india_list.append(india_tuple)

      if str(comma_split[1]).lower() == "united states":
        us_tuple = (comma_split[0], comma_split[2])
        if us_tuple not in set(self.us_state_list):
          self.us_state_list.append(us_tuple)
    #print(self.us_state_list)
    #print(set(new_list))
    #print(set(self.city_dict))
    #print(set(['New York']) & set(new_list))
    #print(set(['Athens,Greece']) & set(city_country))
    self.separated_city_list = new_list
    self.city_country = city_country



#I reworked your logic above into individual functions
class Sentence:
  def __init__(self, text):
    text.replace("\n", " ")
    #text.replace("\r", " ")
    doc = nlp(text)

    self.text = text.replace("\n", " ")
   
    #self.text.replace("\r", " ")
    self.dates = []
    self.locations = []
    self.events = []
    #fills above lists with the appropriate tags
    self.get_tags()

  def get_tags(self):

    #doc = nlp(self.text)
    doc = nlp(self.text)
    #doc = nlp(self.text.replace('\r', " "))
    
    # Try with original parsing method
    e_list = self.get_event_tags2(self.text)
    if len(e_list) >0:
      self.events.extend(e_list )
    else:
      e_list = self.get_event_tags2(re.sub('\r\n', '', self.text))
      if len(e_list) >0:
        self.events.extend(e_list)
    

    ents = doc.ents
    for ent in ents:
      #print(ent.text, ent.label_)
      self.get_loc_tags(ent)
     # self.get_event_tags(ent)
      self.get_date_tags(ent)


  def get_loc_tags(self, ent):
    #logic looking for loacations **************
    if ent.label_ == "GPE":
      if not self.contains_digit(ent.text) and not self.is_font_name(ent.text) and not self.is_common_incorrect_loc_name(ent.text):
        if ent.text not in self.locations:
          self.locations.append(ent.text)

  def get_event_tags(self, ent):
    #logic looking for Conference Names ********************
    if ent.label_ == "EVENT" or ( ent.label_ == "ORG" and ent.text.lower().find("conference") !=-1 ):#might need to do something with org
      self.events.append(ent.text)



  def get_event_tags2(self, n_text):
  #  n_text = re.sub('<.*>','', n_text)
    n_tags = nltk.pos_tag(n_text.split())

    e_possible = False
    e_list = []
    curr = 0
    matches = ["Conference", "Symposium", "Congress", "Journal"]
    reminder = ["Reminder", "Speech", "Highlight"]
    months = ["January", "February", "March", "April", "May", "June", "July", "August", 'September', 'October', 'November', 'December',"Vancouver" ]

    for x in n_tags:
      if e_possible ==False and x[0].find(">")==-1 and (x[1] in ["DT", "CD", "JJ"] or x[0] == "International" or x[0].find("Asia") !=-1 or re.match(r'2[0-9][0-9][0-9]', x[0]) != None):
        e_possible = True
        e_list.append(x[0])
        continue

      elif e_possible == False :
        continue
      elif e_possible  and   (x[1] in ["NNP","IN", "CC", "CD" , "JJ"] and x[0] not in months  ) and len(re.findall(r'\([A-Z][a-z]*',x[0])) ==0 and   re.match(r'2[0-9][0-9][0-9]', x[0])==None and  re.match(r'\(.*\)', x[0])==None:
        e_list[curr]+=(" "+x[0])
      else:
        if re.match(r'2[0-9][0-9][0-9]', x[0]) != None or re.match(r'\(.*\)', x[0])!=None:
          e_list[curr]+=(" "+x[0])

        #Check if it's a conference or not
        if  any(x in e_list[curr] for x in matches)  and not any(x in e_list[curr] for x in reminder) and len(e_list[curr]) <=150 and len(e_list[curr].split()) > 5 and e_list[curr].find("University") ==-1:
          curr+=1
          re.sub('[\r\n]', '', e_list[curr-1])
          re.sub(' *', ' ', e_list[curr-1])
        elif len(e_list) >0:
          e_list.pop(curr)
        e_possible = False

    #Check if it's a conference or not
    if e_possible == True:
      if  any(x in e_list[curr] for x in matches):
        curr+=1
        re.sub('[\r\n]', '', e_list[curr-1])
        re.sub(' *', ' ', e_list[curr-1])
      elif len(e_list) >0:
        e_list.pop(curr)
      e_possible = False
    return e_list



  def get_date_tags(self, ent):
    #logic looking for Dates ***********************
    if ent.label_ == "DATE":
      if self.contains_letter(ent.text):
        self.dates.append(ent.text)

  def is_common_incorrect_loc_name(self, text):
    names = ["IEEE", "Blockchain", "san\r"]
    for n in names:
      if text.find(n) != -1:
        return True
    return False

  def is_font_name(self, text):
    fonts = ["Helvetica", "Arial"]
    for f in fonts: 
      if text.find(f) != -1:
        return True
    return False

  def contains_digit(self, text):
    return any(c.isdigit() for c in text)

  def contains_letter(self, text):
    return any(c.isalpha() for c in text)

  def is_empty(self):
    return self.dates == [] and self.locations == [] and self.events == []

  
  def enough_info_for_loacation(self):
    return (self.dates != [] and self.locations != [])\
     or (self.dates != [] and self.locations != [] and self.events != [])

  
  def __eq__(self, other):
    return self.events == other.events and self.locations == other.locations and self.dates == other.dates

  def __repr__(self):
    return f"\n Events Found: {self.events} \n Dates Found: {self.dates} \n Locations Found: {self.locations}"





locInfo = LocationDictSetup()

class emailParser: 
  """Class that will take in the email's text body as a parameter. The main method
  will tokenize the email into sentences. Then parse that sentence into sentence objects
  using the sentence class. And then take data from the sentence class to determine 
  what the attributes we want. And returns a Results class."""
  def __init__(self, email_file_path, id):
    subject_line, body = self.email_to_text(email_file_path)
    self.id = id
    self.email_body = body
    self.subject_line = subject_line
    self.paragraph_tokens = self.email_body.split('\n\n')
    
    self.sent_classes = self.get_sentence_classes() #list of sentence classes
    self.possible_dates = []


    self.separated_city_list = locInfo.separated_city_list
    self.city_country = locInfo.city_country
    self.city_dict = locInfo.city_dict
    self.country_dict = locInfo.country_dict
    self.india_list = locInfo.india_list
    self.us_state_list = locInfo.us_state_list

    self.possible_event_names = [] #contains sentence object, that may contain event
    self.possible_locations = [] #contains sentence object, that may contain location
    self.possible_event_dates = [] #contains sentence object, that may contain event date
    self.possible_submission_deadlines = [] #contains sentence object, that may contain submission deadline
    self.possible_notification_deadlines = [] #contains sentence object, that may contain submission deadline
    # self.results = results() #our final results class which we will return at the end 


    self.submission_pred = None
    self.notificaiton_pred = None
    self.event_date_pred = None


  def is_conference(self):
    conference_count = self.count_frequency('conference')
    conference_count += self.count_frequency('congress')
    journal_count = self.count_frequency('journal')
    if journal_count > conference_count:
      return False
    return True

  def count_frequency(self, word):
    count = 0
    for sent in self.sent_classes:
      clean_text_tokens = self.clean_text(sent.text)
      count += clean_text_tokens.count(word)

    return count


  def clean_text(self, text):
    for p in punctuation:
      text = text.replace(p, '')
    
    text = text.lower()
    tokens = word_tokenize(text)
    ps = PorterStemmer()
    clean_tokens = []
    for token in tokens:
      clean_tokens.append(ps.stem(token))
    return clean_tokens

  def email_to_text(self, filename):
    fname= 'drive/My Drive/id326.eml'
    print(filename)
    with open(filename, 'rb') as fp:  # select a specific email file from the list
        txt = fp.read()
        msg = email.message_from_bytes(txt, policy=policy.default)

    h = html2text.HTML2Text()
    h.ignore_links = True

    subject= msg['Subject']

    body= ""

    if msg.is_multipart():
        for payload in msg.get_payload():
            body = h.handle(payload.get_payload())
    else:
        #body = b.get_payload() <-- what's b supposed to be?
        body = msg.get_payload()

    #fixing parsing errors
    body = re.sub('=[EB][DF]', "", body)
    body = re.sub('\**',"",body)
    body = re.sub('<.*>',"", body)
    body = re.sub('= *',"", body)
    body = re.sub('\!\[.*\)','', body)
    body = re.sub('\\\.','',body)
    body = re.sub('\r','',body)
    #Comment it out if need be
    body = re.sub(r'<[^>]*?>', ' ', body)

    return (subject, body)

  def remove_html_tags(self, text):
    """Remove html tags from a string"""
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

  def main_loop(self):
    #main loop
    self.get_sentence_classes()

    self.get_events() #adds the relevant sentence object to self.possible_events
    location = self.get_locations() #adds the relevant sentence object to self.possible_locations
    self.get_dates() #adds the relevant sentence object to self.possible_dates
    self.determine_email_type()

    self.determine_date() #makes changes to results object attribute
    self.determine_location() #makes changes to results object attribute
    self.determine_event() #makes changes to results object attribute
  
  
  def get_sentence_classes(self):
    """Tokenizes the email body into seperate sentences. Then will make each corresponding
    sentence into a sentence class.
    
    sentence_objects = []
    for paragraph in self.paragraph_tokens:
      sent_tokens = nltk.sent_tokenize(self.email_body)

      for sentence in sent_tokens:
        if Sentence(sentence) not in sentence_objects:
          sentence_objects.append(Sentence(sentence))

    return sentence_objects
    """

    email_sentences = nltk.sent_tokenize(self.subject_line+"\n"+self.email_body) #returns list of strings. Each string corresponds to 1 sentence in email
    sentence_objects = []
    for i, sentence in enumerate(email_sentences):
      sentence_objects.append(Sentence(sentence))
    return sentence_objects

  def get_events(self):
    for s_obj in self.sent_classes:
      if len(s_obj.event) != 0:
        self.possible_event_names.append(s_obj)
  
  def get_locations(self):
    # print("POSSIBLE LOCATIONS")
    for s_obj in self.sent_classes:
      if len(s_obj.locations) != 0 and s_obj not in self.possible_locations:
        self.possible_locations.append(s_obj)
    #print(self.possible_locations)
    #print("-------------------------")

  def determine_location(self):
    event_date_location = []
    date_location = []
    for s in self.sent_classes:
      if s.enough_info_for_loacation():
        if s.events != []:
          event_date_location.append(s)
        else:
          date_location.append(s)

    selectedNode = None
    if len(event_date_location) == 1:
      selectedNode = list(event_date_location)[0]
    elif len(event_date_location) > 1:
      is_equal = True
      curr = list(event_date_location)[0]
      for conf in event_date_location:
        if curr != conf:
          is_equal = False
      if is_equal:
        selectedNode = list(event_date_location)[0]
      else:
        # print("OUCH1")
        # print(event_date_location)
        selectedNode = list(event_date_location)[0]
    else:
      if len(date_location) == 1:
        selectedNode = list(date_location)[0]
      elif len(date_location) > 1:
        is_equal = True
        curr = date_location[0]
        for conf in date_location:
          if curr != conf:
            is_equal = False
        if is_equal:
          selectedNode = list(date_location)[0]
        else:
          # print("OUCH2")
          # print(date_location)
          selectedNode = list(date_location)[0]
      else:
        selectedNode = None
    
    if selectedNode is None and len(self.possible_locations) == 1:
      selectedNode = self.possible_locations[0]

    #print("SELECTED NODE")
    #print(selectedNode)
    
    finalCity = ""
    if selectedNode is None:
      return "No Location Found!"
    else:
      locations = self.ensure_loactions_are_valid(selectedNode)
      det_city = self.find_city_name(selectedNode.text, locations)
      if det_city == None:
        return "No location found!"
      else:
        return det_city


  def ensure_loactions_are_valid(self, sent):
    new_locs = []
    for l in sent.locations:
      if l in set(self.separated_city_list) or l == "Lodz" or l == "Zurich":
        new_locs.append(l) 
    return new_locs

  # got regex cleaning from
  # https://stackoverflow.com/questions/34860982/replace-the-punctuation-with-whitespace/34922745
  def find_city_name(self, text, locs):
    #print("TEXT:")
    #print(text)
    #print("LOCATION:")
    #print(locs)
    clean = re.sub(r"""
            [,.;@#?!&$\-\[\]\"]+  # Accept one or more copies of punctuation
            \ *           # plus zero or more copies of a space,
            """,
            " ",          # and replace it with a single space
            text, flags=re.VERBOSE)
    clean = clean.lower()
    clean = clean.split()
    len_of_locs = len(locs)
    final_location = ""
    highest_n_gram = 0
    #print(len_of_locs)
    if "India" in set(locs):
      if len(locs) == 3:
        trigrams = nltk.trigrams(locs)
        for t in trigrams:
          #print("TRIGRAM")
          #print(t)
          if t in set(self.india_list):
            final_location = ", ".join(t)
    if final_location == "":
      if len_of_locs == 1:
        if locs[0] in text:
          final_location = str(locs[0])
        highest_n_gram = 1
      else:
        for i in range(len_of_locs):
          ngrams = nltk.ngrams(locs, i+1)
          for n in ngrams:
            #print(n)
            if i == 0:
              if set(n[0]) & set(self.separated_city_list):
                final_location = str(n[0])
                highest_n_gram = 1
            else:
              city_state = ",".join(n)
              # print("CITY STATE")
              # print(city_state)
              # print(set([city_state]) & set(self.city_country))
              if set([city_state]) & set(self.city_country):
                #final_location = city_state
                final_location = ", ".join(n)
                highest_n_gram = i+1
                # print("ACCEPTED")
              
              if set([n]) & set(self.us_state_list):
                final_location = str(n[0])
                final_location += ", USA"
                highest_n_gram = i+1
              
    # print(highest_n_gram)
    if highest_n_gram == 1:
      # print("VALS")
      vals = []
      country_vals = False
      if final_location in set(self.city_dict):
        vals = self.city_dict[final_location]
      elif final_location in set(self.country_dict):
        vals = self.country_dict[final_location]
        country_vals = True
      # print(vals)
      if len(vals) <= 1:
        if len(vals) == 0:
          final_location = ""
        if len(vals) == 1:
          final_location += ", "
          final_location += str(vals[0])
      else:
        highest_val = 0
        corresponding_city = vals[0]
        for v in vals:
          c_count = clean.count(v.lower())
          if c_count > highest_val:
            highest_val = c_count
            corresponding_city = v
        if country_vals:
          new_final = ""
          if highest_val > 0:
            new_final = str(corresponding_city)
            new_final += ", "
          new_final += final_location
          final_location = new_final
        else:
          if highest_val > 0:
            final_location += ", "
            final_location += str(corresponding_city)
    # print("FINAL LOCATION: " + final_location)
    if final_location.find("United States") != -1:
      new_final_loc_arr = final_location.split(",")
      new_final_loc_arr[1] = "USA"
      final_location = ", ".join(new_final_loc_arr)
    if final_location.find("United Arab Emirates") != -1:
      new_final_loc_arr = final_location.split(",")
      new_final_loc_arr[1] = "UAE"
      final_location = ", ".join(new_final_loc_arr)
    if final_location.find("United Kingdom") != -1:
      new_final_loc_arr = final_location.split(",")
      new_final_loc_arr[1] = "UK"
      final_location = ", ".join(new_final_loc_arr)
    return final_location

  def get_dates(self):
    for sent in self.sent_classes:
      if len(sent.dates) > 0:
        self.possible_dates.append(sent)
  
  
  def mode(self, iterable):
    unique = set(iterable)
    counts = [(iterable.count(val), val) for val in unique]
    most = max(counts)
    return most[1]
  

 
    
  def determine_dates(self):
    all_dates = []
    self.get_dates()
    for sent in self.possible_dates:
      for date in sent.dates:
        correct_format = re.findall(r'\d+, 2[0-9][0-9][0-9]', date)
        if correct_format:
          all_dates.append(date)
    
    #removes duplicates
    all_dates = sorted(set(all_dates), key=all_dates.index)
    #if we literally can't find 3 dates, we'll just remove
    if len(all_dates) < 3:
      return 
    

    relevant_dates = all_dates[:3] #first 3 dates are what we care about
    relevant_dts = []


    most_likely_event_date = None
    for date in relevant_dates:
      #just in case, we'll take the event date as is
      event_pattern_found = re.findall(r'\d+ *- *\d+', date)
      if event_pattern_found:
        most_likely_event_date = date

      date = re.sub(r' *- *\d+', '', date) #removing the hyphens where we find them
      date = date.strip(' ;:,."/[]{}')
      try:
        relevant_dts.append(parse(date))
      except:
        continue #if we can't parse it, we can't use it 

    #if all goes according to plan
    if len(relevant_dts) == 3:
      relevant_dts.sort()
      self.submission_pred = relevant_dts[0].strftime("%B %d, %Y")
      self.notificaiton_pred = relevant_dts[1].strftime("%B %d, %Y")
      self.event_date_pred = relevant_dts[2].strftime("%B %d, %Y")
      return

      
    #best guess on where they could be shown
    else:
      if most_likely_event_date is not None:
        self.event_date_pred = most_likely_event_date
        self.submission_pred = relevant_dates[1]
        self.notificaiton_pred = relevant_dates[2]
        return
      
      else:
        self.event_date_pred = relevant_dates[0] 
        self.submission_pred = relevant_dates[1]
        self.notificaiton_pred = relevant_dates[2]
        return


  def determine_events(self):
    pos_events = [] 
    for sent in self.possible_event_names:
      pos_events.extend(sent.events)
     
    if len(pos_events) ==0:
      return self.subject_line

    if len(list(set(pos_events))) >= 5:
      print("List of conferences")
      return "LOC"

    most_frequent = max(set(pos_events), key = pos_events.count)
    if pos_events.count(most_frequent) >1:
      return most_frequent

    maxEvent = max(list(set(pos_events)), key=len)
    return maxEvent
  

def write_pickle(filename, object_):
	pickling_on = open(f"{filename}.pickle", "wb")
	pickle.dump(object_, pickling_on)
	pickling_on.close()

def load_pickle(filename):
	pickle_off = open(f"{filename}", 'rb')
	object_ = pickle.load(pickle_off)
	return object_

if __name__ == '__main__':
	dir_ = 'pickle_emails'

	data = {"ids": [], "event_pred": [], "location_pred": [], "event_date_pred": [], "submission_date_pred": [], "notification_date_pred": []}
	for file in listdir(dir_):
		email_obj = load_pickle(f"{dir_}/{file}")
		email_obj.determine_dates()
		data['ids'].append(email_obj.id)

		email_obj.

		data['event_pred'].append(email_obj.determine_events())
		data['location_pred'].append(email_obj.determine_location())
		data['event_date_pred'].append(email_obj.event_date_pred)

		data['submission_date_pred'].append(email_obj.submission_pred)
		data['notification_date_pred'].append(email_obj.notificaiton_pred)

	
	our_predictions = pd.DataFrame(data)

	our_predictions.to_csv("Predictions.csv")
















	#for writing pickles
	# dir_ = 'conf_emails_numbered'

	# for file in listdir(dir_):
	# 	file_name = f"{dir_}/{file}"
	# 	print(file)
	# 	try:
	# 		parser = emailParser(file_name, file)
	# 	except Exception as ex:
	# 		print(f"Error: {ex}")

	# 	write_pickle(f"pickle_emails/{file}", parser)




