from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserManager(BaseUserManager):
    """Custom user manager where email is the unique identifier"""
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Extended User model.
    Username is not used - we use email for authentication.
    """
    username = None  # Remove username field
    email = models.EmailField(unique=True)
    bio = models.TextField(blank=True, help_text="User's biography")
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True,
        help_text="Profile picture"
    )
    
    # Reading DNA - tematski profil korisnika (populated by AI later)
    reading_dna = models.JSONField(
        default=dict,
        blank=True,
        help_text="User's thematic reading profile"
    )
    
    # Social
    location = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    birth_date = models.DateField(null=True, blank=True, help_text="Date of birth")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Use custom manager
    objects = UserManager()
    
    # Override username requirement
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return self.email
    
    @property
    def full_name(self):
        """Returns user's full name"""
        return f"{self.first_name} {self.last_name}".strip() or self.email


class UserProfile(models.Model):
    """
    User profile settings and preferences.
    Automatically created when User is created (via signal).
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    
    # Privacy settings
    is_public = models.BooleanField(
        default=False,
        help_text="Make profile visible to everyone"
    )
    show_reading_stats = models.BooleanField(default=True)
    show_quotes = models.BooleanField(default=True)
    
    # Reading preferences
    reading_goal_year = models.IntegerField(
        null=True,
        blank=True,
        help_text="Annual reading goal (number of books)"
    )
    favorite_genres = models.JSONField(
        default=list,
        blank=True,
        help_text="List of favorite genre IDs"
    )
    reading_preferences = models.JSONField(
        default=dict,
        blank=True,
        help_text="Preferences: tone, depth, style, etc."
    )
    
    # Onboarding
    onboarding_completed = models.BooleanField(default=False)

    # Notification settings
    email_on_friend_request = models.BooleanField(default=True)
    email_on_circle_invite = models.BooleanField(default=True)
    email_on_quote_comment = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
    
    def __str__(self):
        return f"{self.user.email}'s profile"


# Signal to auto-create profile when user is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create UserProfile when User is created"""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save UserProfile when User is saved"""
    if hasattr(instance, 'profile'):
        instance.profile.save()


