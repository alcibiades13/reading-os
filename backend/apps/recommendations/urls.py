from django.urls import path
from .views import (
    RecommendationsView,
    ContextualRecommendationsView,
    SimilarBooksView,
    BookDNASurveyView,
    CheckSurveyView,
    SurveyConfigView,
    TasteProfileView,
    BookDNAView,
)

app_name = 'recommendations'

urlpatterns = [
    # Main recommendations
    path('', RecommendationsView.as_view(), name='list'),
    path('contextual/', ContextualRecommendationsView.as_view(), name='contextual'),
    path('similar/<int:book_id>/', SimilarBooksView.as_view(), name='similar'),

    # Survey
    path('survey/', BookDNASurveyView.as_view(), name='survey'),
    path('survey/check/<int:book_id>/', CheckSurveyView.as_view(), name='check-survey'),
    path('survey/config/', SurveyConfigView.as_view(), name='survey-config'),

    # User profile
    path('taste-profile/', TasteProfileView.as_view(), name='taste-profile'),

    # Book DNA
    path('book-dna/<int:book_id>/', BookDNAView.as_view(), name='book-dna'),
]
