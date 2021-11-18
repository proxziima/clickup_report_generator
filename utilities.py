# Utility functions to help generate ClickUp's report
import datetime
import time

def get_end_date( ts_ms ):
  """
  Utility function to convert a timestamp in miliseconds to string 
  Returns string of a date: YYYY-MM-DD
  """
  return datetime.datetime.fromtimestamp( ts_ms/1000 ).strftime('%Y-%m-%d')


def get_eod_timestamp( s ) :
  """
  Utility function to convert a date string in YYYY-MM-DD into end-of-day timestamp.
  End date can be omitted. In this case, it will be set to today's EOD.
  Returns timestamp in miliseconds
  """
  if s == '' :
    # check for the end of day
    return int( datetime.datetime.now()
                .replace(hour=23, minute=59, second=59, microsecond=0)
                .timestamp() 
                * 1000 ) 
  else :
    return int( datetime.datetime.strptime( s, '%Y-%m-%d' )
                .replace(hour=23, minute=59, second=59, microsecond=0)
                .timestamp() 
                * 1000 )


def str_to_timestamp( s ):
  """
  Utility function to convert date string (YYYY-MM-DD) to timestamp (miliseconds)
  """
  time_tuple = datetime.datetime.strptime( s, '%Y-%m-%d').timetuple()
  return int( time.mktime( time_tuple ) ) * 1000


def timestamp_to_human( ts_ms ):
  """
  Utility function to convert timestamp in miliseconds to human readable format
  """
  return datetime.datetime.fromtimestamp( ts_ms /1000 ).strftime('%b %d')