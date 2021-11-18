# Clickup Timesheet Generator
This little script is made during my tenure at a consultation company. They required us to create a timesheet (basically a log-based time report) every month. Since our design team _independently_ uses ClickUp, we log the time there BUT having no budget from the office to pay for ClickUp sucks too. So I created this little script to generate the report automatically-ish, and most importantly, for free. Well it gets the job done, so yeah, I'm a tad bit happy.

## Installation & running

1. Clone the repository: `git clone https://github.com/anwari666/clickup-timesheet-generator.git`
2. Install the requirements: `pip install -r requirements.txt`
3. Rename the `example.env` to `.env`
4. Grab your Clickup API key by going to Settings > Apps and then click Generate. Put it inside the `.env`
5. Run the script: `python generate-report.py`

Tested on Mac. Not 100% sure if it's working on Windows...
