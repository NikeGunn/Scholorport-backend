"""
Admin API Serializers

Serializers for admin authentication and user management.
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from drf_spectacular.utils import extend_schema_field


class AdminLoginSerializer(serializers.Serializer):
    """Serializer for admin login."""
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('Invalid username or password')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled')
            if not user.is_staff:
                raise serializers.ValidationError('User does not have admin privileges')
            data['user'] = user
        else:
            raise serializers.ValidationError('Username and password are required')

        return data


class AdminUserSerializer(serializers.ModelSerializer):
    """Serializer for admin user profile."""
    full_name = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'full_name',
            'role',
            'is_active',
            'is_staff',
            'is_superuser',
            'date_joined',
            'last_login',
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']

    @extend_schema_field(str)
    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username

    @extend_schema_field(str)
    def get_role(self, obj):
        if obj.is_superuser:
            return 'superadmin'
        elif obj.is_staff:
            return 'admin'
        return 'user'


class AdminUserListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing users."""
    full_name = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'full_name',
            'role',
            'is_active',
            'last_login',
        ]

    @extend_schema_field(str)
    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username

    @extend_schema_field(str)
    def get_role(self, obj):
        if obj.is_superuser:
            return 'superadmin'
        elif obj.is_staff:
            return 'admin'
        return 'user'


class AdminUserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating admin users."""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=['admin', 'superadmin'], default='admin')

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'password',
            'password_confirm',
            'first_name',
            'last_name',
            'role',
        ]

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'Passwords do not match'})
        return data

    def create(self, validated_data):
        role = validated_data.pop('role', 'admin')
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')

        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.is_staff = True
        user.is_superuser = (role == 'superadmin')
        user.save()

        return user


class AdminUserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating admin users."""
    role = serializers.ChoiceField(choices=['admin', 'superadmin', 'user'], required=False)

    class Meta:
        model = User
        fields = [
            'email',
            'first_name',
            'last_name',
            'is_active',
            'role',
        ]

    def update(self, instance, validated_data):
        role = validated_data.pop('role', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if role:
            if role == 'superadmin':
                instance.is_staff = True
                instance.is_superuser = True
            elif role == 'admin':
                instance.is_staff = True
                instance.is_superuser = False
            else:
                instance.is_staff = False
                instance.is_superuser = False

        instance.save()
        return instance


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password."""
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError({'new_password_confirm': 'Passwords do not match'})
        return data


class ResetPasswordSerializer(serializers.Serializer):
    """Serializer for resetting user password (admin only)."""
    new_password = serializers.CharField(required=True, write_only=True, min_length=8)
