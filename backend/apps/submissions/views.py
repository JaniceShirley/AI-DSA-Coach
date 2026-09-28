from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Count, Avg, Q
from django.utils import timezone

from apps.problems.models import Problem, TestCase
from apps.progress.models import UserProblemProgress
from apps.submissions.models import Submission
from apps.submissions.serializers import (
    SubmissionSerializer,
    RunCodeRequestSerializer,
    SubmitCodeRequestSerializer,
    RunCodeResponseSerializer
)
from apps.submissions.services.execution_service import CodeExecutionService
from apps.problems.serializers import ProblemListSerializer

class RunCodeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = RunCodeRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        problem_id = serializer.validated_data['problem_id']
        code = serializer.validated_data['code']
        language = serializer.validated_data.get('language', 'python')

        try:
            problem = Problem.objects.get(id=problem_id)
        except Problem.DoesNotExist:
            return Response({'detail': f'Problem {problem_id} not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Get public test cases only for RUN
        public_test_cases = list(TestCase.objects.filter(problem=problem, is_public=True))
        if not public_test_cases:
            # Fallback mock testcase from examples if no DB testcases exist yet
            for idx, ex in enumerate(problem.examples or []):
                public_test_cases.append(TestCase(
                    id=idx + 1,
                    problem=problem,
                    input_data=ex.get('input', ''),
                    expected_output=ex.get('output', ''),
                    is_public=True
                ))

        result = CodeExecutionService.execute_code(code=code, test_cases=public_test_cases, language=language)
        response_serializer = RunCodeResponseSerializer(data=result)
        response_serializer.is_valid()
        return Response(response_serializer.data, status=status.HTTP_200_OK)

class SubmitCodeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = SubmitCodeRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        problem_id = serializer.validated_data['problem_id']
        code = serializer.validated_data['code']
        language = serializer.validated_data.get('language', 'python')

        try:
            problem = Problem.objects.get(id=problem_id)
        except Problem.DoesNotExist:
            return Response({'detail': f'Problem {problem_id} not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Get all test cases (public + hidden) for SUBMIT
        all_test_cases = list(TestCase.objects.filter(problem=problem))
        if not all_test_cases:
            for idx, ex in enumerate(problem.examples or []):
                all_test_cases.append(TestCase(
                    id=idx + 1,
                    problem=problem,
                    input_data=ex.get('input', ''),
                    expected_output=ex.get('output', ''),
                    is_public=True
                ))

        exec_res = CodeExecutionService.execute_code(code=code, test_cases=all_test_cases, language=language)
        sub_status = exec_res['status']

        # Save submission to database
        submission = Submission.objects.create(
            user=request.user,
            problem=problem,
            code=code,
            language=language,
            status=sub_status,
            runtime=exec_res['runtime'],
            memory=exec_res['memory'],
            error_message=exec_res['error_message'],
            test_cases_passed=exec_res['test_cases_passed'],
            total_test_cases=exec_res['total_test_cases']
        )

        # Update UserProblemProgress
        now = timezone.now()
        progress, _ = UserProblemProgress.objects.get_or_create(
            user=request.user,
            problem=problem,
            defaults={'status': 'UNSOLVED', 'attempts': 0, 'time_spent': 0}
        )

        progress.attempts += 1
        if sub_status == 'ACCEPTED':
            progress.status = 'SOLVED'
            if not progress.solved_at:
                progress.solved_at = now
        elif progress.status != 'SOLVED':
            progress.status = 'ATTEMPTED'

        history = list(progress.submission_history or [])
        history.append({
            'submission_id': submission.id,
            'status': sub_status,
            'runtime': exec_res['runtime'],
            'test_cases_passed': exec_res['test_cases_passed'],
            'timestamp': now.isoformat()
        })
        progress.submission_history = history
        progress.save()

        return Response(SubmissionSerializer(submission).data, status=status.HTTP_201_CREATED)

class SubmissionListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        problem_id = request.query_params.get('problem_id')
        queryset = Submission.objects.filter(user=request.user)
        if problem_id:
            queryset = queryset.filter(problem_id=problem_id)

        submissions = queryset.order_by('-created_at')[:20]
        return Response(SubmissionSerializer(submissions, many=True).data, status=status.HTTP_200_OK)

class SubmissionDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, submission_id):
        try:
            submission = Submission.objects.get(id=submission_id, user=request.user)
        except Submission.DoesNotExist:
            return Response({'detail': f'Submission {submission_id} not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(SubmissionSerializer(submission).data, status=status.HTTP_200_OK)

class AnalyticsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        total_problems = Problem.objects.count()

        # Database aggregations via Django ORM
        user_submissions = Submission.objects.filter(user=user)
        total_submissions = user_submissions.count()

        user_progress = UserProblemProgress.objects.filter(user=user)
        solved_count = user_progress.filter(status='SOLVED').count()
        attempted_count = user_progress.count()

        success_rate = round((solved_count / attempted_count * 100), 1) if attempted_count > 0 else 0.0

        # Average attempts per solved problem
        solved_entries = user_progress.filter(status='SOLVED')
        avg_attempts_res = solved_entries.aggregate(avg_att=Avg('attempts'))
        avg_attempts = round(avg_attempts_res['avg_att'], 1) if avg_attempts_res['avg_att'] else 0.0

        # Average solving time in minutes
        avg_time_res = solved_entries.aggregate(avg_t=Avg('time_spent'))
        avg_time_mins = round((avg_time_res['avg_t'] or 0) / 60, 1)

        # Solved by difficulty
        all_problems = Problem.objects.all()
        solved_problem_ids = set(user_progress.filter(status='SOLVED').values_list('problem_id', flat=True))

        difficulty_counts = {'Easy': {'solved': 0, 'total': 0}, 'Medium': {'solved': 0, 'total': 0}, 'Hard': {'solved': 0, 'total': 0}}
        for p in all_problems:
            d = p.difficulty
            if d in difficulty_counts:
                difficulty_counts[d]['total'] += 1
                if p.id in solved_problem_ids:
                    difficulty_counts[d]['solved'] += 1

        # Topic Breakdown & Weakest Topic Identification for Recommendation System
        topic_stats = {}
        for p in all_problems:
            is_solved = p.id in solved_problem_ids
            for t in (p.topics or []):
                if t not in topic_stats:
                    topic_stats[t] = {'topic': t, 'solved': 0, 'total': 0}
                topic_stats[t]['total'] += 1
                if is_solved:
                    topic_stats[t]['solved'] += 1

        topic_list = []
        weakest_topic = None
        min_pct = 101.0

        for t_name, data in topic_stats.items():
            pct = round((data['solved'] / data['total']) * 100, 1) if data['total'] > 0 else 0.0
            topic_list.append({
                'topic': t_name,
                'solved': data['solved'],
                'total': data['total'],
                'percentage': pct
            })
            if pct < min_pct and data['solved'] < data['total']:
                min_pct = pct
                weakest_topic = t_name

        # Rule-based Recommendation System: Recommend unsolved problem from weakest topic
        recommended_problem = None
        if weakest_topic:
            candidate = Problem.objects.filter(
                ~Q(id__in=solved_problem_ids)
            ).filter(topics__icontains=weakest_topic).first()
            if candidate:
                recommended_problem = ProblemListSerializer(candidate, context={'request': request}).data

        if not recommended_problem:
            candidate = Problem.objects.exclude(id__in=solved_problem_ids).first()
            if candidate:
                recommended_problem = ProblemListSerializer(candidate, context={'request': request}).data

        recent_submissions = user_submissions.order_by('-created_at')[:5]

        return Response({
            'total_problems': total_problems,
            'solved_count': solved_count,
            'attempted_count': attempted_count,
            'total_submissions': total_submissions,
            'success_rate': success_rate,
            'average_attempts_per_solved': avg_attempts,
            'average_solving_time_minutes': avg_time_mins,
            'solved_by_difficulty': difficulty_counts,
            'solved_by_topic': topic_list,
            'recommended_problem': recommended_problem,
            'recent_submissions': SubmissionSerializer(recent_submissions, many=True).data
        }, status=status.HTTP_200_OK)
