from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from .utils import *
from jobs.models import *
from rest_framework.permissions import IsAuthenticated
from jobs.authentication import JWTAuthentication



class ResumeUploadView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = (IsAuthenticated,)
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        file = request.FILES.get("file")
        if file.name.lower().endswith('.pdf'):
            text = extract_text_from_pdf(file)
        elif file.name.lower().endswith('.docx'):
            text = extract_text_from_docx(file)
        else:
            return Response({"error": "Unsupported file format"}, status=400)

        parsed_data = parse_resume(text)

        resume = Resume.get_or_create_resume_data(user=request.user, file=file, parsed_data=parsed_data)
        return Response({"parsed_data": resume.parsed_data})





