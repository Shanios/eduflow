from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import TeacherProfile, StudentProfile

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'role', 'phone', 'bio')

    def validate_role(self, value):
        if value == User.Role.ADMIN:
            raise serializers.ValidationError("Cannot self-register as admin.")
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        if user.role == User.Role.TEACHER:
            TeacherProfile.objects.create(user=user)
        elif user.role == User.Role.STUDENT:
            StudentProfile.objects.create(user=user)
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'role', 'phone', 'bio', 'profile_picture', 'date_joined')
        read_only_fields = ('role', 'date_joined')
