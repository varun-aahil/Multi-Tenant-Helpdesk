from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .models import KnowledgeBase
from .serializers import KnowledgeBaseSerializer, KnowledgeBaseListSerializer
from tickets.permissions import IsTenantMember


class KnowledgeBaseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Knowledge Base articles
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsTenantMember]
    serializer_class = KnowledgeBaseSerializer
    
    def get_queryset(self):
        """Filter by published status and search"""
        queryset = KnowledgeBase.objects.all()
        
        # Only show published articles to non-authenticated users
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(is_published=True)
        
        # Filter by category
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category=category)
        
        # Search
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(content__icontains=search) | Q(tags__icontains=search)
            )
        
        return queryset.select_related('created_by')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return KnowledgeBaseListSerializer
        return KnowledgeBaseSerializer
    
    @action(detail=True, methods=['post'])
    def increment_view(self, request, pk=None):
        """Increment view count"""
        article = self.get_object()
        article.view_count += 1
        article.save()
        return Response({'view_count': article.view_count})
