from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views
from django.views.decorators.csrf import csrf_exempt

app_name = 'chatbase'

urlpatterns = [
    path('login', views.login_view, name='login_page'),
    path('register', views.register_view, name='login_page'),
    path('', views.index, name='index'),
    path('logout', views.log_out, name="log_out"),
    path('upload', views.upload, name='upload'),
    path('delete_document', views.delete_document, name='delete_document'),
    path('chatpage', views.chat_page, name='chatpage'),
    path('delete_history', views.delete_history, name='delete_history'),
    path('chat', views.chat, name='chat'),
    path('settings', views.setting, name='setting'),
    path('faq', views.faq, name='faq'),
    path('document/<int:document_id>', views.chat_page, name='document'),
    path('documents', views.documents, name='documents'),
    path('pricing', views.pricing, name='pricing'),
    path('webhook', csrf_exempt(views.stripe_webhook), name='webhook'),
    path('google_login', views.google_login, name='google_login'),
    path('verify/<str:token>', views.verify_email, name='verify_email'),
    path('resend_mail', views.resend_mail, name='resend_mail'),
    path('faq', views.faq, name="faq"),
    path('about', views.about, name='about')

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
