from django.shortcuts import render, HttpResponse
from django.http import JsonResponse, HttpResponseBadRequest,HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from . models import pastQuery,errorFeedback
from datetime import datetime
import json
import json
from user import indexing
from . import rag

indexer = indexing.SystemInfoIndexer()

@csrf_exempt
def getpastqueries(request):
    if request.method=="POST":
        user_id = request.POST.get('user_id')
        page = request.POST.get('pageno')
        skiplist = (int(page)-1)*10
        queries = list(pastQuery.find({"user_id" : user_id},{"_id":0}).skip(skip=skiplist).limit(10))
        # isMore = len(queries) == 10
        jsonresp = json.dumps(queries)
        return HttpResponse(jsonresp, content_type="application/json; charset=utf-8")
    else:
        return HttpResponse("Forbidden")




@csrf_exempt
def deletepastqueries(request):
    if request.method != "POST":
        return HttpResponseForbidden("POST required")

    # parse JSON body
    try:
        payload = json.loads(request.body.decode("utf-8"))
        user_id = payload["user_id"]
        question = payload["question"]
    except (ValueError, KeyError):
        return HttpResponseBadRequest("Invalid JSON payload")

    # perform the deletion
    result = pastQuery.delete_one({
        "user_id": user_id,
        "question": question
    })

    return JsonResponse({
        "deleted_count": result.deleted_count
    })




@csrf_exempt
def savepastqueries(request):
    if request.method == 'POST':
        
        queryRecord = {
            "user_id" : request.POST.get('user_id'),
            "question" : request.POST.get('question'),
            "answer": request.POST.get('answer'),
            "timeStamp" :datetime.now().timestamp()
        }
        pastQuery.insert_one(queryRecord)
        return HttpResponse(" User Created Successfully")
    else:
        return HttpResponse("Forbidden")




@csrf_exempt
def getAnswer(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")

    try:
        payload = json.loads(request.body.decode("utf-8"))
        question = payload["contents"][0]["parts"][0]["question"].strip()
    except (json.JSONDecodeError, KeyError, IndexError, TypeError):
        return HttpResponseBadRequest("Invalid JSON or missing question.")
        # Step 1: Semantic retrieval


    retrieved = indexer.search(question, limit=3)

    # Step 2: Build context block
    context = "\n".join([f"- {doc}" for doc in retrieved])

    # Step 3: Compose final prompt
    prompt = f"""
    You are an Ubuntu system assistant. Answer the following question

    Context:
    {context}

    Question:
    {question}
    """


    answer = rag.ask_gemini(prompt)

    response = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {"text": answer}
                    ]
                }
            }
        ]
    }

    return JsonResponse(response)



@csrf_exempt
def troubleShoot(request):
    if request.method != "POST":
        return HttpResponseBadRequest("Only POST allowed")

    # 1) Parse JSON body (not request.POST)
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON")

    # 2) Extract the field from troubleshooting
    error = payload.get("error")
    if not error:
        return HttpResponseBadRequest("Missing 'error' field")

    print("Received error:", error)

    retrieved = indexer.search(error, limit=3)

    # Step 2: Build context block
    context = "\n".join([f"- {doc}" for doc in retrieved])

    # Step 3: Compose final prompt
    prompt = f"""
    You are an Ubuntu system assistant. Answer the following question
    This error log contains a problem. I want you to give me three things strictly :\n
    Cause\n
    Solution\n
    Version in which the solution is applicable\n

    Return the result in JSON format only.\n\n
    
    Context:
    {context}

    Error:
    {error}

    """

    print(prompt)


    answer = rag.ask_gemini(prompt)
    print(answer)
    response = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {"text": answer}
                    ]
                }
            }
        ]
    }
    return JsonResponse(response)



@csrf_exempt
def add_error_report(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            error = data.get("error")
            solution = data.get("solution")
            status = data.get("status")

            if not all([error, solution, status]):
                return JsonResponse({"error": "Missing fields"}, status=400)

            # Insert into MongoDB
            document = {
                "error": error,
                "solution": solution,
                "status": status
            }
            errorFeedback.insert_one(document)

            return JsonResponse({"message": "Feedback saved successfully."})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Invalid HTTP method."}, status=405)


@csrf_exempt
def add_application_info(request):
    pass
