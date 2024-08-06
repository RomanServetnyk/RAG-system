import re, jwt, datetime, os, json
from django.conf import settings
from .models import (Document, User, Billing, Product, Chat, Verification)
from dotenv import load_dotenv
from django.http import (JsonResponse, HttpResponse)
from dateutil.relativedelta import relativedelta

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
ENDPOINT_SECRET_KEY = os.getenv("ENDPOINT_SECRIT_KEY")
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GMAIL_ADDRESS = os.getenv('GMAIL_ADDRESS')
GMAIL_APP_PASSWORD = os.getenv('GMAIL_APP_PASSWORD')

# convert openai response to html
def replace_markdown_bold_with_html(text):
    # Replace bold markdown with <strong> HTML tags
    new_text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text, flags=re.DOTALL)
    # Replace italic markdown with <i> HTML tags (avoiding matches within <strong> tags)
    new_text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<i>\1</i>', new_text, flags=re.DOTALL)
    # Replace multiline code block markdown with <code> HTML tags
    new_text = re.sub(r'\`\`\`([\s\S]*?)\`\`\`', r'<code>\1</code>', new_text)
    return new_text

# get token
def generate_jwt_token(email, password):
    payload = {
        'email': email,
        'password': password,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1),  # Token expiration time
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
    return token

# send verify mail
def send_verify_mail(user_email, token):
    subject = 'Confirm Your Email - PDF CAKE'
    email = user_email
    body = f'<table style="color:#000000; margin-top: 1.5rem; margin-right: 1rem; background-clip: padding-box; box-shadow: 0 0.125rem 0.625rem 0 rgba(76, 78, 100, 0.22); border-radius: 0.625rem; width: 100%; box-sizing: border-box;"><tbody><tr><td style="padding: 1.5rem; text-align: center; font-size: 24pt;">Welcome!</td></tr><tr><td style="padding-left: 1rem; padding-right: 1rem;">Thank you for signing up with PDF CAKE.</td></tr><tr><td style="padding-left: 1rem; padding-right: 1rem;">To begin your PDF CAKE journey, please confirm your signup.</td></tr><tr><td style="padding-left: 1rem; padding-right: 1rem;">Click the following button to confirm your signup:</td></tr><tr><td style="text-align: center; padding: 0.5rem;"><a type="button" style="padding: 0.5rem; padding-left: 1rem; padding-right: 1rem; display: inline-block; color: #fff; background-color: #666cff; border-color: #666cff; text-transform: uppercase; letter-spacing: 0.4px; box-shadow: 0px 4px 8px -4px rgba(76, 78, 100, 0.42); border-radius: 0.5rem; text-decoration: none;" href="https://pdfcake.com/verify/{token}">Confirm</a></td></tr><tr><td style="padding-left: 1rem; padding-right: 1rem;">Sincerely yours,</td></tr><tr><td style="padding-left: 1rem; padding-right: 1rem; padding-bottom: 1.5rem;">PDF CAKE Team</td></tr></tbody></table>'
    return send_mail(email, subject, body)


# resend verify mail
def resend_mail(request):
    if request.method == 'POST':
        verification_id = request.POST['verification_id']
        if Verification.objects.filter(id=verification_id).exists():
            verification = Verification.objects.get(id=verification_id)
            if verification.count >= 5:
                current_time = datetime.datetime.now()
                difference = current_time - verification.modified_at
                if difference < datetime.timedelta(hours=1):
                    return JsonResponse({'error':'Too many emails are sent. Please try after a hour'})
                else:
                    verification.count = 0
            email = verification.email
            password = verification.password
            token = generate_jwt_token(email, password)
            ok = send_verify_mail(email, token)
            if ok:
                verification.count += 1
                verification.save()
                return JsonResponse({'success':'Verification email is sent! please conform in your inbox.'})
            else:
                return JsonResponse({'error':'You are not available to send verification email now. Please try after a hour'})
        else: return JsonResponse({'error':'Bad Request.'})
    return JsonResponse({'error':'Invalid Request.'})


def send_mail(email, subject, body):
    try:
        # Set up SMTP server credentials
        smtp_server = 'smtp.gmail.com'
        port = 587  # TLS port

        # Sender and recipient details
        sender_email = GMAIL_ADDRESS
        receiver_email = email
        password = GMAIL_APP_PASSWORD  # Your Gmail account password

        # Create a multipart message object
        message = MIMEMultipart()
        message['From'] = sender_email
        message['To'] = receiver_email
        message['Subject'] = subject

        # Add email body
        mail_body=body
        message.attach(MIMEText(mail_body, 'html'))
        # Connect to the SMTP server, start TLS encryption, and login
        server = smtplib.SMTP(smtp_server, port)
        server.starttls()
        server.login(sender_email, password)

        # Send the email
        server.sendmail(sender_email, receiver_email, message.as_string())
        server.quit()
        return True
    except:
        return False

upload_limits = [1, 100, float('inf'), float('inf')]
chat_limits = [500, 5000, float('inf'), float('inf')]
file_size_limits = [limit * 1024 * 1024 for limit in [10, 50, 50, 100]]


def get_uploads_monthly(user_id):
    documents = Document.objects.filter(user=user_id)
    count_documents_month = 0
    
    end_datetime = datetime.datetime.now()  # Replace with your ending datetime
    start_datetime = end_datetime - relativedelta(months=1)  # Set start_datetime as one month ago
    
    for document in documents:
        if start_datetime <= document.created_at <= end_datetime:
            count_documents_month += 1
    return count_documents_month

def get_chats_monthly(user_id):
    chats = Chat.objects.filter(user=user_id)
    count_chats_month = 0
    for chat in chats:
        start_datetime = chat.created_at  # Replace with your starting datetime
        end_datetime = datetime.datetime.now()  # Replace with your ending datetime
        months_diff = relativedelta(end_datetime, start_datetime).months
        if months_diff == 0: count_chats_month += 1
    return count_chats_month
# User = get_user_model()

def current_best_plan(user):
    billings = Billing.objects.filter(user=user, status='paid')
    if len(billings) == 0:
        return 0
    best_plan = 0
    for billing in billings:
        start_datetime = billing.created_at  # Replace with your starting datetime
        end_datetime = datetime.datetime.now()  # Replace with your ending datetime
        months_diff = relativedelta(end_datetime, start_datetime).months
        product = Product.objects.get(product_id=billing.product_id)
        if product is None or months_diff >= product.duration:
            continue
        if best_plan < product.level:
            best_plan = product.level
    return best_plan

from langchain.vectorstores import Chroma
from langchain.document_loaders import PyMuPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings

# Create chromdb for each document when uploading
def read(user_id, document_id):
    document = Document.objects.get(id=document_id)
    file_path = os.path.join(settings.MEDIA_ROOT, document.file.path)
    documents = []
    if document.need_ocr:
        text_path = get_ocr_text(file_path)
        file_loader = TextLoader(text_path)
        documents = file_loader.load()
        print(text_path)
        os.remove(text_path)
    else: 
        file_loader = PyMuPDFLoader(file_path)
        documents = file_loader.load()
    text_splitter = RecursiveCharacterTextSplitter(['\n\n', '\n', ' '], chunk_size=1000, chunk_overlap=20)
    docs = text_splitter.split_documents(documents)
    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
    persist_directory = os.path.join(settings.MEDIA_ROOT, str(user_id), str(document_id))
    if not os.path.exists(persist_directory):
        os.makedirs(persist_directory)
    try:
        db = Chroma.from_documents(docs, embeddings, persist_directory=persist_directory)
        db.persist()
    except:
        print('============ Empty PDF ==============')
    return persist_directory

from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import PromptTemplate
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chat_models import ChatOpenAI

# get answer to question
def get_answer(question, user_id, document_id, save=True):
    # Prompt
    template = """
                Act as a AI assistant that read PDF and chat with user to explain PDF.
                Following Context is data of PDF that user want to know about information of.
                Use the following pieces of context to answer the question.
                if the context is empty, answer that you can't get any data from the pdf and OCR may be needed
                You can provide answer based on the context and try to answer as much as possible.
                Keep the answer as concise as possible, explain in detail, add a deep thought at the end.
                Give more weight to the context.
                If the user sends a greeting such as 'hi','hello' and 'good morning', don't make other answers, just send the user greeting and ask what you can help.
                If you can't find answer in pdf, don't make wrong answer and say that pdf don't have information of that question.
                Present the results as HTML.
                To help the user to understand your answer easily and make your answer looks clean, try to use form of a bullet list, ordered list, table, break lines.
                Make topics, titles, and main words and sentences presented in bold or italic
                Don't begin your answer with new line.

                
                Context:{context}

                
                Question: {question}


                Helpful Answer:"""
    prompt = PromptTemplate(input_variables=["query", "context"], template=template)

    new_chat = {}
    new_chat['document'] = Document.objects.get(id=document_id).id
    new_chat['question'] = question
    new_chat['sent'] = datetime.datetime.now().isoformat()

    db = Chroma(persist_directory=os.path.join(settings.MEDIA_ROOT, str(user_id), str(document_id)), embedding_function=OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY))
    llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY, model_name='gpt-3.5-turbo')
    memory = ConversationBufferWindowMemory(memory_key='chat_history', return_messages=True)
    chat_history_path = os.path.join(settings.MEDIA_ROOT, str(user_id), str(document_id), 'history.json')
    chats = []
    if os.path.exists(chat_history_path) and save:
        with open(chat_history_path) as json_file:
        # Read the JSON data from the file
            chats = json.load(json_file)
            for chat in chats:
                memory.chat_memory.add_user_message(chat['question'])
                memory.chat_memory.add_ai_message(chat['answer'])
    qa = ConversationalRetrievalChain.from_llm(llm, retriever=db.as_retriever(), memory = memory)
    # qa.combine_docs_chain.llm_chain.prompt = prompt
    qa.combine_docs_chain.llm_chain.prompt = prompt
    # langchain
    try: 
        response: str = qa.run(question)
    except:
        response = ' '
    # response = "This is a answer"
    response = response.replace("\n", "<br>")
    while response.startswith('<br>'):
        response = response.lstrip('<br>')
    response = replace_markdown_bold_with_html(response)
    new_chat['answer'] = response
    new_chat['received'] = datetime.datetime.now().isoformat()
    chats.append(new_chat)
    if save: 
        with open(chat_history_path, 'w') as json_file:
            # Write the data to the JSON file
            json.dump(chats, json_file)

    return response



import platform
from tempfile import TemporaryDirectory
from pathlib import Path

import pytesseract
from pdf2image import convert_from_path
from PIL import Image


def get_ocr_text(pdf_path):
    # Get the directory of the PDF file
    pdf_directory = os.path.dirname(pdf_path)
    # Get the filename without extension
    pdf_filename = os.path.splitext(os.path.basename(pdf_path))[0]
    # Create the text file path by joining the directory, filename, and ".txt" extension
    text_file_path = os.path.join(pdf_directory, pdf_filename + ".txt")

    if platform.system() == "Windows":
        # We may need to do some additional downloading and setup...
        # Windows needs a PyTesseract Download
        # https://github.com/UB-Mannheim/tesseract/wiki/Downloading-Tesseract-OCR-Engine

        pytesseract.pytesseract.tesseract_cmd = (
            r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        )
 
    # Path of the Input pdf
    PDF_file = pdf_path

    # Store all the pages of the PDF in a variable
    image_file_list = []

    text_file = text_file_path
    ''' Main execution point of the program'''
    with TemporaryDirectory() as tempdir:
        # Create a temporary directory to hold our temporary images.

        """
        Part #1 : Converting PDF to images
        """

        pdf_pages = convert_from_path(PDF_file, 500)
        # Read in the PDF file at 500 DPI

        # Iterate through all the pages stored above
        for page_enumeration, page in enumerate(pdf_pages, start=1):
            # enumerate() "counts" the pages for us.

            # Create a file name to store the image
            filename = f"{tempdir}\page_{page_enumeration:03}.jpg"

            # Declaring filename for each page of PDF as JPG
            # For each page, filename will be:
            # PDF page 1 -> page_001.jpg
            # PDF page 2 -> page_002.jpg
            # PDF page 3 -> page_003.jpg
            # ....
            # PDF page n -> page_00n.jpg

            # Save the image of the page in system
            page.save(filename, "JPEG")
            image_file_list.append(filename)

        """
        Part #2 - Recognizing text from the images using OCR
        """

        with open(text_file, "a") as output_file:
            # Open the file in append mode so that
            # All contents of all images are added to the same file

            # Iterate from 1 to total number of pages
            for image_file in image_file_list:

                # Set filename to recognize text from
                # Again, these files will be:
                # page_1.jpg
                # page_2.jpg
                # ....
                # page_n.jpg

                # Recognize the text as string in image using pytesserct
                text = str(((pytesseract.image_to_string(Image.open(image_file)))))

                # The recognized text is stored in variable text
                # Any string processing may be applied on text
                # Here, basic formatting has been done:
                # In many PDFs, at line ending, if a word can't
                # be written fully, a 'hyphen' is added.
                # The rest of the word is written in the next line
                # Eg: This is a sample text this word here GeeksF-
                # orGeeks is half on first line, remaining on next.
                # To remove this, we replace every '-\n' to ''.
                text = text.replace("-\n", "")

                # Finally, write the processed text to the file.
                output_file.write(text)

            # At the end of the with .. output_file block
            # the file is closed after writing all the text.
        # At the end of the with .. tempdir block, the 
        # TemporaryDirectory() we're using gets removed!     
    
    return text_file
    # End of main function!

faqs = [
    {
        'name' : 'Usage & Features',
        'qas' : [
            {
                'question':"How can I utilize PDFCake?",
                'answer':'PDF Cake can be used for various purposes with your PDFs. You can ask questions, review documents, find information, and more in seconds. It saves you hours of scrolling and allows you to understand documents deeply in minutes. Try it for free yourself.'
            },
            {
                'question':"What kind of questions should I ask?",
                'answer':'Feel free to ask any question you want! We are here to provide answers and assist you with any type of question. Common questions include: "Can you summarize this document?" and "Give me the big takeaways from this document".'
            },
            {
                'question':"How does it work?",
                'answer':'Getting started is easy! Simply sign up, upload a document, and start chatting with it. You can ask questions and chat with your documents using natural language. The underlying AI model will retrieve any relevant information from the document and give you a well-informed answer.'
            },
            {
                'question':"What type of document can I upload?",
                'answer':'You can only upload PDF (.pdf) files at the moment. However, we are working to support more file types in the future.'
            },
            {
                'question' : 'What should I do if I\'m having trouble placing an subcription?',
                'answer' : 'For any technical difficulties you are experiencing with our website, please email us at <a href="javascript:void(0);">pdfcake@gmail.com</a>'
            }
        ]
    },
    {
        'name' : 'Functionality',
        'qas' : [
            {
                'question':"Does PDFCake support different languages?",
                'answer':'Yes, PDF Cake works with 90+ languages. You can upload documents in different languages, ask questions in various languages, and even translate between different languages.'
            },
            {
                'question':"Is the information provided accurate?",
                'answer':'PDFCake generates answers based on the content of the document you upload. If it\'s a legal document, our AI utilizes information from that document to provide accurate responses and find relevant information. It is accurate and uses the latest AI technology to be your partner to increase productivity and allow you to learn better.'
            },
            {
                'question':"What OpenAI model does PDF Cake use?",
                'answer':'We use gpt-3.5-turbo-16k for all paying customers. For freemium users, we use gpt-3.5-turbo (4K base model). The gpt-3.5-turbo-16k model offers four times the context length of the 4k base model.'
            },
            {
                'question':"Where are my files stored?",
                'answer':'Your uploaded documents undergo encryption both during storage and while being transferred. They are securely stored by our data storage provider, who holds a SOC2 Type II certification. We understand that some individuals prioritize data privacy, which is why we offer a private document option for processing PDF documents. By choosing this option, your documents will never come into contact with our cloud storage, ensuring their confidentiality.'
            },
        ]
    },
    {
        'name' : 'Pricing & Payment',
        'qas' : [
            {
                'question':"Is PDF Cake free?",
                'answer':'Yes, you can upload 1 PDF file (max 10MB) to try it out for free. We also have paid plans that give you more quota.'
            },
            {
                'question':"How do I pay for my order?",
                'answer':'We accept Visa®, MasterCard®, American Express®, and PayPal®. Our servers encrypt all information submitted to them, so you can be confident that your credit card information will be kept safe and secure.'
            },
            {
                'question':"Billing and refunds",
                'answer':'As a result of the product, we pay high cost to run the business, so we regret to inform you that we do not provide any form of refunds, whether partial or in full, at this time. However, you have the freedom to cancel your subscription effortlessly whenever you desire. Once you decide to cancel, no further charges will be incurred.'
            },
        ]
    }
]

import stripe
COUPON_ID = os.getenv('COUPON_ID')
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

def get_promotion_code():
    expiration_date = datetime.datetime.utcnow() + datetime.timedelta(days=1)
    try:
        promotion_response =  stripe.PromotionCode.create(
            coupon=COUPON_ID,
            active=True,
            expires_at=int(expiration_date.timestamp()),
            max_redemptions=1
        )
        return promotion_response.code
    except Exception as e:
        print(e)
        return None
    
# send welcome email
def send_welcome_email(email):
    subject = 'Welcome to PDF CAKE'
    try: 
        promotion_code = get_promotion_code()
        body = f'''
        <table style="color:#000000; margin-top: 1.5rem; margin-right: 1rem; background-clip: padding-box; box-shadow: 0 0.125rem 0.625rem 0 rgba(76, 78, 100, 0.22); border-radius: 0.625rem; width: 100%; box-sizing: border-box;">
          <tbody>
            <tr>
              <td style="padding: 1.5rem; text-align: center; font-size: 24pt;">Welcome!</td>
            </tr>
            <tr>
              <td style="padding-left: 1rem; padding-right: 1rem;">Thank you for signing up with PDF CAKE.</td>
            </tr>
            <tr>
              <td style="padding-left: 1rem; padding-right: 1rem;">As a token of appreciation, we're offering new users a 10% discount code.</td>
            </tr>
            <tr>
              <td style="padding-left: 1rem; padding-right: 1rem;">This code will expire in 24 hours, so don't miss this opportunity: {promotion_code}</td>
            </tr>
            <tr>
              <td style="padding-left: 1rem; padding-right: 1rem;">Sincerely yours,</td>
            </tr>
            <tr>
              <td style="padding-left: 1rem; padding-right: 1rem; padding-bottom: 1.5rem;">PDF CAKE Team</td>
            </tr>
          </tbody>
        </table>
        '''
        return send_mail(email, subject, body)
    except Exception as e:
        print(e)
        return False
