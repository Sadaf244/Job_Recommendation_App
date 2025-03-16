from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.Login.as_view()),
    path('recruiter-registration/', views.CreateRecruiterAccount.as_view()),
    path('jobseeker-registeration/', views.CreateJobSeekerAccount.as_view()),
    path('add-jobs/', views.CreateJob.as_view()),
    path('get-jobs-list/', views.GetJobList.as_view()),
    ]