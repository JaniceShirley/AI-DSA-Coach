from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from apps.problems.models import Problem
from .models import CoachingInteraction
from .serializers import (
    HintRequestSerializer,
    ChallengeRequestSerializer,
    AlternativeRequestSerializer,
    FeedbackRequestSerializer,
    CoachingInteractionSerializer,
)
from .ai_service import ai_coach_service

class HintView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = HintRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        problem_id = serializer.validated_data['problem_id']
        problem = get_object_or_404(Problem, id=problem_id)

        result = ai_coach_service.generate_hint(
            user=request.user,
            problem=problem,
            student_code=serializer.validated_data['student_code'],
            submission_id=serializer.validated_data.get('submission_id'),
            requested_level=serializer.validated_data.get('requested_level')
        )
        return Response(result, status=status.HTTP_200_OK)

class ChallengeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChallengeRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        problem_id = serializer.validated_data['problem_id']
        problem = get_object_or_404(Problem, id=problem_id)

        result = ai_coach_service.challenge_understanding(
            user=request.user,
            problem=problem,
            student_code=serializer.validated_data['student_code'],
            user_answer=serializer.validated_data.get('user_answer')
        )
        return Response(result, status=status.HTTP_200_OK)

class AlternativeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AlternativeRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        problem_id = serializer.validated_data['problem_id']
        problem = get_object_or_404(Problem, id=problem_id)

        result = ai_coach_service.generate_alternative_approach(
            user=request.user,
            problem=problem,
            student_code=serializer.validated_data['student_code']
        )
        return Response(result, status=status.HTTP_200_OK)

class FeedbackView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = FeedbackRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        problem_id = serializer.validated_data['problem_id']
        problem = get_object_or_404(Problem, id=problem_id)

        result = ai_coach_service.generate_feedback(
            user=request.user,
            problem=problem,
            student_code=serializer.validated_data['student_code'],
            submission_id=serializer.validated_data.get('submission_id')
        )
        return Response(result, status=status.HTTP_200_OK)

class HistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, problem_id):
        problem = get_object_or_404(Problem, id=problem_id)
        interactions = CoachingInteraction.objects.filter(
            user=request.user,
            problem=problem
        ).order_by('-created_at')
        
        serializer = CoachingInteractionSerializer(interactions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class CoachModeView(APIView):
    """
    Returns current AI Coach model backend mode (e.g. fine-tuned, base, mock)
    and version metadata for development and admin visibility.
    """
    permission_classes = []

    def get(self, request):
        provider = ai_coach_service.provider
        if hasattr(provider, 'get_mode_info'):
            info = provider.get_mode_info()
        else:
            import os
            backend_mode = os.getenv("AI_MODEL_BACKEND", "finetuned").lower()
            info = {
                "mode": backend_mode,
                "is_fine_tuned": "fine" in backend_mode,
                "model_version": "dsa-coach-qlora-v1"
            }
        return Response(info, status=status.HTTP_200_OK)
