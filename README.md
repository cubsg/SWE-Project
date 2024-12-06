# SWE-Project

Welcome to TaskBoard!

Default MongoDB address (MongoDB must be running locally on your machine): "mongodb://127.0.0.1:27017/TaskBoardDB"

Default port for backend server.py: 5000

To Run:

1. Ensure MongoDB is installed and running on your local machine.  In our program, the host is currently set to "mongodb://127.0.0.1:27017/TaskBoardDB".

2. Open command prompt or terminal and cd into 'SWE-Project' directory

3. If flask is not installed on your system yet, run 'pip install flask'

4. Run the command 'python server.py'

5. The server should output success messages indicating that it is running on localhost (127.0.0.1) port 5000.

6. Open a browser and navigate to http://127.0.0.1:5000 (or whatever address the backend gave you upon starting).

7. Enjoy the calendar!  Log in or create an account to get started.


NOTES:

- No way to add or remove new organizations by users currently.
- No way to delete users (from user perspective).