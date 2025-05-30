from django.http import HttpResponseBadRequest
from django.shortcuts import HttpResponse
from .models import User, SystemInfo
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
import pyotp
from django.core.cache import cache
from django.core.mail import send_mail
import json
from .indexing import SystemInfoIndexer
import uuid


indexer = SystemInfoIndexer()


# Create your views here.
# while creating a user if a userId already exists return the user ID along with email to save in database
@csrf_exempt
def createUser(request):
    if request.method == 'POST':
        user = {
            "user_id" : request.POST.get('user_id'), 
            "email" : request.POST.get('email'),
            "timestamp" :  datetime.utcnow().timestamp(),
            "timezone" : request.POST.get('timezone'), 
            "profile_url" : request.POST.get("profile_url")
        }
        User.insert_one(user)
        return HttpResponse(" User Created Successfully")
    else:
        return HttpResponse({"error": "Forbidden"})
    
def getUser(request):
    if request.method == "POST":
        user_id = request['user_id']
        user = User.find_one(user_id=user_id)
        return HttpResponse(user)
    else:
        return HttpResponse("Forbidden")


def updateavatar(request):
    return HttpResponse("Update avatar")

def blank(request):
    return HttpResponse("this is the blank page")

@csrf_exempt
def sendOTP(request):
    email = request.POST.get('email')  # Get email from request
    print(email)
    if not email:
        return HttpResponse({'error': 'Email is required'})

    secret = pyotp.random_base32()  # Generate a secret key
    otp = pyotp.TOTP(secret).now()  # Generate a time-based OTP

    cache.set(email, {'otp': otp, 'secret': secret}, timeout=300)  # Store OTP & secret for 5 min

    subject = 'Welcome Geeks !!'
    message = f'Your OTP for Ubntai user Registration is : {otp}'
    from_email = 'srigoanuj786@gmail.com' 
    recipient_list = [email]
    
    try:
        send_mail(subject, message, from_email, recipient_list)
        return HttpResponse({'message': 'OTP sent successfully'})
    except Exception as e:
        print(e)
        return HttpResponse({'error': str(e)})


@csrf_exempt
def verifyOTP(request):
    if request.method == "POST":
        email = request.POST.get('email') 
        otp = request.POST.get('otp')  
        
        print(email, otp)
        if not email or not otp:
            return HttpResponse({'error': 'Email and OTP are required'})
        
        cached_data = cache.get(email)  # Retrieve stored OTP & secret
        if not cached_data:
            return HttpResponse({'error': 'OTP expired or invalid'})
        
        secret = cached_data['secret']
        totp = pyotp.TOTP(secret)
        
        if totp.verify(otp):
            cache.delete(email)  # Remove OTP after successful verification
            return HttpResponse({'message': 'OTP verified successfully'})
        else:
            return HttpResponse({'error': 'Invalid OTP'})
    else: 
        return HttpResponse({"error": "Forbidden"})


@csrf_exempt
def createSystemInfo(request):
    if request.method != "POST":
        return HttpResponseBadRequest("Forbidden")

    unique_id = uuid.uuid4().hex

    info = {
        "_id": unique_id,
        "sys_name":     request.POST.get("sys_name"),
        "kernel_type":  request.POST.get("kernel_type"),
        "kernel_version": request.POST.get("kernel_version"),
        "arch_type":    request.POST.get("arch_type"),
        "hostname":     request.POST.get("hostname"),
        "timezone":     request.POST.get("timezone"),
        "user_id":      request.POST.get("user_id"),
    }

    # store in Mongo
    SystemInfo.insert_one(info)

    # also index in Quadrant/Qdrant
    indexer.insert(info)

    return HttpResponse("Inserted System information")
    

@csrf_exempt
def isUser(request):
    if request.method == "POST":
        email = request.POST.get('email')
        user = list(User.find({"email": email}))
        if user:
            user_data = user[0]  # Get first matched user
            
            # Convert ObjectId to string
            user_data["_id"] = str(user_data["_id"]) if "_id" in user_data else None
            
            response_data = json.dumps(user_data)  # Convert dictionary to JSON string
            return HttpResponse(response_data, content_type="application/json; charset=utf-8")
        else :
            return HttpResponse(False)
    else : 
        return HttpResponse({"error": "Forbidden"})