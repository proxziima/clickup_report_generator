from decouple import config
import os
import json
import requests
import pandas as pd 
import numpy as np
from requests import status_codes
import utilities as util


# API_ENDPOINT  = "https://api.clickup.com/api/v2/"
API_ENDPOINT = "https://private-anon-ca0332bf87-clickup20.apiary-proxy.com/api/v2/"
USER_AGENT    = config('USER_AGENT')
API_KEY       = config('API_KEY')
TEAM_ID       = config('TEAM_ID')
TIMEZONE      = config('TIMEZONE')


columns_time_entries = [  'task_id', 'task_name',
                          'time_id', 'time_start', 'time_end', 'time_duration', 
                          'user_id', 'user_name']

def get_members( team ) :
  """
  Function to parse members inside a team's JSON
  """
  members = [ { 'id': member['user']['id'], 'username': member['user']['username'] } for member in team['members'] ]
  return members


def get_team_members( ) :
  """
  Function to get all available team members
  @param team_id
  @return array of tuple [id, name]
  """

  api_team = f"{API_ENDPOINT}team"
  headers = {
    "User-Agent": USER_AGENT,
    "Authorization": API_KEY }

  try:
    session = requests.session()
    r = session.get(api_team, headers=headers)

  except Exception as e:
    print(f'Clickup request error: {e}')

  # write file for the first time
  teams = None

  if (r.status_code == 200):
    teams = r.json()['teams']
    
    if ( len(teams) > 0 ):
      global TEAM_ID 
      TEAM_ID = teams[0]['id']

    return get_members( teams[0] )
    # if ( len(teams) == 1 ) :
    # else, choose team first.


  else:
    print( 'Response gagal. Status:', r.status_code )


def create_folder( path ):
  """
  Create folder at path if not exist
  """
  if not os.path.exists( path ) :
    os.makedirs( path )


def main() :
  """
  Function main
  the actual function to invoke for the first time
  """
  # dates in format YYYY-MM-DD
  print("Clickup timesheet report generator  -  Because having to create timesheet report manually sucks. Big time.")
  print("===")
  start = input("Begin since when? (in YYYY-MM-DD): ") # since early dec
  end = input("Until when? (defaults to today): ") # string or None
  members = get_team_members( )
  
  print("===\nGenerate whose report?")
  for i, member in enumerate(members, start=1):
    print( f"{i}: {member['username']}" )
  
  chosen_member = input("Choose one (or just hit enter to choose everyone): ")
  # assignee accepts empty string, but defaults to API_KEY holder
  # it accepts list of ids too, which is the intended 
  assignee = members[(int(chosen_member) - 1)]['id'] if chosen_member else ",".join([ str(member['id']) for member in members])

  start_ts = util.str_to_timestamp( start )
  end_ts = util.get_eod_timestamp( end )

  api_time_entries = f"{API_ENDPOINT}team/{TEAM_ID}/time_entries?start_date={start_ts-1}&end_date={end_ts}&assignee={assignee}"
  api_task = f"{API_ENDPOINT}task/"


  headers = {"Authorization": API_KEY }

  try:
    # read time_entries from API
    session = requests.session()
    r = session.get(api_time_entries, headers=headers)

  except:
    print('error konek coi')

  # write file for the first time
  time_entries = None

  if (r.status_code == 200):
    
    create_folder('data')
    create_folder('report')

    f = open('./data/time_entries.json', 'w')
    time_entries = r.json()
    f.write( r.text )
    f.close()
    print( f"===\nThere are { len(time_entries['data']) } time logs found for the given time range." )


  else:
    print( 'Response gagal. Status:', r.status_code )


  # # read time entries from file
  # f = open('./data/time_entries.json', 'r')
  # time_entries = json.load(f)
  # f.close()
  # # print(time_entries)

  tasks = {}

  # info about time_entries
  time_entries_rows = []


  for time_entry in time_entries['data'] :
    # populate the tasks object
    tasks[time_entry['task']['id']] = time_entry['task']['name']

    # append new row
    time_entries_rows.append([  time_entry['task']['id'], 
                                time_entry['task']['name'],
                                time_entry['id'],         
                                pd.to_datetime(time_entry['start'], unit='ms', utc=True).tz_convert( TIMEZONE ), 
                                pd.to_datetime(time_entry['end'], unit='ms', utc=True).tz_convert( TIMEZONE ), 
                                int(time_entry['duration']),
                                time_entry['user']['id'], 
                                time_entry['user']['username'] ] )

  # create new dataframe
  time_entries_df = pd.DataFrame(time_entries_rows, columns=columns_time_entries)

  print( f"Found in { len(tasks) } tasks." )


  # =====
  # iterate over the task ids
  i = 0
  for task_id in tasks.keys() :

    print(f"> {str(i+1).rjust(3)}/{len(tasks)} | Fetching info about task {task_id}: {tasks[task_id]}")

    t = requests.get(f"{api_task}{task_id}", verify=False, headers=headers)
    tasks[task_id] = t.json()

    i+=1

  # ====
  # woohoo got the list's details here. We can work on something, finally.
  with open('./data/tasks.json', 'w') as tasks_file :
    # write the file
    json.dump(tasks, tasks_file)
    tasks_file.close()


  # # read tasks from file instead of API
  # with open('./data/tasks.json', 'r') as tasks_r_file :
  #   tasks = json.load( tasks_r_file )
  #   tasks_r_file.close()


  # create lists dataframe
  lists_df = pd.DataFrame([ [ tasks[task]['list']['id'],
                              tasks[task]['list']['name'], 
                              tasks[task]['id'] 
                              ] for task in tasks ], 
                            columns=['list_id', 'list_name', 'task_id'])
  
  # join everything
  all_df = pd.merge( time_entries_df, lists_df, how="left", on='task_id' )

  # .assign() to create new column
  all_df = all_df.assign(hours= lambda x: x.time_duration / (3600 * 1000))

  grouped_by_user = all_df.groupby('user_name')

  for username, user_frame in grouped_by_user :


    # --> INSERT SCRIPT to DIVIDE BETWEEN USERS HERE <--
    total_time = user_frame['time_duration'].sum()
    total_hour = total_time / (3600*1000)
    ten_percent = total_time * 0.1
    project_group = user_frame.groupby('list_name', sort=True)
    tasks_group = user_frame.groupby(['list_name', 'task_name'])


    print( f"\n\n\n>>>>>>> { username.upper() } " )
    print( "====== TASKS ======" )

    # print one by one huvt
    for project, project_frame in project_group:
      time_spent = project_frame['hours'].sum()
      fraction = time_spent / total_hour
      print( f"### {project.ljust(20)} | {time_spent:4.1f} hrs | {fraction:6.2%}" )
      # print(frame.iloc[:,[1, -1] ], end="\n\n\n")


    # export to CSV
    # todo: export per person.
    tasks_filename = f"{username} - tasks { util.timestamp_to_human( start_ts ) } - { util.timestamp_to_human( end_ts) }.csv"
    tasks_group['hours'].sum().rename_axis(['Project', 'Task']).reset_index().to_csv(f"./report/{ tasks_filename }")
    print( f"\nThe detailed tasks have been saved to: { tasks_filename }" )



    # fill user_frame with missing dates
    missing_dates = pd.date_range( start, util.get_end_date( end_ts), tz=TIMEZONE )

    missing_str = [ 'test' for _ in range(len(missing_dates)) ]
    missing_num = [ 0 for _ in range(len(missing_dates)) ]
    missing_empty = [ 0 for _ in range(len(missing_dates)) ]

    missing_df = pd.DataFrame({ 'task_id': missing_str, 'task_name': missing_str,
                            'time_id': missing_str, 'time_start': missing_dates, 
                            'time_end': missing_dates, 'time_duration': missing_num, 
                            'list_id': missing_str, 'list_name': missing_empty,
                            'user_id': missing_str, 'user_name': missing_str, 'hours': missing_empty})
    

    full_frame = user_frame.append( missing_df )

    # kinda work but missing some dates
    # print( full_frame.tail(20) )
    timesheet_df = pd.pivot_table(full_frame, index=['list_name'], margins=True, margins_name='Total', columns='time_start', values=['hours'], aggfunc=[np.sum], fill_value='')

    timesheet_filename = f"{ username } - timesheet { util.timestamp_to_human( start_ts ) } - { util.timestamp_to_human( end_ts) }.csv"
    # timesheet_df.loc['Total'] = timesheet_df.sum(numeric_only=True, axis=0)

    timesheet_df.to_csv(f"./report/{ timesheet_filename }")
    
    print( f"\n====== TIMESHEET ======" )
    print( timesheet_df )
    print( f"The timesheet is saved to: {timesheet_filename}" )



# call the function woohoo
if __name__ == "__main__":
  main()
