# Work Generator Documentation

## Summary
The work generator interacts with Regulations.gov directly. It uses a personal API key to check to see if anything new has been posted on the website. If there is something new-- meaning if the gathered link(s) are not in Redis-- the work genrator will generate jobs for the client to complete. It takes up to 250 jobs at a time.
