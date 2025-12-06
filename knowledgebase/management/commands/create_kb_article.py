"""
Management command to create a knowledge base article
Usage: python manage.py create_kb_article --title "How to Reset Password" --content "Steps to reset..." --category "General"
"""
from django.core.management.base import BaseCommand
from knowledgebase.models import KnowledgeBase


class Command(BaseCommand):
    help = 'Create a knowledge base article'

    def add_arguments(self, parser):
        parser.add_argument('--title', type=str, required=True, help='Article title')
        parser.add_argument('--content', type=str, required=True, help='Article content')
        parser.add_argument('--category', type=str, default='General', help='Article category')
        parser.add_argument('--tags', type=str, default='', help='Comma-separated tags')
        parser.add_argument('--is_published', action='store_true', default=True,
                          help='Set article as published')

    def handle(self, *args, **options):
        """Create the knowledge base article"""
        tags_list = [tag.strip() for tag in options['tags'].split(',') if tag.strip()] if options['tags'] else []
        
        article = KnowledgeBase.objects.create(
            title=options['title'],
            content=options['content'],
            category=options['category'],
            tags=tags_list,
            is_published=options['is_published']
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Created knowledge base article: {article.title} (ID: {article.id})'
            )
        )

