from rest_framework import serializers
from apps.progress.models import UserProblemProgress
from apps.problems.serializers import ProblemListSerializer

class UserProblemProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProblemProgress
        fields = (
            'id', 'user', 'problem', 'status', 'attempts', 'solved_at',
            'time_spent', 'hints_used', 'hint_level', 'challenge_score',
            'interview_score', 'submission_history'
        )
        read_only_fields = ('id', 'user', 'problem', 'solved_at')

class ProgressAttemptSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=['UNSOLVED', 'ATTEMPTED', 'SOLVED'])
    time_spent = serializers.IntegerField(required=False, default=0)
    code = serializers.CharField(required=False, allow_blank=True, default="")

class TopicProgressSerializer(serializers.Serializer):
    topic = serializers.CharField()
    solved = serializers.IntegerField()
    total = serializers.IntegerField()
    percentage = serializers.FloatField()

class DashboardStatsSerializer(serializers.Serializer):
    total_problems = serializers.IntegerField()
    solved_count = serializers.IntegerField()
    attempted_count = serializers.IntegerField()
    current_streak = serializers.IntegerField()
    topic_progress = TopicProgressSerializer(many=True)
    recent_problems = ProblemListSerializer(many=True)
    recommended_problem = ProblemListSerializer(allow_null=True)
