# authentication/serializers.py
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, 
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(  # 改为 password_confirm（与前端一致）
        write_only=True, 
        required=True,
        style={'input_type': 'password'}
    )
    email = serializers.EmailField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password_confirm')  # 更新字段名

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError('两次密码输入不一致')
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')  # 移除确认密码字段
        user = User.objects.create_user(**validated_data)
        return user
