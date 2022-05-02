# Dashboard Documentation

### Format & Server Overview

The main source of communication will come from a Flask server that contains two endpoints: `data` and `/`. The server will serve JSON.

The `data` endpoint will return JSON with the necessary information related to the jobs - more detailed description found below on what information the JSON would contain.

The `/` endpoint will return an HTML/CSS display of the information on the jobs.

The dashboard itself will show the number of jobs in the queue, the number of jobs in the queue of each type, the number of jobs in progress, and the number of completed jobs. It will also display the percentage of each category as well. Finally, the dashboard also displays each container currently running on the system, along with information describing its current status. This front-end will be made of HTML, CSS, and Javascript.

Currently, the server runs through port `5000`. Down the line, we hope to run through HTTPS. 
