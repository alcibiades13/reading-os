from rest_framework import serializers
from apps.users.models import User, UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile model"""
    
    class Meta:
        model = UserProfile
        fields = [
            'is_public',
            'show_reading_stats',
            'show_quotes',
            'reading_goal_year',
            'favorite_genres',
            'reading_preferences',
            'email_on_friend_request',
            'email_on_circle_invite',
            'email_on_quote_comment',
        ]


class UserSerializer(serializers.ModelSerializer):
    """Basic User serializer"""
    profile = UserProfileSerializer(read_only=True)
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'full_name',
            'bio',
            'avatar',
            'location',
            'website',
            'birth_date',
            'reading_dna',
            'profile',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'reading_dna', 'username']


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = User
        fields = [
            'email',
            'first_name',
            'last_name',
            'password',
            'password_confirm',
        ]
    
    def validate(self, data):
        """Validate that passwords match"""
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return data
    
    def create(self, validated_data):
        """Create user with hashed password"""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        return user


class UserDetailSerializer(serializers.ModelSerializer):
    """Detailed User serializer with stats"""
    profile = UserProfileSerializer(read_only=True)
    full_name = serializers.CharField(read_only=True)
    
    # Stats (calculated)
    books_count = serializers.SerializerMethodField()
    quotes_count = serializers.SerializerMethodField()
    reading_lists_count = serializers.SerializerMethodField()
    friends_count = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'full_name',
            'bio',
            'avatar',
            'location',
            'website',
            'birth_date',
            'reading_dna',
            'profile',
            'created_at',
            # Stats
            'books_count',
            'quotes_count',
            'reading_lists_count',
            'friends_count',
        ]
        read_only_fields = ['id', 'created_at', 'reading_dna']
    
    def get_books_count(self, obj):
        """Count user's books"""
        return obj.user_books.count()
    
    def get_quotes_count(self, obj):
        """Count user's quotes"""
        return obj.quotes.count()
    
    def get_reading_lists_count(self, obj):
        """Count user's reading lists"""
        return obj.reading_lists.count()
    
    def get_friends_count(self, obj):
        """Count user's friends"""
        from apps.social.models import Friendship
        return Friendship.objects.filter(
            from_user=obj,
            status='accepted'
        ).count()


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile"""
    profile = UserProfileSerializer(required=False)
    
    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'bio',
            'avatar',
            'location',
            'website',
            'birth_date',
            'profile',
        ]
    
    def update(self, instance, validated_data):
        """Update user and profile"""
        profile_data = validated_data.pop('profile', None)
        
        # Update user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update profile if provided
        if profile_data and hasattr(instance, 'profile'):
            profile = instance.profile
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()
        
        return instance


