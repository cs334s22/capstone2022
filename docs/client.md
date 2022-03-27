# Client Documentation


## Summary
The clients are their own objects that will connect to the work server, receive work, 
and send results back to the server by making the calls to [regulations.gov]
(https://www.regulations.gov/) for data downloads. 

## Description 
Multiple clients will be able to connect to the work server at once. A client 
will also try to get a `client_id` if it doesn't have one already. The goal is 
that the client will request and complete work in order to download data from 
[regulations.gov](https://www.regulations.gov/) to disk. 


### `/get_job`
Get an endpoint with the URL/'get_job', and Params of the Client_ID. Loads the response from requests.get(endpont, params)as text. If there is no 'job' in the JSON response_text, raise an exception. Job variable - a JSON of the contents from the 'job' in response_text. Job_ID which is the first key in Job . URl indexed with the Job_ID in Job . If there is a job type in Job, save it to Job_type, otherwise save Job_type to 'other'. Return the Job_ID, URL, and Job_type

### `/execute_task`
Main tries to call execute job, and will create an exception if there are no jobs available. 

Will be used to call get_job() which will return a Job's ID, URL,and Type, printing updates along the way. The function checks to is if the Job Type is an attachment. If it is, **perform_attachment_job(url)** is called. If not, **perform_job(url)** is called.  

The JSON of the job, and the Job ID are then sent to **send_job_results(job_id, results)** 

Prints(Job Complete!)

### `/perform_attachment_job` 
Returns a JSON of the Job's: text, type, id, and its attributes (agencyID, docketID, commentOnDocument )

### `/ perform_job`
Adds the specified Api_Key to the url, to be sent in  **Assure_Request(requests.get, url)** which returns a JSON data of the Job

### `/send_job_results`
An endpoint of the URL + /putresults is create. If the JSON contains an error, only a dictionary (Data) of the Job ID and Results will be sent through requests.put. Otherwise, a dictionary (Data) of Directory: which calls **Get_Output_Path(Job_results)**, Job ID, and Results is made. A parameter (Params) of the specific client id is also made. At the end, the new made endpoint, a JSON dump of Data, and Params are sent through requests.put

### `/assure_request` 
Wrapped in a ***while True*** that runs while request.get is called as request(url, ** kwargs). The response ***tries**  to check ****check_status_code(response)** which will print a message regarding the status code. **.raise_for_status()** is then called, which will raise an HTTPError if the HTTP request returned an unsuccessful status code. Three exceptions are checked.RequestConnectionError(): the function prints a message, sleeps for a minute before trying again. HTTPError(): prints a message and tries again. RequestException(): prints a message and tries again. **Returns** the response is there is one. 

### `/get_output_path`
Returns -1 if there is an error in the result. Creates an empty string: output_path. A variable Data is create from the JSON Results pointed to the key 'data' and then to its 'attributes'. Output_path is concatenated with **get_key_path_string(data,"agencyID")**, **get_key_path_string(data,"docketID")**, **get_key_path_string(data,"commentOnDocument")**. Output_path is concatenated with JSON Results pointed to the key 'data' and then to its 'id' with "/" and then again with ".json". Output_path is returned.

### `/get_key_path_string`
If the parameter Key is a key in Results, continue. If not, return a blank string.  If the Key leads to nothing in Results, return a string of 'None/'. Otherwise, return the reuslts[key] concatenated with "/"
