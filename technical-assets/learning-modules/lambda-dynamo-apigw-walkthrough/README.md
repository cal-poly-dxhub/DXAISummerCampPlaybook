This is a walkthrough of creating a Lambda function that writes to a DynamoDB table, then invoking that lambda function from a newly created REST API in API Gateway.

![alt text](https://github.com/cal-poly-dxhub/lambda-dynamo-apigw-walkthrough/blob/main/archDiagramDeploymentTrack.png)

Here is a website to test the API: https://reqbin.com/

Here is some sample data to POST to the API:

```
{
  "id": "1232134",
  "name": "Alice",
  "age": 30
}
```
