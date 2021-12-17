from decouple import config
import os
import json
import requests
import pandas as pd
import numpy as np
from requests import status_codes
import utilities as util

# API URL
API_ENDPOINT  = "https://api.clickup.com/api/v2/"
# API_ENDPOINT = "https://private-anon-ca0332bf87-clickup20.apiary-proxy.com/api/v2/"
USER_AGENT = config('USER_AGENT')
API_KEY = config('API_KEY')
TEAM_ID = config('TEAM_ID')
TIMEZONE = config('TIMEZONE')

#colunas que serão extraídas
columns_time_entries = [  'task_id', 'task_name',
                          'time_id', 'time_description', 'time_start', 'time_end', 'time_duration', 
                          'user_id', 'user_name']


# Função principal que será invocada no inicio

def main():

    print('Clickup timesheet report creator - Porquê usar a opçào nativa do Clickup é um pesadelo :). Cheers')
    print('======')
    start = input('Data início do período (Formato YYYY-MM-DD): ')
    end = input('Data final do período (padrão será hoje): ')
    members = get_team_members()
    print ("===\nGerar os relatórios?")

    #printa a lista com todos os usuários
    for i, member in enumerate(members, start=1):
        print(f"{i}: {member['username']}")
    
    chosen_member = input("Escolha um número(ou aperte enter para escolher todos): ")

    #retorna o id escolhido, ou concatena todos se não escolhido um
    assignee = members[int(chosen_member)-1]['id'] if chosen_member else ",".join([ str(member['id']) for member in members])

    start_ts = util.str_to_timestamp( start )
    end_ts = util.get_eod_timestamp( end )
    
    api_time_entries = f"{API_ENDPOINT}team/{TEAM_ID}/time_entries?start_date={start_ts}&end_date={end_ts}&assignee={assignee}"
    api_task = f"{API_ENDPOINT}task/"

    headers = {
        "User-Agent": USER_AGENT,
        "Authorization": API_KEY
    }

    # lê os apontamentos pelo API
    try:
        session = requests.session()
        r = session.get(api_time_entries, headers=headers)
    except Exception as e:
        print(f"Erro ao ler os apontamentos. Erro:{e}")
    
    #escreve o arquivo pela primeira ves
    time_entries = None

    if (r.status_code == 200):
        create_folder('data')
        create_folder('report')

        #escreve o arquivo json com o timesheet
        f = open('./data/time_entries.json', 'w')
        time_entries = r.json()
        f.write (r.text)
        f.close()
        print(f"===\nExiste {len(time_entries['data'])} apontamentos registrados no período que você escolheu")
    else:
        print ('Erro de resposta do Clickup. Status:', r.status_code)

    tasks = {}

    time_entries_rows = []
    
    #popula o objeto tasks com as tarefas do timesheet
    for time_entry in time_entries['data']:
        """
        checa se a task é bloqueada pra mim
        se for bloqueada pula a ação no loop
        !isso é temporário visto que estão mexendo
        na estrutura do Clickup
        """
        if(time_entry['task'] != '0'):
            tasks[time_entry['task']['id']] = time_entry['task']['name']

            #insere nova linha
            time_entries_rows.append([
                time_entry['task']['id'],
                time_entry['task']['name'],
                time_entry['id'],
                time_entry['description'],
                pd.to_datetime(time_entry['start'], unit='ms', utc=True).tz_convert( TIMEZONE),
                pd.to_datetime(time_entry['end'], unit='ms', utc=True).tz_convert( TIMEZONE),
                int(time_entry['duration']),
                time_entry['user']['id'],
                time_entry['user']['username']
            ])

    #cria um novo dataframe
    time_entries_df = pd.DataFrame(time_entries_rows, columns=columns_time_entries)

    print(f"E {len(tasks)} tarefas exportadas")

    # ===
    # hora de fazer iteração pra cada tarefa
    # pega as informações da tarefa e adiciona no dicionario.
    i = 0
    for task_id in tasks.keys():
        print(f"> {str(i+1).rjust(3)}/{len(tasks)} | Buscando info sobre a tarefa {task_id}: {tasks[task_id]}")

        t = requests.get(f"{api_task}{task_id}", headers=headers)
        tasks[task_id] = t.json()

        i += 1
    
    #Salva a lista de tarefas em um json separado
    with open('./data/tasks.json', 'w') as tasks_file:
        json.dump(tasks, tasks_file)
        tasks_file.close()
        
    # # lê as tarefas do arquivo
    # with open('./data/tasks.json', 'r') as tasks_r_file :
    #   tasks = json.load( tasks_r_file )
    #   tasks_r_file.close()

    #cria um dataframe para as listas
    lists_df = pd.DataFrame([[
        tasks[task]['space']['id'],
        tasks[task]['folder']['id'],
        tasks[task]['list']['id'],
        tasks[task]['list']['name'],
        tasks[task]['id']
        ] for task in tasks
    ], columns=['space_id', 'folder_id', 'list_id', 'list_name', 'task_id'])

    #junt os dois dataframes
    all_df = pd.merge(time_entries_df, lists_df, how="left", on='task_id')

    #cria uma nova coluna horas
    #.assign() para criar nova coluna
    all_df = all_df.assign(hours = lambda x: x.time_duration / (3600 * 1000))

    grouped_by_user = all_df.groupby('user_name')

    for username, user_frame in grouped_by_user:
        total_time = user_frame['time_duration'].sum()
        total_hour = total_time / (3600*1000)
        project_group = user_frame.groupby('list_name', sort=True)
        tasks_group = user_frame.groupby(['list_name', 'task_name'])

        print(f"\n\n\n>>>>>>>> {username.upper()}")
        print("========= tarefas =========")

        #imprime um por um no terminal
        for project, project_frame in project_group:
            time_spent = project_frame['hours'].sum()
            fraction = time_spent / total_hour
            print(f"### {project.ljust(20)} | {time_spent:4.1f} hrs | {fraction:6.2%}")

        #exporta para formato csv dentro da pasta data
        tasks_filename = f"{username} - tarefas {util.timestamp_to_human(start_ts)} - {util.timestamp_to_human(end_ts)}.csv"
        tasks_group['hours'].sum().rename_axis(['Project', 'Task']).reset_index().to_csv(f"./report/{tasks_filename}")

        print(f"\n O detalhamento das tarefas foi salva em: {tasks_filename}")

        """
        Preenche as datas faltantes.
        O date_range gera o período de datas entre
        o start e o end informados.
        """
        missing_dates = pd.date_range(start, util.get_end_date(end_ts), tz=TIMEZONE)
        missing_str = ['test' for _ in range(len(missing_dates))]
        missing_num = [0 for _ in range(len(missing_dates))]
        missing_empty = [0 for _ in range(len(missing_dates))]

        missing_df = pd.DataFrame({ 'task_id': missing_str, 'task_name': missing_str,
                            'time_id': missing_str, 'time_start': missing_dates, 
                            'time_end': missing_dates, 'time_duration': missing_num, 
                            'list_id': missing_str, 'list_name': missing_empty,
                            'user_id': missing_str, 'user_name': missing_str, 'hours': missing_empty})
        full_frame = user_frame.append(missing_df)

        timesheet_df = pd.pivot_table(full_frame, index=['list_name'], margins= True, margins_name='Total', columns='time_start', values=['hours'], aggfunc=[np.sum], fill_value='')

        timesheet_filename = f"{ username } - timesheet { util.timestamp_to_human( start_ts ) } - { util.timestamp_to_human( end_ts) }.csv"

        timesheet_df.to_csv(f"./report/{ timesheet_filename }")

        print( f"\n====== TIMESHEET ======" )
        print( timesheet_df )
        print( f"The timesheet is saved to: {timesheet_filename}" )

# Função para pegar os membros do time
def get_team_members():

    api_team = f"{API_ENDPOINT}team"
    headers = {
        "User-Agent": USER_AGENT,
        "Authorization": API_KEY
    }

    try:
        session = requests.session()
        r = session.get(api_team,headers=headers)
    
    except Exception as e:
        print(f'Erro ao requisitar dados ao Clickup {e}')
    
    teams = None

    #se o request der sucesso, retorna o time todo
    if(r.status_code == 200):
        teams = r.json()['teams']

        # recupera o ID do time 
        if (len(teams) > 0):
            global TEAM_ID
            TEAM_ID = teams[0]['id']
        
        return get_members( teams[0])
    else:
        print('Erro na resposta. Status:', r.status_code)

# Função para separar os membros dentro do json de Times
def get_members (team):
    members = [    {
      "id": member['user']['id'],
      "username": member['user']['username'],
      "email": member['user']['email']
    } for member in team['members']]
    return members

#Função resposável por criar a estrutura de pastas no Windows
def create_folder( path ):
    #Cria a pasta se ela não existir
    if not os.path.exists( path ):
        os.makedirs ( path )
      
#chama a função main
if __name__ == "__main__":
    main()