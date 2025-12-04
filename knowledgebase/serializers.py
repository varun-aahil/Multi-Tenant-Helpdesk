from rest_framework import serializers
from .models import KnowledgeBase


class KnowledgeBaseSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = KnowledgeBase
        fields = [
            'id', 'title', 'content', 'category', 'tags',
            'is_published', 'view_count', 'created_by', 'created_by_username',
            'created_at', 'updated_at'
        ]
        read_only_fields = ('view_count', 'created_at', 'updated_at', 'created_by')
    
    def create(self, validated_data):
        """Set created_by to current user"""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class KnowledgeBaseListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views"""
    class Meta:
        model = KnowledgeBase
        fields = ['id', 'title', 'category', 'tags', 'view_count', 'created_at']

