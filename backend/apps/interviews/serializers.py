from rest_framework import serializers
from apps.problems.models import Problem
from apps.problems.serializers import ProblemDetailSerializer
from apps.submissions.serializers import SubmissionSerializer
from .models import InterviewSession, InterviewMessage, InterviewEvaluation

class StartInterviewRequestSerializer(serializers.Serializer):
    difficulty = serializers.CharField(required=False, allow_blank=True, default='Any')
    topic = serializers.CharField(required=False, allow_blank=True, default='Any')
    problem_id = serializers.IntegerField(required=False, allow_null=True)

class InterviewRespondRequestSerializer(serializers.Serializer):
    message = serializers.CharField(min_length=1)

class InterviewCodeRequestSerializer(serializers.Serializer):
    submission_id = serializers.IntegerField()

class InterviewMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewMessage
        fields = ['id', 'role', 'message', 'stage', 'created_at']

class InterviewEvaluationSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewEvaluation
        fields = [
            'id',
            'overall_score',
            'problem_understanding',
            'approach_quality',
            'technical_reasoning',
            'complexity_analysis',
            'edge_case_awareness',
            'optimization',
            'communication',
            'coding_correctness',
            'strengths',
            'areas_for_improvement',
            'final_feedback',
            'recommended_topics',
            'recommended_problems',
            'created_at',
        ]

class InterviewSessionListSerializer(serializers.ModelSerializer):
    problem_title = serializers.CharField(source='problem.title', read_only=True)
    problem_slug = serializers.CharField(source='problem.slug', read_only=True)
    overall_score = serializers.SerializerMethodField()

    class Meta:
        model = InterviewSession
        fields = [
            'id',
            'problem',
            'problem_title',
            'problem_slug',
            'status',
            'difficulty',
            'current_stage',
            'overall_score',
            'started_at',
            'completed_at',
            'created_at',
        ]

    def get_overall_score(self, obj):
        if hasattr(obj, 'evaluation'):
            return obj.evaluation.overall_score
        return None

class InterviewSessionDetailSerializer(serializers.ModelSerializer):
    problem = ProblemDetailSerializer(read_only=True)
    messages = InterviewMessageSerializer(many=True, read_only=True)
    evaluation = InterviewEvaluationSerializer(read_only=True)
    submission = SubmissionSerializer(read_only=True)

    class Meta:
        model = InterviewSession
        fields = [
            'id',
            'problem',
            'status',
            'difficulty',
            'current_stage',
            'final_feedback',
            'submission',
            'messages',
            'evaluation',
            'started_at',
            'completed_at',
            'created_at',
        ]
