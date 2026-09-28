from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from apps.problems.models import Problem
from apps.progress.models import UserProblemProgress
from apps.progress.serializers import (
    UserProblemProgressSerializer,
    ProgressAttemptSerializer,
    DashboardStatsSerializer
)
from apps.problems.serializers import ProblemListSerializer

class DashboardProgressView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        total_problems = Problem.objects.count()
        progress_entries = UserProblemProgress.objects.filter(user=user)
        progress_map = {p.problem_id: p for p in progress_entries}

        solved_count = progress_entries.filter(status='SOLVED').count()
        attempted_count = progress_entries.count()
        current_streak = 1 if solved_count > 0 else 0

        # Calculate Topic Breakdown
        all_problems = Problem.objects.all()
        topic_totals = {}
        topic_solved = {}

        for p in all_problems:
            p_status = progress_map[p.id].status if p.id in progress_map else 'UNSOLVED'
            for t in (p.topics or []):
                topic_totals[t] = topic_totals.get(t, 0) + 1
                if p_status == 'SOLVED':
                    topic_solved[t] = topic_solved.get(t, 0) + 1

        topic_progress_list = []
        for t, total in topic_totals.items():
            solved = topic_solved.get(t, 0)
            percentage = round((solved / total) * 100, 1) if total > 0 else 0.0
            topic_progress_list.append({
                'topic': t,
                'solved': solved,
                'total': total,
                'percentage': percentage
            })

        # Recent problems
        recent_entries = progress_entries.filter(
            status__in=['SOLVED', 'ATTEMPTED']
        ).order_by('-solved_at', '-id')[:5]

        recent_problems = [e.problem for e in recent_entries]
        recent_serialized = ProblemListSerializer(
            recent_problems, many=True, context={'request': request}
        ).data

        # Recommended problem
        unsolved_problems = [p for p in all_problems if p.id not in progress_map or progress_map[p.id].status != 'SOLVED']
        recommended_problem = None
        if unsolved_problems:
            rec = next((p for p in unsolved_problems if p.difficulty == 'Easy'), unsolved_problems[0])
            recommended_problem = ProblemListSerializer(rec, context={'request': request}).data

        data = {
            'total_problems': total_problems,
            'solved_count': solved_count,
            'attempted_count': attempted_count,
            'current_streak': current_streak,
            'topic_progress': topic_progress_list,
            'recent_problems': recent_serialized,
            'recommended_problem': recommended_problem
        }
        return Response(data, status=status.HTTP_200_OK)

class ProblemProgressDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, problem_id):
        try:
            problem = Problem.objects.get(id=problem_id)
        except Problem.DoesNotExist:
            return Response({'detail': f'Problem with id {problem_id} not found.'}, status=status.HTTP_404_NOT_FOUND)

        progress, created = UserProblemProgress.objects.get_or_create(
            user=request.user,
            problem=problem,
            defaults={'status': 'UNSOLVED', 'attempts': 0, 'time_spent': 0}
        )
        serializer = UserProblemProgressSerializer(progress)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, problem_id):
        try:
            problem = Problem.objects.get(id=problem_id)
        except Problem.DoesNotExist:
            return Response({'detail': f'Problem with id {problem_id} not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ProgressAttemptSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        new_status = serializer.validated_data['status']
        time_spent = serializer.validated_data.get('time_spent', 0)
        code = serializer.validated_data.get('code', '')

        progress, created = UserProblemProgress.objects.get_or_create(
            user=request.user,
            problem=problem,
            defaults={
                'status': new_status,
                'attempts': 1,
                'time_spent': time_spent
            }
        )

        now = timezone.now()
        if not created:
            progress.attempts += 1
            progress.time_spent += time_spent
            if new_status == 'SOLVED':
                progress.status = 'SOLVED'
                if not progress.solved_at:
                    progress.solved_at = now
            elif progress.status != 'SOLVED' and new_status == 'ATTEMPTED':
                progress.status = 'ATTEMPTED'
        else:
            if new_status == 'SOLVED':
                progress.solved_at = now

        if code:
            history = list(progress.submission_history or [])
            history.append({
                'code': code,
                'status': new_status,
                'timestamp': now.isoformat()
            })
            progress.submission_history = history

        progress.save()
        return Response(UserProblemProgressSerializer(progress).data, status=status.HTTP_200_OK)
