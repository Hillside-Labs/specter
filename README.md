## Steps to run
1. `pip install -r requirements.txt`
2. `cp devenv.yaml.tmpl devenv.yaml` and add your OpenAI API key
3. `python main.py`

## Assumptions and Methodology used:
* Parse the given spec into different endpoints
* Minify the endpoints by applying certain rules of abbreviation, trimming few unnecessary keys, etc.
* Group the endpoints by HTTP method
* We have assumed that POST methods are the most important and relevant to the given [FAQs](constants.py)

## Examples:
### Example 1:
URL: `https://api.apis.guru/v2/specs/twitter.com/current/2.61/openapi.yaml`

Audience: `A startup of 8 people with an MVP`

Use-cases: `Data analysis`
```
Query: What is the most important API endpoint?
Final Answer: The most important API endpoints for your startup, given your interest in data analysis, are likely the "createTweet" and "search/stream/rules" endpoints. The "createTweet" endpoint allows you to create tweets under an authorized account, which could be useful for generating data for analysis. The "search/stream/rules" endpoint allows for the retrieval and modification of tweets, which could be crucial for analyzing existing data. However, the importance of API endpoints can vary greatly depending on your specific use case, so it's important to thoroughly understand the functionality of all available endpoints.

Query: What is a potential chokepoint for our customers?
Final Answer: Potential chokepoints for your customers could be error handling, the complexity of the API's structure, and rate limits. Proper error handling is crucial to prevent your application from crashing or behaving unexpectedly. The complexity of the API's structure requires careful handling of parameters and responses. Lastly, be aware of potential rate limits to prevent your application from failing due to too many requests in a short period of time.

Query: Which APIs have to be monitored for cost optimization?
Final Answer: The "2/tweets/search/stream/rules" endpoint of Twitter's API should be monitored for cost optimization. This endpoint is used for adding or deleting rules from a user's active rule set. If rules are being added or deleted frequently, this could result in higher costs. Therefore, monitoring the usage of this endpoint could help in optimizing costs.

Query: What are the sources of potential customer retention risk?
Final Answer: The potential sources of customer retention risk in this API are:

1. Requirement for User Authentication: The operations "usersIdRetweets" and "usersIdFollow" require the user to be authenticated and the id of the user must match the authenticated user. This could potentially be a source of confusion or difficulty for users, leading to dissatisfaction.

2. Variety of Error Responses: Both operations return a variety of error responses, including client disconnected, client forbidden, conflict, disallowed resource, duplicate rules, invalid request, invalid rules, noncompliant rules, not authorized for field, not authorized for resource, OAuth1 permissions, operational disconnect, resource not found, resource unavailable, rule cap, streaming connection, unsupported authentication, and usage capped. These errors could potentially frustrate users if they are not handled properly. 

To mitigate these risks, it is recommended to provide clear and comprehensive documentation on how to authenticate users and handle errors. Additionally, providing responsive customer support can help to resolve any issues that users may encounter.
```

### Example 2:
Enter your OpenAPI specification yaml url:
`https://api.apis.guru/v2/specs/digitalocean.com/2.0/openapi.yaml`

The audience is:` Big 4 consulting firm`

Use-cases are: `upscale operations by migrating from bare-metal`
```
Query: What is the most important API endpoint?
Final Answer: The most important API endpoint is "v2/cdn/endpoints" as it allows users to leverage DigitalOcean's CDN for content delivery and caching purposes, which can have a significant impact on the performance and scalability of their applications.

Query: What is a potential chokepoint for our customers?
Final Answer: Based on the API specification, potential chokepoints for customers may include limitations in resource allocation and performance based on the selected droplet size and region, as well as limitations in the number of alerts and frequency of monitoring data retrieval. However, without further information or performance benchmarks, it is difficult to determine the exact extent of these potential chokepoints.

Query: Which APIs have to be monitored for cost optimization?
Final Answer: The APIs that need to be monitored for cost optimization are:

- v1/insights/lbaas
- v1/dbaas/alerts
- v2/apps/metrics/bandwidth_daily

Query: What are the sources of potential customer retention risk?
Final Answer: The potential sources of customer retention risk in relation to the provided API specification include poor performance, lack of reliability measures, and inadequate documentation. It is important for the company to address these aspects to ensure a positive user experience and minimize the risk of customer churn.
```

### Example 3:
Type yaml or json: `json`

Enter your OpenAPI specification url:
`https://api.apis.guru/v2/specs/twitter.com/current/2.61/openapi.json`

Enter information related to the business:

The audience is: `college students`

Use-cases are: `building side projects`
```
Query: What is the most important API endpoint?
Final Answer: The most important API endpoint would depend on the specific project that the college student is working on. If they are building a project that involves creating tweets, such as a Twitter bot, then the "createTweet" endpoint would be most important. If they are working on a project that involves analyzing or filtering Twitter data, then the "search/stream/rules" endpoint would be most important.

Query: What is a potential chokepoint for our customers?
Final Answer: Potential chokepoints for customers could include handling and recovering from various error responses, such as invalid or unauthorized requests, and usage limit exceeded errors. However, without specific information about rate limits or other restrictions in the API, it's difficult to identify definitive chokepoints. It's recommended to review the API documentation for details on these aspects.

Query: Which APIs have to be monitored for cost optimization?
Final Answer: Based on the provided API specification, the "addOrDeleteRules" endpoint under the "Tweets" tag could potentially have cost implications due to high usage. However, the specification does not provide any direct information about cost or pricing. Therefore, it's recommended to monitor the usage of this endpoint for cost optimization. Please refer to Twitter's API pricing information for more details.

Query: What are the sources of potential customer retention risk?
Final Answer: Potential sources of customer retention risk for these API endpoints include:

1. Complexity of User Authentication: If the process for authenticating users is complex or cumbersome, users may be discouraged from using the API.

2. Operational Errors: The API documentation lists a variety of potential error responses for both operations. If users frequently encounter these errors, they may be discouraged from using the API.

3. Lack of Necessary Features: If the API does not provide all the features or functionality that users need for their projects, they may look for alternative APIs that better meet their needs.

To mitigate these risks, it would be important to ensure a smooth and easy-to-use authentication process, robust error handling and clear, comprehensive documentation, and continuous improvement and expansion of API features based on user feedback and needs.
```