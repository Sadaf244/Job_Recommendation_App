from django.http import JsonResponse
from django.contrib.auth import authenticate
from rest_framework.permissions import AllowAny
from .models import *
from datetime import datetime, timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .authentication import *

class CreateRecruiterAccount(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        resp_dict = dict()
        resp_dict['status'] = False
        resp_dict['message'] = "Something went wrong. Please try again after sometime"
        try:
            create_user_manager = User_Manager(request)
            save_user_resp = create_user_manager.recruiter_registration()
            resp_dict['status'] = save_user_resp['status']
            resp_dict['message'] = save_user_resp['message']
        except Exception as e:
            logging.error('Error in creating account', repr(e))
        return JsonResponse(resp_dict, status=200)


class CreateJobSeekerAccount(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        resp_dict = dict()
        resp_dict['status'] = False
        resp_dict['message'] = "Something went wrong. Please try again after sometime"
        try:
            create_user_manager = User_Manager(request)
            save_user_resp = create_user_manager.jobseeker_registration()
            resp_dict['status'] = save_user_resp['status']
            resp_dict['message'] = save_user_resp['message']
        except Exception as e:
            logging.error('Error in creating account', repr(e))
        return JsonResponse(resp_dict, status=200)


class Login(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(username=username, password=password)
        if user is None:
            raise AuthenticationFailed('Invalid credentials')

        payload = {
            'user_id': user.id,
            'exp': datetime.utcnow() + timedelta(days=1)
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
        return Response({'token': token}, status=status.HTTP_200_OK)


class CreateJob(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = (IsAuthenticated,)

    def post(self, request):
            resp_dict = dict()

            resp_dict['status'] = False
            resp_dict['message'] = "Something went wrong. Please try again after sometime"
            try:
                user = request.user
                create_job_manager = Job_manager(request, user)
                save_user_resp = create_job_manager.add_job()
                resp_dict['status'] = save_user_resp['status']
                resp_dict['message'] = save_user_resp['message']
            except Exception as e:
                logging.error('Error in adding job', repr(e))
            return JsonResponse(resp_dict, status=200)


class GetJobList(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = (IsAuthenticated,)

    def get(self, request):
            resp_dict = dict()

            resp_dict['status'] = False
            resp_dict['message'] = "Something went wrong. Please try again after sometime"
            try:
                user=request.user
                list_job_manager = Job_manager(request, user)
                save_user_resp = list_job_manager.get_job_list()
                resp_dict['data']=save_user_resp['data']
                resp_dict['status'] = save_user_resp['status']
                resp_dict['message'] = save_user_resp['message']
            except Exception as e:
                logging.error('Error in adding job', repr(e))
            return JsonResponse(resp_dict, status=200)