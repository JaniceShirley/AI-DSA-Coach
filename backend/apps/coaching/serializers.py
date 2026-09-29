from rest_framework import serializers
from .models import CoachingInteraction
from apps.problems.models import Problem

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
