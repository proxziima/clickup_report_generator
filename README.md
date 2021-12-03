# Gerador de Relatórios de Timesheet / Clickup Report Generator
Esse script foi criado para automatizar o processo de geração dos relatório de Timesheet para algumas tarefas repetitivas no meu trabalho. Basicamente eu gerava esses relatórios semanalmente, o que alimentava o processo de medição com o cliente e também os indicadores fonte do nosso Dashboard BI (Power BI). Já que era um indicador "on line", eu acabava exportando manualmente esses relatórios e tratando o .csv no "dedão", o que me tomava muito tempo, e também era muito chato.
Então, com base no script montado pelo [Anwari Ilman](https://github.com/anwari666), eu pude entender a lógica e criar um script que atende a essas necessidades.
Agora os apontamentos são exportados, tratados e organizados automaticamente, o que me toma muito menos tempo.
Grande agradecimento ao [Anwari Ilman](https://github.com/anwari666), primeiro a solucionar o problema de muitos. :)

This script was created to automate the process of generating timesheet reports for some boring taks in my daily work. Basically i export this reports weekly, which fed the measurement process with the Client, also the BI Dashboard indicators. Since it was a "online" dashboard, i ended up manualluy exporting this reports and handling the .csv all by myself, witch took a lot of time and effort, also is very annoying.
So, based on script made by [Anwari Ilman](https://github.com/anwari666), i was able to understand the logic and create one script the meets all my needs.
Now the timesheets area exported, treated, organized automatically, taking much less time.
Big thanks for [Anwari Ilman](https://github.com/anwari666), the first to solve this problem.

## Installation & running

1. Clone this repository: `git clone https://github.com/queirozvinicius/clickup_report_generator.git`
2. Install the requirements: `pip install -r requirements.txt`
3. Change the keys in the `.env` file
5. Run the script: `python generate-report.py`

Tested on Linux (LTS 20.04) and Windows.

## Know issues

1. I have some problems running directly on my work network. Apparently the network proxy is causing some permission blocks, returning me a 443 error.
