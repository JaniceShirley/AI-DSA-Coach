from rest_framework import serializers
from apps.submissions.models import Submission
from apps.problems.models import TestCase, Problem
from apps.problems.serializers import ProblemListSerializer

class TestCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestCase
        fields = ('id', 'input_data', 'expected_output', 'is_public')

class SubmissionSerializer(serializers.ModelSerializer):
    problem = ProblemListSerializer(read_only=True)

    class Meta:
        model = Submission
        fields = (
            'id', 'user', 'problem', 'code', 'language', 'status',
            'runtime', 'memory', 'error_message', 'test_cases_passed',
            'total_test_cases', 'created_at'
        )
        read_only_fields = ('id', 'user', 'problem', 'created_at')

class RunCodeRequestSerializer(serializers.Serializer):
    problem_id = serializers.IntegerField()
    code = serializers.CharField()
    language = serializers.CharField(required=False, default='python')

class SubmitCodeRequestSerializer(serializers.Serializer):
    problem_id = serializers.IntegerField()
    code = serializers.CharField()
    language = serializers.CharField(required=False, default='python')

class TestCaseResultSerializer(serializers.Serializer):
    test_case_id = serializers.IntegerField()
    input = serializers.CharField()
    expected_output = serializers.CharField()
    actual_output = serializers.CharField()
    passed = serializers.BooleanField()
    error = serializers.CharField(allow_null=True)
    is_public = serializers.BooleanField()

class RunCodeResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    test_cases_passed = serializers.IntegerField()
    total_test_cases = serializers.IntegerField()
    runtime = serializers.FloatField()
    memory = serializers.FloatField()
    error_message = serializers.CharField(allow_null=True)
    results = TestCaseResultSerializer(many=True)
