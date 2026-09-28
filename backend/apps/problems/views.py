from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Q
from apps.problems.models import Problem
from apps.problems.serializers import ProblemListSerializer, ProblemDetailSerializer

class ProblemListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        search = request.query_params.get('search', '').strip()
        difficulty = request.query_params.get('difficulty', '').strip()
        topic = request.query_params.get('topic', '').strip()
        status_filter = request.query_params.get('status_filter', '').strip()

        queryset = Problem.objects.all().order_by('id')

        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )

        if difficulty and difficulty != 'All':
            queryset = queryset.filter(difficulty__iexact=difficulty)

        problems = list(queryset)

        # In-memory filter for JSON topics and user_status
        filtered_problems = []
        for problem in problems:
            if topic and topic != 'All':
                if topic not in (problem.topics or []):
                    continue

            serializer = ProblemListSerializer(problem, context={'request': request})
            problem_data = serializer.data

            if status_filter and status_filter != 'All':
                if problem_data['user_status'].upper() != status_filter.upper():
                    continue

            filtered_problems.append(problem_data)

        return Response(filtered_problems, status=status.HTTP_200_OK)

class ProblemDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, slug):
        try:
            problem = Problem.objects.get(slug=slug)
        except Problem.DoesNotExist:
            return Response({'detail': f'Problem with slug "{slug}" not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ProblemDetailSerializer(problem, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
