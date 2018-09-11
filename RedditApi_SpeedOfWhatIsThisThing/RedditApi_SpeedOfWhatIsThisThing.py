import time
import operator
from collections import OrderedDict

#Import Reddit API
import praw
from praw.models import MoreComments

#Import PostgreSQL API
import psycopg2
import psycopg2.extras

#Import Plotly API
import plotly
import plotly.graph_objs as go

#Function to print to the console output and also to write into a file for easier analyzation with large output
def PrintAndFileOut(p_string, p_variable=""):
        print(p_string + str(p_variable))
        logFile.write(p_string + str(p_variable) + "\n")


try:
    conn = psycopg2.connect("dbname='redditDatabase' user='postgres' host='localhost' password=''")
    cur = conn.cursor()

    cur.execute("""DROP TABLE IF EXISTS reddittable""")
    cur.execute("""CREATE TABLE IF NOT EXISTS reddittable ( 
                                                                smid TEXT NOT NULL,
                                                                smtitle TEXT,
                                                                smflair TEXT,
                                                                issolvedflair BOOLEAN,
                                                                solutioncomment TEXT,
                                                                approvalcomment TEXT,
                                                                issolutionmarkedbyauthor BOOLEAN,
                                                                solutiontimemin NUMERIC(10,5)
                                                                );""")
    cur.close()
    conn.commit()
except:
    print("I am unable to execute operation in the database")




logFile = open("workfile.txt","w") 



#FILL THIS OUT BEFORE START:
reddit = praw.Reddit(client_id='',
                     client_secret='',
                     user_agent='')



reddit.read_only  
subreddit = reddit.subreddit('whatisthisthing')




allSolvedSubmission = 0
allLikelySolved = 0
allNotSolvedSubmission = 0
invalidSolutionNumber = 0
analizedSubmissions = 2000
isSubmissionSolverAprovedbyAuthor = False
howManySubmissionsAreNotSolvedByAuthor = 0
howManySubmissionsAreSolvedByAuthor = 0
deletedSubmissionAuthor = 0
submissionAuthor = None
sumSolutionTime = 0
iteratorCounter = 0
runTime = time.time()

#Manually checked and invalidated submissions: 
invalidSolutions = ["8sscgi","8t1j07","7oy9yi"]

dataList = []  #SubmissionID, SubmissionTitle, SubmissionFlair, isSolvedFlair,
               #SolutionComment, ApprovalComment, isSolutionMarkedByAuthor, SolutiontimeMin

#For Database inserts:
submissionID = None
submissionTitle = None
submissionFlair = None
isSolvedFlair = False
SolutionComment = None
ApprovalComment = None
isSolutionMarkedByAuthor = False
SolutiontimeMin = None

#For data visualization with Plotly:
plotly_SolvedDictionary = {}



#list for not recognised flairs for deeper understanding:
listWithNotRecognizedFlairs = []

for submission in subreddit.top(limit=analizedSubmissions):
    iteratorCounter += 1
    PrintAndFileOut("#############Iteration: ", iteratorCounter)

    submissionID = submission.id
    submissionTitle = submission.title
    submissionFlair = submission.link_flair_text
    isSolvedFlair = False
    SolutionComment = None
    ApprovalComment = None
    isSolutionMarkedByAuthor = False
    SolutiontimeMin = None
    
    if submission.link_flair_text is not None and submission.link_flair_text.lower().startswith("solved") and submissionID not in invalidSolutions:

        isSolvedFlair = True
        allSolvedSubmission += 1

        if submission.author is not None:
            submissionAuthor = submission.author.name
            

            submission.comments.replace_more(limit=None)

            for top_level_comment in submission.comments:


                for second_level_comment in top_level_comment.replies:


                    if submissionAuthor == second_level_comment.author and "solved" in second_level_comment.body.lower(): 
                        howManySubmissionsAreSolvedByAuthor += 1

                        SolutionComment = top_level_comment.body
                        SolutiontimeMin = ((top_level_comment.created_utc - submission.created_utc) / 60)
                        ApprovalComment = second_level_comment.body
                        PrintAndFileOut("SOLUTION TIME (min): " ,SolutiontimeMin)

                        sumSolutionTime += SolutiontimeMin

                        plotly_SolvedDictionary[submissionTitle] = SolutiontimeMin

                        isSubmissionSolverAprovedbyAuthor = True
                        isSolutionMarkedByAuthor = True
                        break

                if isSubmissionSolverAprovedbyAuthor:
                    #Stop iterate over the top level comments if it is already
                    #marked as solved by author
                    break

            if not isSubmissionSolverAprovedbyAuthor:
                howManySubmissionsAreNotSolvedByAuthor += 1
            else:
                isSubmissionSolverAprovedbyAuthor = False
                
        else: 
            deletedSubmissionAuthor += 1 


    elif submission.link_flair_text is not None and "Likely" in submission.link_flair_text:
         allLikelySolved += 1

    elif submissionID in invalidSolutions:
          invalidSolutionNumber += 1

    else:
         allNotSolvedSubmission += 1
         listWithNotRecognizedFlairs.append(submission.link_flair_text)



    dataList.append((submissionID,submissionTitle,submissionFlair,isSolvedFlair,SolutionComment,ApprovalComment, isSolutionMarkedByAuthor,SolutiontimeMin))
    PrintAndFileOut(" ")


#Insert into PostgreSQL Database
try: 
    conn = psycopg2.connect("dbname='redditDatabase' user='postgres' host='localhost' password='12345678'")
    cur = conn.cursor()
    
    insert_query = 'INSERT INTO redditTable (smid, smtitle, smflair, issolvedflair, solutioncomment, approvalcomment, issolutionmarkedbyauthor, solutiontimemin) values %s'
    psycopg2.extras.execute_values(cur, insert_query, dataList, template=None, page_size=100)
    
    cur.close()
    conn.commit()
    
except psycopg2.Error as e:
    print(e.pgerror)


#Prerequisite for visualization
orderedDict = OrderedDict(sorted(plotly_SolvedDictionary.items(), key=lambda x: x[1]))


generatedList = []
nameAvgForTrace = "Average Time: "
if(howManySubmissionsAreSolvedByAuthor is not 0):
    averageSolutionTime = sumSolutionTime / howManySubmissionsAreSolvedByAuthor
    for x in range(0, len(orderedDict.keys())):
        generatedList.append(averageSolutionTime)

    nameAvgForTrace = "Average Time: " + str(round(averageSolutionTime,1))

    

#Visualization with Plotly
plotly.offline.plot({
    "data": [go.Bar(x = list(orderedDict.keys()),
               y = list(orderedDict.values()),
               name='Solution Time'),
             
             go.Scatter(x=list(orderedDict.keys()),
                 y=generatedList,
                 name=nameAvgForTrace)],

    "layout": go.Layout(title = "How quick is r/WhatIsThisThing",
                        xaxis = dict(title = 'Submissions',
                                        titlefont=dict(family='Courier New, monospace',
                                        size=18,
                                        color='#7f7f7f')),
                        yaxis = dict(title = 'Time (min)',
                                        titlefont=dict(family='Courier New, monospace',
                                        size=18,
                                        color='#7f7f7f')))
}, auto_open=True)




PrintAndFileOut("-------------------------------------------")
PrintAndFileOut("METRICS:")
PrintAndFileOut("Analyzed Submissions: ", analizedSubmissions)
PrintAndFileOut("Solved Submissions: ", allSolvedSubmission)
PrintAndFileOut("Likely Solved Submissions: ", allLikelySolved)
PrintAndFileOut("Likely Solved Submissions: ", invalidSolutionNumber)
PrintAndFileOut("Not Recognized Submissions: ", allNotSolvedSubmission)
PrintAndFileOut("Not recognized flairs: ", listWithNotRecognizedFlairs)
PrintAndFileOut("Submissions are not marked as solved by author: ", howManySubmissionsAreNotSolvedByAuthor)
PrintAndFileOut("Submissions are solved by author: ", howManySubmissionsAreSolvedByAuthor)
PrintAndFileOut("Submission Author is deleted and the submission is solved: ", deletedSubmissionAuthor)
PrintAndFileOut("Rumetime (min): ", (time.time() - runTime) / 60)
PrintAndFileOut("AverageSolutionTime (min): ", averageSolutionTime)

logFile.close()