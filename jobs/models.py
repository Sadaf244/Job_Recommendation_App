from django.db import models
from django.contrib.auth.models import AbstractUser
import re
import logging
from django.shortcuts import render, get_object_or_404
from resume.utils import standardize_skills
# Create your models here.


class User(AbstractUser):
    email = models.EmailField(unique=True, null=True, blank=True)
    username = models.CharField(max_length=20, unique=True, null=True, blank=True)
    is_jobseeker = models.BooleanField(default=False)
    is_recruiter = models.BooleanField(default=False)

    def __str__(self):
        return self.username


class Job(models.Model):
    recruiter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='jobs')
    title = models.CharField(max_length=100, null=True, blank=True)
    job_description = models.TextField()
    address = models.CharField(max_length=100, null=True, blank=True)
    experience = models.CharField(max_length=100, null=True, blank=True)
    posted_on = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def create_job(user, title, job_description, address, experience):
        job = Job.objects.create(recruiter=user, title=title, job_description=job_description, address=address,
                               experience=experience)
        return job

    def matches_resume(self, resume):

        resume_skills = resume.parsed_data.get("Skills", "")
        resume_experience = resume.parsed_data.get("Overall Total Experience", "")

        # Ensure resume_skills is a string
        if isinstance(resume_skills, list):
            resume_skills = ", ".join(resume_skills)
        resume_skills = resume_skills.split(", ")

        # Standardize skills using the ontology
        job_skills = self.job_description.lower().split()
        job_skills = standardize_skills(job_skills)
        resume_skills = standardize_skills(resume_skills)

        # Skill matching: Calculate overlap percentage
        skill_match = len(set(job_skills).intersection(set(resume_skills))) / len(job_skills) if job_skills else 0

        # Experience matching
        try:
            resume_experience_years = int(resume_experience.split()[0])
            job_experience_years = int(self.experience.split()[0])
            experience_match = 1 if resume_experience_years >= job_experience_years else 0
        except (ValueError, IndexError):
            experience_match = 0

        skill_weight = 0.6
        experience_weight = 0.4
        weighted_score = (skill_match * skill_weight) + (experience_match * experience_weight)
        print(weighted_score)
        return weighted_score >= 0.5


class Resume(models.Model):
    job_seeker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resume', null=True, blank=True)
    file = models.FileField()
    created_at = models.DateTimeField(auto_now_add=True)
    parsed_data = models.JSONField(default=dict)

    @staticmethod
    def get_or_create_resume_data(user, file, parsed_data):
        resume=None
        try:
            is_exists=Resume.objects.filter(job_seeker=user).exists()
            if not is_exists :
                resume=Resume.objects.create(job_seeker=user, file=file, parsed_data=parsed_data)
            else:
               resume=Resume.objects.get(job_seeker=user)
        except Exception as e:
            logging.error(f"Error in get_or_create_resume_data: {e}")
        return resume


class UserSignupValidation:

    def validate_signup_data(self, username, email):
        errors = {}
        if not username or username.strip() == "":
            errors = 'Username is required'
        elif not email or email.strip() == "":
            errors = 'Email address is required'
        elif User.objects.filter(username=username).exists():
            errors = 'Username is already in use'
        elif User.objects.filter(email=email).exists():
            errors = 'Email address is already in use'

        email_regex = re.compile(
            r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        )

        if not email_regex.match(email):
            errors = 'Please provide a valid email address (e.g., username@gmail.com)'

        if errors:
            return {'status': False, 'message': errors}
        return {'status': True, 'message': 'Validation successful'}


class User_Manager:
    def __init__(self, request):
        self.request = request

    def recruiter_registration(self):
        username = self.request.data.get('username')
        email = self.request.data.get('email')
        password = self.request.data.get('password')

        validate_signup = UserSignupValidation()
        resp_dict = validate_signup.validate_signup_data(username, email)

        if not resp_dict['status']:
            return resp_dict
        try:
            User.objects.create_user(username=username, email=email, password=password, is_recruiter=True)
            resp_dict.update({'status': True, 'message': 'User account created successfully'})
        except Exception as e:
            logging.error('Getting exception on recruiter_registration: %s', repr(e))
            resp_dict.update({'status': False, 'message': 'An error occurred while creating the user'})

        print(resp_dict)  # Debugging statement
        return resp_dict

    def jobseeker_registration(self):
        username = self.request.data.get('username')
        email = self.request.data.get('email')
        password = self.request.data.get('password')

        validate_signup = UserSignupValidation()
        resp_dict = validate_signup.validate_signup_data(username, email)

        if not resp_dict['status']:
            return resp_dict
        try:
            User.objects.create_user(username=username, email=email, password=password, is_jobseeker=True)
            resp_dict.update({'status': True, 'message': 'User account created successfully'})
        except Exception as e:
            logging.error('Getting exception on recruiter_registration: %s', repr(e))
            resp_dict.update({'status': False, 'message': 'An error occurred while creating the user'})

        return resp_dict

class Job_manager:
    def __init__(self, request, user):
        self.request = request
        self.user = user

    def add_job(self):
        resp_dict = dict(status=False, message="Something went wrong")
        try:
            title = self.request.data.get('title', None)
            job_description = self.request.data.get('job_description', None)
            address = self.request.data.get('address', None)
            experience = self.request.data.get('experience', 0)
            if title is not None and job_description is not None and address is not None:
                Job.create_job(self.request.user, title, job_description, address, experience)
                resp_dict['status'] = True
                resp_dict['message'] = "Successfully Job added"
        except Exception as e:
            logging.error('Getting exception on add_job: %s', repr(e))
            resp_dict.update({'status': False, 'message': 'An error occurred while adding job'})
        return resp_dict

    def get_job_list(self):
        resp_dict = dict(data=[], status=False, message="Something went wrong")
        try:
            # Get the user's resume
            resume = get_object_or_404(Resume, job_seeker=self.user)

            # Get matching jobs
            matching_jobs = []
            for job in Job.objects.all():
                if job.matches_resume(resume):
                    matching_jobs.append({
                        "id": job.id,
                        "title": job.title,
                        "job_description": job.job_description,
                        "address": job.address,
                        "experience": job.experience,
                        "posted_on": job.posted_on.strftime("%Y-%m-%d %H:%M:%S"),  # Format datetime
                    })

            resp_dict['data'] = matching_jobs
            resp_dict['status'] = True
            resp_dict['message'] = "Successfully Retrieved Jobs"
        except Exception as e:
            logging.error('Getting exception on getting_job: %s', repr(e))
            resp_dict.update({'status': False, 'message': 'An error occurred while getting jobs'})
        return resp_dict