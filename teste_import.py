from os import execlpe
from decouple import config
import requests

# api_url = 'https://api.clickup.com/api/v2/user'
api_url = 'https://api.clickup.com/api/v1/team'
api_key = config( 'API_KEY' )
headers = { 
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36 Edg/93.0.961.47',
    'Authorization': api_key 
    }

try:
    request = requests.get(api_url, verify = False, headers=headers)
except Exception as err:
    print(f'Erro de request: {err}')

if (request.status_code == 200):
    # user = request.json()['user']
    # username = user['username']
    team = request.json()['teams']
    team_name = team['name']


    # print(f'O usuário autorizado é: {username}')
    print(f'O time autorizado é: {team}')
else:
    print(f'response is fucked up: {request.status_code}')
