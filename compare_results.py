import pandas as pd 
from dateutil.parser import parse
def try_parse(string):
  try:
    return parse(string)
  except:
    return "Not a Date"



actual = pd.read_csv('actual_answers.csv')
predictions = pd.read_csv('Predictions.csv')
predictions['ids'] = predictions.ids.apply(lambda x: ''.join([i for i in x if i.isdigit()]))
predictions.ids = predictions.ids.apply(int)

predictions = predictions.merge(actual, left_on="ids", right_on="ID", how='left')

predictions['location_correct'] = predictions.location_pred == predictions['Event location']
predictions['event_correct'] = predictions.event_pred == predictions['Event Name']
predictions['event_date_correct'] = predictions.event_date_pred.apply(try_parse) == predictions['Event Date'].apply(try_parse)
predictions['notification_correct'] = predictions.notification_date_pred.apply(try_parse) == predictions['Notification deadline'].apply(try_parse)
predictions['submission_correct'] = predictions.submission_date_pred.apply(try_parse) == predictions['Submission deadline'].apply(try_parse)



d = len(predictions)

print("Location Accuracy: ", predictions.location_correct.sum()/d)
print("Event Name Accuracy: ", predictions['event_correct'].sum()/d)
print("Event Date Accuracy:", predictions['event_date_correct'].sum()/d)
print("Notificaion Accuracy: ", predictions['notification_correct'].sum()/d)
print("Submission Accuracy: ", predictions['submission_correct'].sum()/d)




