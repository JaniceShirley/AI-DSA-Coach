from rest_framework import serializers
from apps.problems.models import Problem
from apps.progress.models import UserProblemProgress

class ProblemListSerializer(serializers.ModelSerializer):
    user_status = serializers.SerializerMethodField()

    class Meta:
        model = Problem
        fields = ('id', 'title', 'slug', 'difficulty', 'topics', 'patterns', 'user_status')

    def get_user_status(self, obj):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            progress = UserProblemProgress.objects.filter(user=request.user, problem=obj).first()
            return progress.status if progress else 'UNSOLVED'
        return 'UNSOLVED'

class ProblemDetailSerializer(serializers.ModelSerializer):
    user_status = serializers.SerializerMethodField()

    class Meta:
        model = Problem
        fields = (
            'id', 'title', 'slug', 'difficulty', 'topics', 'patterns',
            'description', 'constraints', 'examples', 'starter_code',
            'created_at', 'user_status'
        )

    def get_user_status(self, obj):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            progress = UserProblemProgress.objects.filter(user=request.user, problem=obj).first()
            return progress.status if progress else 'UNSOLVED'
        return 'UNSOLVED'
