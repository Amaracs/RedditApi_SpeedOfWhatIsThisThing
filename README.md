To create this project I used the reddit python api called PRAW, for data visualization I used plotly, also for debugging I inserted the collected data into a PostgreSQL database by using psycopg2 API.
Basically the script just iterates over submissions from all time top and looking for OPs approval comment in the second level comments then it takes its top level comment and subtracts the submission creation time which can be seen on the graph.
To get reliable results I only worked with the submissions that has a solved flair, and where OP wrote solved for a top level comment. 

Unfortunatelly with PRAW I could only iterate over 1000 submissions. Out of it 751 posts have solved flair, 68 posts have likely solved and the rest have not specific flair. 
Out of the 751 solved solutions 360 was marked "Solved" by OP which can be seen in the graph.

The average solution time is 74.96578703703705 min.

Data: https://docs.google.com/spreadsheets/d/1aiPB6YY_cB27Qlvx59lIy5gNUuMTxaAJGKDlgzGxYQ4/edit#gid=38137914
Interactive Graph: https://plot.ly/~amaracs/1#plot
