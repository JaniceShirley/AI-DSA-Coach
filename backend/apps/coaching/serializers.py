from rest_framework import serializers
from .models import CoachingInteraction, CoachingSession
from apps.problems.models import Problem

class ChatRequestSerializer(serializers.Serializer):
    problem_id = serializers.IntegerField()
    message = serializers.CharField(allow_blank=False, max_length=5000)
    student_code = serializers.CharField(allow_blank=True, default='')
    run_code = serializers.BooleanField(default=False)

class HintRequestSerializer(serializers.Serializer):
    problem_id = serializers.IntegerField()
    student_code = serializers.CharField(allow_blank=True, default='')
    submission_id = serializers.IntegerField(required=False, allow_null=True)
    requested_level = serializers.IntegerField(required=False, allow_null=True)

class ChallengeRequestSerializer(serializers.Serializer):
    problem_id = serializers.IntegerField()
    student_code = serializers.CharField(allow_blank=True, default='')
    user_answer = serializers.CharField(required=False, allow_blank=True, default='')

class AlternativeRequestSerializer(serializers.Serializer):
    problem_id = serializers.IntegerField()
    student_code = serializers.CharField(allow_blank=True, default='')

class FeedbackRequestSerializer(serializers.Serializer):
    problem_id = serializers.IntegerField()
    student_code = serializers.CharField(allow_blank=True, default='')
    submission_id = serializers.IntegerField(required=False, allow_null=True)

class CoachingSessionSerializer(serializers.ModelSerializer):
    problem_title = serializers.CharField(source='problem.title', read_only=True)

    class Meta:
        model = CoachingSession
        fields = [
            'id',
            'problem',
            'problem_title',
            'stage',
            'current_approach',
            'explored_approaches',
            'solution_status',
            'complexity_state',
            'hints_provided',
            'misconceptions',
            'last_student_code',
            'last_execution_result',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields

class CoachingInteractionSerializer(serializers.ModelSerializer):
    problem_title = serializers.CharField(source='problem.title', read_only=True)
    
    class Meta:
        model = CoachingInteraction
        fields = [
            'id',
            'session_id',
            'problem',
            'problem_title',
            'student_code',
            'hint_level',
            'user_question',
            'ai_response',
            'submission',
            'interaction_type',
            'evaluation_metadata',
            'created_at',
        ]
        read_only_fields = ['id', 'session_id', 'created_at']

