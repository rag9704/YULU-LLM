import requests
import ast
import json
from dotenv import load_dotenv
import os 

load_dotenv()



headers = {
    'Authorization': os.environ['bot_token'],
    'Accept-Language': 'en',
    'Content-Type': 'application/json',
    }

yulu_api_functions = [
    {
        "name": "user_status_check",
        'description': 'Get the current status of user',
        "parameters": {
            'type': 'object',
            "properties": {"user_id": {"type": "integer","description": "user id of user"},
                            'user_latitude': {'type': 'number','description': 'latitude of user'},
                            'user_longitude': {'type': 'number','description': 'longitude of user'},
                            'user_location_accuracy': {'type': 'number','description': 'location accuracy of user device'}               
                        }
        }
    },
    {
        'name': 'get_nearest_yuluzone',
        'description': 'Get the nearest yulu zone location using users location',
        'parameters': {
            'type': 'object',
            'properties': {
                'user_id': {
                    'type': 'integer',
                    'description': 'user id of user '
                },
                'user_latitude': {
                    'type': 'number',
                    'description': 'latitude of user'
                },
                'user_longitude': {
                    'type': 'number',
                    'description': 'longitude of user'
                },
                'user_location_accuracy': {
                    'type': 'number',
                    'description': 'location accuracy of user device'
                }               
            }
        }
    },
    {
        'name': 'can_end_ride',
        'description': 'check weather the user can end the ride with or without penalty.',
        'parameters': {
            'type': 'object',
            'properties': {
                'user_id': {
                    'type': 'integer',
                    'description': 'user id of user '
                },
                'user_latitude': {
                    'type': 'number',
                    'description': 'latitude of user'
                },
                'user_longitude': {
                    'type': 'number',
                    'description': 'longitude of user'
                },
                'user_location_accuracy': {
                    'type': 'number',
                    'description': 'location accuracy of user device'
                }               
            }
        }
    },
    {
        'name': 'location_check',
        'description': 'find the nearest charged vehicle, miracle or dex ,for user',
        'parameters': {
            'type': 'object',
            'properties': {
                'user_id': {
                    'type': 'integer',
                    'description': 'user id of user '
                },
                'user_latitude': {
                    'type': 'number',
                    'description': 'latitude of user'
                },
                'user_longitude': {
                    'type': 'number',
                    'description': 'longitude of user'
                },
                'user_location_accuracy': {
                    'type': 'number',
                    'description': 'location accuracy of user device'
                }               
            }
        }
    },
    {
        'name': 'battery_swap_charge',
        'description': 'returns the charge of battery swaps for user',
        'parameters': {
            'type': 'object',
            'properties': {    
            }
        }
    },
    {
        'name': 'extend_rental_plan', 
        'description': 'returns the steps to extend users rental plan',
        'parameters': {
            'type': 'object',
            'properties': {       
            }
        }
    },
    {
        "name": "get_nearest_ymax",
        'description': 'returns the nearest charging/YUMA/Y-Max/Battery swap station when asked',
        "parameters": {
            'type': 'object',
            "properties": {"user_id": {"type": "integer","description": "user id of user"},
                            'user_latitude': {'type': 'number','description': 'latitude of user'},
                            'user_longitude': {'type': 'number','description': 'longitude of user'},
                            'user_location_accuracy': {'type': 'number','description': 'location accuracy of user device'}               
                        }
        }
    },
]




def user_status_check(user_id,user_latitude,user_longitude,user_location_accuracy=0.0):
    json_data = {
    "user_id": user_id,
    "user_latitude": user_latitude,
    "user_longitude": user_longitude,
    "user_location_accuracy": user_location_accuracy}
    response = requests.post('https://ipa.passion.bike/s/user-type-check', headers=headers, json=json_data)
    return ast.literal_eval(response.text)['data']

def can_end_ride_flow(user_id,user_latitude,user_longitude,user_location_accuracy=0.0,ride="idle"):
    json_data = {
    "user_id": user_id,
    "user_latitude": user_latitude,
    "user_longitude": user_longitude,
    "user_location_accuracy": user_location_accuracy}
    #response = requests.post('https://ipa.passion.bike/s/can-end-ride', headers=headers, json=json_data)
    response = "bike is outside of the zone"
    #if ast.literal_eval(response.text)['message'] == "No Live Journey":
    if response =="No Live Journey":
        return """ If you are unable to your end your ride at a Yulu zone -2. Select the <b>‘End Ride’</b> button to end your ride.If you are unable to end the ride or not satisfied with the solution, reach out to us via the <b>‘Chat with us’</b> option."""
    elif response == "bike is outside of the zone":
        return 'test successfull'
        #return f"You are trying to park outside Yulu zone, for which {str(ast.literal_eval(response.text)['data']['EndRideWithPenality'])} rupees will be applied,You can park the bike to neareast Yulu Zone, {str(ast.literal_eval(response.text)['data']['Distance'])} mtrs away. {str(ast.literal_eval(response.text)['data']['LocateNearestZone'])}"
    elif response == "Ride ended successfully":
         return """ Ride ended successfully!!"""
        

def get_nearest_yuluzone(user_id,user_latitude,user_longitude,user_location_accuracy=0.0):
    json_data = {
    "user_id": user_id,
    "user_latitude": user_latitude,
    "user_longitude": user_longitude,
    "user_location_accuracy": user_location_accuracy}
    response = requests.post('https://ipa.passion.bike/s/get-nearest-yuluzone', headers=headers, json=json_data)
    return str(ast.literal_eval(response.text)['data'][0]['map_link'])

def location_check(user_id,user_latitude,user_longitude,user_location_accuracy=0.0):
    json_data = {
    "user_id": user_id,
    "user_latitude": user_latitude,
    "user_longitude": user_longitude,
    "user_location_accuracy": user_location_accuracy}
    
    response = requests.post('https://ipa.passion.bike/s/location-check', headers=headers, json=json_data)
    response = ast.literal_eval(response.text)['data']
    if response[0]['bike_availability'] == 'true':
            response= (f"Sure, I can help you with that, Please tap on the link below to go to the nearest charged vehicle {str(response[0]['mapLink'])}")
    else:
            response= "Sorry, there are no vehicles available near your location."
    
    return response

def get_nearest_ymax(user_id,user_latitude,user_longitude,user_location_accuracy=0.0):
    json_data = {
    "user_id": user_id,
    "user_latitude": user_latitude,
    "user_longitude": user_longitude,
    "user_location_accuracy": user_location_accuracy}
    
    response = requests.post('https://ipa.passion.bike/s/get-nearest-ymax', headers=headers, json=json_data)
    response = json.loads(response.text)
    if response['data'][0]['zone_type'] == 'ymax':
        response= f"""Sure, I can help you with that, Please tap on the link below to go to the Y-Max station {response['data'][0]['map_link']}"""
    elif response['data'][0]['zone_type'] == 'yz':
        response = f"""Nearest Y-MAX station with battery is not available. Please return the nearest Yulu Zone map link to user : {response['data'][0]['map_link']}"""
    else:
        response ="""There's no Y-Max station or Yulu zone near you."""
    return response

def sd_refund_details_fetch(user_id,user_latitude,user_longitude,user_location_accuracy=0.0):   
         json_data = {
         "user_id": user_id,
         "user_latitude":user_latitude,
         "user_longitude": user_longitude,
         "user_location_accuracy": user_location_accuracy}
         response = requests.post('https://ipa.passion.bike/s/sd-refund-details-fetch', headers=headers, json=json_data)
         response = ast.literal_eval(response.text)['data'][0]['RefundDetails']
         if "Not Initiate" in response['refund_status']:
              return 'Security Deposit refund is not initiated'
         elif "Completed" in response['refund_status']:
              x = user_status_check(user_id,user_latitude,user_longitude)
              return f"""You initiated a refund for {response['refund_amount']} and refund was done on {x[0]['refund_expected_completion_date']} """
         elif "Processing" in response['refund_status']: 
              return f""" You requested a refund on {response['pg_requested_date']} for amount of {response['refund_amount']} & is expected to complete on {response['pg_expected_completion_date']} """
         
              
         #x={'refund_status':response['refund_status'],'payment gateway status' :response['pg_refund_status'],'refund_amount' : response['refund_amount']}
         #return response.text




def dte_check(user_id,latitude,longitude,user_location_accuracy=0.0): 
    json_data = {
    "user_id": user_id,
    "user_latitude":latitude,
    "user_longitude": longitude,
    "user_location_accuracy": user_location_accuracy}
    response = requests.post('https://ipa.passion.bike/s/dte-check', headers=headers, json=json_data)
    return response.text

def end_ride_with_penalty(user_id,user_latitude,user_longitude,user_location_accuracy=0.0):
    json_data = {
    "user_id": user_id,
    "user_latitude": user_latitude,
    "user_longitude": user_longitude,
    "user_location_accuracy": user_location_accuracy}
    
    #response = requests.post('https://ipa.passion.bike/s/lend-ride-with-penalty', headers=headers, json=json_data)
    #return ast.literal_eval(response.text)['message']
    return 'Ended ride with penalty!! test successfull'



## ----------------------------------------------------------------------------
    

def end_ride_with_penalty(user_id,user_latitude,user_longitude,user_location_accuracy=0.0):
    json_data = {
    "user_id": user_id,
    "user_latitude": user_latitude,
    "user_longitude": user_longitude,
    "user_location_accuracy": user_location_accuracy}
    
    response = requests.post('https://ipa.passion.bike/s/lend-ride-with-penalty', headers=headers, json=json_data)
    return ast.literal_eval(response.text)['data']

def pg_status_check(user_id,user_latitude,user_longitude,user_location_accuracy=0.0):
    json_data = {
    "user_id": user_id,
    "user_latitude": user_latitude,
    "user_longitude": user_longitude,
    "user_location_accuracy": user_location_accuracy}
    
    response = requests.post('https://ipa.passion.bike/s/lend-ride-with-penalty', headers=headers, json=json_data)
    return response.text
def sd_refund_status_check(user_id,user_latitude,user_longitude,user_location_accuracy=0.0):
    json_data = {
    "user_id": user_id,
    "user_latitude": user_latitude,
    "user_longitude": user_longitude,
    "user_location_accuracy": user_location_accuracy}
    
    response = requests.post('https://ipa.passion.bike/s/lend-ride-with-penalty', headers=headers, json=json_data)
    #return ast.literal_eval(response.text)['data']
    return response.text

def sd_refund_status_update(user_id,user_latitude,user_longitude,user_location_accuracy=0.0):
    json_data = {
    "user_id": user_id,
    "user_latitude": user_latitude,
    "user_longitude": user_longitude,
    "user_location_accuracy": user_location_accuracy}
    response = requests.post('https://ipa.passion.bike/s/lend-ride-with-penalty', headers=headers, json=json_data)
    #return ast.literal_eval(response.text)['data']
    return response.text

def sd_refund_details_fetch(user_id,user_latitude,user_longitude,user_location_accuracy=0.0):
    json_data = {
    "user_id": user_id,
    "user_latitude": user_latitude,
    "user_longitude": user_longitude,
    "user_location_accuracy": user_location_accuracy}
    
    response = requests.post('https://ipa.passion.bike/s/lend-ride-with-penalty', headers=headers, json=json_data)
    return ast.literal_eval(response.text)['data']



    

def dte_check(user_id,user_latitude,user_longitude,user_location_accuracy=0.0):
    json_data = {
    "user_id": user_id,
    "user_latitude": user_latitude,
    "user_longitude": user_longitude,
    "user_location_accuracy": user_location_accuracy}
    
    response = requests.post('https://ipa.passion.bike/s/lend-ride-with-penalty', headers=headers, json=json_data)
    return response.text



def get_nearest_yz_or_bike(user_id,user_latitude,user_longitude,user_location_accuracy=0.0):
    json_data = {
    "user_id": user_id,
    "user_latitude": user_latitude,
    "user_longitude": user_longitude,
    "user_location_accuracy": user_location_accuracy}
    
    response = requests.post('https://ipa.passion.bike/s/lend-ride-with-penalty', headers=headers, json=json_data)
    return ast.literal_eval(response.text)['data']

def ltr_ride_end(user_id,user_latitude,user_longitude,user_location_accuracy=0.0):
    json_data = {
    "user_id": user_id,
    "user_latitude": user_latitude,
    "user_longitude": user_longitude,
    "user_location_accuracy": user_location_accuracy}
    
    response = requests.post('https://ipa.passion.bike/s/lend-ride-with-penalty', headers=headers, json=json_data)
    return ast.literal_eval(response.text)['data']

def battery_swap_charge():
    
    return "Battery swap is FREE if your vehicle's range is less than 15km. If your vehicle's range is more than 15km you will be charged Rs.19."

def extend_rental_plan():
    return "To extend your rental plan, please tap on ‘Menu’ in the bottom bar and select ‘Extend Rental Plan’"




def pg_status_check(user_id,user_latitude,user_longitude,user_location_accuracy=0.0):
    json_data = {
    "user_id": user_id,
    "user_latitude": user_latitude,
    "user_longitude": user_longitude,
    "user_location_accuracy": user_location_accuracy}
    response = requests.post('https://ipa.passion.bike/s/sd-refund-status-check', headers=headers, json=json_data)
    return response.text

