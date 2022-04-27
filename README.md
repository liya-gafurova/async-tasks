### Advanced Python Programming book 
https://github.com/PacktPublishing/AdvancedPythonProgramming/tree/master/

This phenomenon raises an interesting issue: if a heavy, long-running task is blocking, then
it is literally impossible to implement asynchronous programming with that task as a
coroutine. So, if we really wanted to achieve what a blocking function returns in an
asynchronous application, we would need to implement another version of that blocking
function, which could be made into a coroutine and allow for task switching events to take
place at at least one point inside the function.

