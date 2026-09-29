from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import InterviewSession
from .serializers import (
    StartInterviewRequestSerializer,
    InterviewRespondRequestSerializer,
    InterviewCodeRequestSerializer,
    InterviewSessionListSerializer,
    InterviewSessionDetailSerializer,
    InterviewEvaluationSerializer,
)
from .services import interview_service

class InterviewStartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = StartInterviewRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = interview_service.start_interview(
                user=request.user,
                difficulty=serializer.validated_data.get('difficulty'),
                topic=serializer.validated_data.get('topic'),
                problem_id=serializer.validated_data.get('problem_id')
            )
            return Response(result, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class InterviewListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sessions = InterviewSession.objects.filter(user=request.user).order_by('-created_at')
        serializer = InterviewSessionListSerializer(sessions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class InterviewDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, session_id):
        session = get_object_or_404(InterviewSession, id=session_id, user=request.user)
        serializer = InterviewSessionDetailSerializer(session)
        return Response(serializer.data, status=status.HTTP_200_OK)

class InterviewRespondView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, session_id):
        session = get_object_or_404(InterviewSession, id=session_id, user=request.user)
        serializer = InterviewRespondRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        student_msg = serializer.validated_data['message']
        result = interview_service.respond(session, student_msg)
        return Response(result, status=status.HTTP_200_OK)

class InterviewCodeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, session_id):
        session = get_object_or_404(InterviewSession, id=session_id, user=request.user)
        serializer = InterviewCodeRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        submission_id = serializer.validated_data['submission_id']
        try:
            result = interview_service.associate_code_submission(session, submission_id)
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class InterviewEndView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, session_id):
        session = get_object_or_404(InterviewSession, id=session_id, user=request.user)
        evaluation = interview_service.end_interview(session)
        serializer = InterviewEvaluationSerializer(evaluation)
        return Response(serializer.data, status=status.HTTP_200_OK)

class InterviewFeedbackView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, session_id):
        session = get_object_or_404(InterviewSession, id=session_id, user=request.user)
        if hasattr(session, 'evaluation'):
            serializer = InterviewEvaluationSerializer(session.evaluation)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        evaluation = interview_service.end_interview(session)
        serializer = InterviewEvaluationSerializer(evaluation)
        return Response(serializer.data, status=status.HTTP_200_OK)
