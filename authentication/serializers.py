# authentication/serializers.py
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, 
        required=True,
        # 移除密码验证器，或者自定义验证规则
        # validators=[validate_password],  # 注释掉这行
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True, 
        required=True,
        style={'input_type': 'password'}
    )
    email = serializers.EmailField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password_confirm')

    def validate(self, data):
        # 检查密码是否一致
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError('两次密码输入不一致')
        
        # 检查用户名长度（可选，设置你自己的规则）
        username = data.get('username', '')
        if len(username) < 1:  # 或者设置为你想要的最小长度
            raise serializers.ValidationError('用户名不能为空')
        
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')  # 移除确认密码字段
        
        # 创建用户，不进行额外的验证
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )
        return user
