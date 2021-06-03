# search_Youtube_videos_v2
An efficient and scalable api, to fulfil user's queries returning most valid and latest data

## Search Youtube Video:

An safe, secure, efficient and scalable api where user can come register, login and query for any video. He/she can also register the query in prior, either seperatly or in bulk.
This api provides bulk register and bulk query functionality as well. This api provides a efficient and secure 
solution for queries.
provided Endpoints to refresh your **access token** using **refresh token** .
After authentication, user gets a unique key and refresh token in case if his/her access token expires.

while access token and secret key gets stored on server side itself, and to access this data user needs to 
have unique keys provided to him/her while logging in. keys are stored in **redis** and with lifetime same as expiry 
age. So blacklisting is not required any more. As after expiry token gets deleted by itself.

Every endnode is getting authorized via **custom authentication middleware**. 

To fetch data regarding registered queries, **Asynchronous tasks** are used to fetch data and store in mongodb. **Celery workers** take tasks from **mesage queue** and execute them. **Redis** is used as a message queue.

provided two extra endpoints :
1. full text search for any word in title
2. date range filtering on video published date
For this need, there is no better solution than **ElasticSearch**. So along with storing data into mongo using **pymodm**, data is also getting inserted into elastic search **synchronously**. 
**Docker-compose** is used in order to run docker containers of elastic search and  **kibana** for furthur analysis. for sake to ease, **Port mapping** is done with same ports of host.
