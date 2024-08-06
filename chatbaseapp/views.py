from django.http import (HttpResponse, JsonResponse)
from django.shortcuts import render
from django.contrib.auth import logout, login, authenticate
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import (Document, User, Billing, Product, Chat, Verification)
import os
from datetime import datetime
from django.conf import settings
from dotenv import load_dotenv
import json
import datetime
import shutil
import json
import stripe
import jwt

from .utils import *

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
ENDPOINT_SECRET_KEY = os.getenv("ENDPOINT_SECRIT_KEY")
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GMAIL_ADDRESS = os.getenv('GMAIL_ADDRESS')
GMAIL_APP_PASSWORD = os.getenv('GMAIL_APP_PASSWORD')


# Log in.
def login_view(request):
    error_message = ""
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(username=email, password=password)
        print(user)
        if user:
            login(request, user)
            # replace home with your app's home page url
            url = request.POST.get('redirect')
            return redirect(url if url else '/', {'username': email})
        else:
            error_message = "Invalid email or password"
            return render(request, 'auth-login-cover.html', {'error':error_message})
    next_url = request.GET.get('next')
    redirect_url = next_url if next_url else '/'
    return render(request, 'auth-login-cover.html', {'redirect':redirect_url, 'google_client_id': GOOGLE_CLIENT_ID})


# Register.
def register_view(request):
    error_message = ""
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        # Check if username already exists
        if User.objects.filter(email=email).exists():
            return render(request, 'auth-register-cover.html', {"error": "Email already exists"})
        # send confirm mail
        token = generate_jwt_token(email, password)
        send_verify_mail(email, token)
        verification = Verification(email = email, password= password)
        verification.save()

        message = f"Account activation link sent to your email address: {email} <br>Please follow the link inside to continue."
        
        return render(request, 'verify.html', {'message': message, 'verification_id':verification.id})
    return render(request, 'auth-register-cover.html', {'api': OPENAI_API_KEY})


# verify email
def verify_email(request, token):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        email = payload['email']
        password = payload['password']
        user = None
        if not User.objects.filter(email=email).exists():
            user = User.objects.create_user(username=email, email=email, password=password)
            # Additional steps if needed
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            user.first_name = first_name if first_name else ''
            user.last_name = last_name if last_name else ''
            # Save the user object
            user.save()
            send_welcome_email(email)
        else:
            user = User.objects.get(email=email)
        login(request, user)
        return redirect('/pricing')
    except jwt.ExpiredSignatureError:
        message = 'Your verification link is expiered. Please sign up again'
        return render(request, 'verify.html', {'message': message})
    except jwt.InvalidTokenError:
        # Handle invalid token
        message = 'Your verification link is invalid. Please sign up again'
        return render(request, 'verify.html', {'message': message})
    

# Google Login.
def google_login(request):
    if request.method == 'POST':
        body = json.loads(request.body.decode())
        email = body.get('email')
        # Check if username already exists
        user = None
        to = '/documents'
        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)
        else:
            # Create a new user instance
            user = User.objects.create_user(username=email, email=email, password=email)
            # Additional steps if needed
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            user.first_name = first_name if first_name else ''
            user.last_name = last_name if last_name else ''

            # Save the user object
            user.save()
            to = 'pricing'
            send_welcome_email(email)
        login(request, user)
        return JsonResponse({'success': 'Google login successeed', 'to':to}, status=200)
    return JsonResponse({'error': 'Invalid request.'}, status=400)


# Log out
def log_out(request):
    logout(request)
    return redirect('/')


# index page
def index(request):
    print('promotion', get_promotion_code())
    return render(request, 'index.html')


# documents page
@login_required
def documents(request):
    all_documents = Document.objects.filter(user=request.user.id, deleted=False)
    search_string = ''
    page =  1
    previous = False
    next = False
    if request.GET.get('page'):
        page = int(request.GET.get('page'))
    if page < 1:
        page = 1
    if request.GET.get('search'):
        search_string = request.GET.get('search')
    all_documents = all_documents.filter(name__icontains=search_string)
    if (page - 1) * 10 + 1 > len(all_documents):
        page = 1
    if len(all_documents) == 0:
        documents = []
        pagiantion_string = ''
    elif page * 10 > len(all_documents):
        documents = all_documents[((page - 1)*10):]
        pagiantion_string = f'{((page - 1)*10 + 1)}-{len(all_documents)} of {len(all_documents)}'
        previous = True
    else:
        documents = all_documents[((page - 1)*10):(page)*10]
        pagiantion_string = f'{((page - 1)*10 + 1)}-{((page)*10)} of {len(all_documents)}'
        previous = True
        next = True
    if page * 10 == len(all_documents): next = False
    if page == 1: previous = False
    url = '/documents?page={}'
    if search_string != '': url += '&search=' + search_string
    previous_url = url.format(page - 1) if previous else ''
    next_url = url.format(page + 1) if next else ''
    current_level = current_best_plan(request.user.id)
    contents = {'documents': documents, "pagination_string":pagiantion_string, 'previous': previous_url, 'next':next_url, 'search':search_string, 'file_size_limit':file_size_limits[current_level]}
    if len(documents) > 0:
        contents['info'] = 'To start your adventure, please select a document.'
    return render(request, 'documents.html', contents)


# handle file uploading
@login_required
def upload(request):
    user_id = request.user.id
    if request.method == 'POST' and request.POST.get('length'):
        files_count = request.POST.get('length')
        current_level = current_best_plan(user_id)
        if upload_limits[current_level] < int(files_count) + get_uploads_monthly(user_id):
            return JsonResponse({'error': 'Uploads a month limited. Please upgrade!'}, status=400)
        l = int(request.POST.get('length'))
        for i in range(l):
            myfile = request.FILES['file' + str(i)]
            if myfile.size > file_size_limits[current_level]:
                return JsonResponse({'error': f'Uploaded file size limited({file_size_limits[current_level] / 1024 / 1024}MB). Please upgrade!'}, status=400)
        directory = os.path.join(settings.MEDIA_ROOT, str(request.user.id))
        if not os.path.exists(directory):
            os.makedirs(directory)

        
        
        # Process the uploaded file here
        # You can save it, read its content, etc.
        # For example, to save the file:
        need_ocrs = request.POST.get('need_ocrs')
        for i in range(l):
            myfile = request.FILES['file' + str(i)]
            document = Document()
            document.user =  User.objects.get(id=request.user.id)
            document.file = myfile
            document.name = myfile.name
            document.size = myfile.size
            document.need_ocr = need_ocrs[i]
            document.save()
            read(request.user.id, document.id)
        redirect('/documents')
        return JsonResponse({'success': 'Files uploaded successfully.'})
    
    return JsonResponse({'error': 'Invalid request.'}, status=400)


# Delete multi documents,
# id : '156126,16126,126126'  
@login_required
def delete_document(request):
    if request.POST.get('id') is None:
        return JsonResponse({"error":"Error: No ID provided"})
    else:
        ids = request.POST.get('id').split(',')
        for id in ids:
            document = Document.objects.get(id=id)
            if document is None: continue
            os.remove(os.path.join(settings.MEDIA_ROOT, str(request.user.id), document.file.url.split('/')[-1]))
            document.deleted = True
            document.save()
            shutil.rmtree(os.path.join(settings.MEDIA_ROOT, str(request.user.id), str(id)))
        redirect('/documents')
        return JsonResponse({"error":"Success"})


# chat page
@login_required
def chat_page(request, document_id):
    if len(Document.objects.filter(id = document_id)) == 0:
        return redirect('/404')
    document = Document.objects.get(id=document_id)
    initial_question = '''
        create only 3 questions I can ask you to help me to know summary, purpose and information of this pdf. do numbering questions e.g. 1.xxx, 2.yyy. 
        I don't need any other answers.
    '''
    questions: str = get_answer(initial_question, request.user.id, document_id, save=False)
    chat_history_path = os.path.join(settings.MEDIA_ROOT, str(request.user.id), str(document_id), 'history.json')
    chats = []
    if os.path.exists(chat_history_path):
        with open(chat_history_path) as json_file:
        # Read the JSON data from the file
            chats = json.load(json_file)
    for chat in chats:
        chat['answer'] = chat['answer'].replace('\n', '<br>')
        chat['sent'] = datetime.datetime.fromisoformat(chat['sent'])
        chat['received'] = datetime.datetime.fromisoformat(chat['received'])
    return render(request, 'app-chat.html', {'chats':chats, 'document': document, 'questions':questions.split('<br>')})


# handle chat
def chat(request):
    user_id = request.user.id
    current_level = current_best_plan(user_id)
    if chat_limits[current_level] <= get_chats_monthly(user_id):
        return HttpResponse('<span class="text-danger" style="font-style: italic">Questions a month limited. Please upgrade if you want more!</span>')
    question = request.POST.get('question')
    document_id = request.POST.get('documentId')
    response = get_answer(question, request.user.id, document_id)
    chat = Chat()
    chat.user = User.objects.get(id=request.user.id)
    chat.save()
    return HttpResponse(response)


# delete all chat history
@login_required
def delete_history(request):
    if request.POST.get('documentId') is None:
        return JsonResponse({"message":"Error: No ID provided"})
    else:
        id = request.POST.get('documentId')
        chat_history_path = os.path.join(settings.MEDIA_ROOT, str(request.user.id), str(id), 'history.json')
        if os.path.exists(chat_history_path):
            os.remove(chat_history_path)

        return JsonResponse({"message":"Success"})
  

@login_required
def setting(request):
    return render(request, 'setting.html')


@login_required
def faq(request):
    return render(request, 'faq.html')

from urllib.parse import urlparse, parse_qs

# @login_required
def pricing(request):
    if not request.user.is_authenticated:
        return render(request, 'pricing.html')
    parsed_url = urlparse(request.build_absolute_uri())
    query_params = parse_qs(parsed_url.query)
    if 'success' in query_params:
        return render(request, 'pricing.html', {'email': request.user.email, 'current_plan': current_best_plan(request.user.id), 'success':'Subscription succeeded!'})
    else:
        return render(request, 'pricing.html', {'email': request.user.email, 'current_plan': current_best_plan(request.user.id)})
    
# stripe webhook
def stripe_webhook(request):
    stripe.api_key = STRIPE_SECRET_KEY
    event = None
    payload = request.body
    try:
        event = json.loads(payload)
    except json.decoder.JSONDecodeError as e:
        print('⚠️  Webhook error while parsing basic request.' + str(e))
        return HttpResponse(status=400)
    if ENDPOINT_SECRET_KEY:
        # Only verify the event if there is an endpoint secret defined
        # Otherwise use the basic event deserialized with json
        sig_header = request.headers.get('stripe-signature')
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, ENDPOINT_SECRET_KEY
            )
        except stripe.error.SignatureVerificationError as e:
            print('⚠️  Webhook signature verification failed.' + str(e))
            return HttpResponse(status=400)

    # Handle the event
    if event is None:
        return HttpResponse(status=400)
    # Handle the event
    if event['type'] == 'charge.dispute.funds_withdrawn':
        dispute = event['data']['object']
        invoice = Billing.objects.get(paymentIntentId=dispute['payment_intent'])
        invoice.status = 'disputed'
        invoice.save()
        print('disputed', dispute)
    elif event['type'] == 'invoice.payment_succeeded':
        invoice = event['data']['object']
        print('paid', invoice)
        new_billing = Billing()
        new_billing.user = User.objects.get(email=invoice["customer_email"])
        new_billing.paymentIntentId = invoice["payment_intent"]
        new_billing.product_id = invoice['lines']["data"][0]["price"]["product"]
        new_billing.save()
    # ... handle other event types
    else:
        print('Unhandled event type {}'.format(event['type']))

    return HttpResponse(status=200)

# faq page
def faq(request):
    return render(request, 'faq.html', {'faqs': faqs})

def about(request):
    return render(request, 'about.html')
