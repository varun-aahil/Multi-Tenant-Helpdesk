"""
Frontend views for admin and customer panels using Django templates with token authentication
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import authenticate
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from tickets.models import Ticket, SLAPolicy
from customers.models import Customer
from knowledgebase.models import KnowledgeBase
from tickets.services import TicketService

User = get_user_model()


def get_user_from_token(request):
    """Get user from JWT token in request (set by middleware)"""
    # Middleware already sets request.user if token is valid
    if hasattr(request, '_token') and request.user.is_authenticated:
        return request.user
    return None


def is_staff_user(user):
    """Check if user is staff"""
    return user and user.is_authenticated and user.is_staff


# ==================== Customer Panel Views ====================

def root_view(request):
    """Root view - redirects to customer login"""
    # Use direct path redirect instead of named URL to avoid potential issues
    return redirect('/login/')

def customer_register(request):
    """Customer registration page"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        name = request.POST.get('name', username)
        
        if password != password_confirm:
            messages.error(request, 'Passwords do not match')
            return render(request, 'frontend/customer/register.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return render(request, 'frontend/customer/register.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists')
            return render(request, 'frontend/customer/register.html')
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=name.split()[0] if name else '',
            last_name=' '.join(name.split()[1:]) if name and len(name.split()) > 1 else ''
        )
        
        # Create customer record
        Customer.objects.create(
            email=email,
            name=name,
        )
        
        messages.success(request, 'Account created successfully! Please login.')
        return redirect('customer_login')
    
    return render(request, 'frontend/customer/register.html')


def customer_login(request):
    """Customer login page - returns token"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user:
            if user.is_staff:
                messages.error(request, 'Admins must use the admin login portal.')
                return render(request, 'frontend/customer/login.html')
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)
            
            # Store tokens in response (will be handled by JavaScript)
            response = render(request, 'frontend/customer/login_success.html', {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user': user,
            })
            return response
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'frontend/customer/login.html')


def customer_logout(request):
    """Logout page"""
    return render(request, 'frontend/customer/logout.html')


def customer_dashboard(request):
    """Customer dashboard with quick stats and recent tickets"""
    user = get_user_from_token(request)
    if not user:
        messages.error(request, 'Please login to continue')
        return redirect('customer_login')
    if user.is_staff:
        messages.error(request, 'Admins must use the admin portal.')
        return redirect('admin_dashboard')
    
    tickets_qs = Ticket.objects.filter(
        customer__email=user.email
    ).select_related('customer', 'assignee', 'sla_policy').order_by('-created_at')
    
    tickets = list(tickets_qs[:20])  # limit for calculations
    total_tickets = tickets_qs.count()
    open_statuses = ['New', 'Open', 'In Progress']
    open_tickets = tickets_qs.filter(status__in=open_statuses).count()
    resolved_tickets = tickets_qs.filter(status__in=['Resolved', 'Closed']).count()
    overdue_count = sum(1 for ticket in tickets if TicketService.check_sla_breach(ticket))
    recent_tickets = tickets[:5]
    recent_ticket_cards = []
    for ticket in recent_tickets:
        recent_ticket_cards.append({
            'ticket': ticket,
            'is_overdue': TicketService.check_sla_breach(ticket),
            'sla_timer': TicketService.format_time_to_escalation(ticket),
        })
    
    context = {
        'user': user,
        'total_tickets': total_tickets,
        'open_tickets': open_tickets,
        'resolved_tickets': resolved_tickets,
        'overdue_count': overdue_count,
        'recent_tickets': recent_ticket_cards,
    }
    return render(request, 'frontend/customer/dashboard.html', context)


def customer_tickets(request):
    """Customer tickets list with filters"""
    user = get_user_from_token(request)
    if not user:
        messages.error(request, 'Please login to continue')
        return redirect('customer_login')
    if user.is_staff:
        messages.error(request, 'Admins must use the admin portal.')
        return redirect('admin_dashboard')
    
    # Get tickets for this customer (by email match)
    tickets = Ticket.objects.filter(
        customer__email=user.email
    ).select_related('customer', 'assignee', 'sla_policy').order_by('-created_at')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        tickets = tickets.filter(status=status_filter)
    
    # Filter by priority if provided
    priority_filter = request.GET.get('priority')
    if priority_filter:
        tickets = tickets.filter(priority=priority_filter)
    
    # Search
    search = request.GET.get('search')
    if search:
        tickets = tickets.filter(
            Q(title__icontains=search) | Q(description__icontains=search)
        )
    
    # Calculate overdue status
    ticket_list = []
    for ticket in tickets:
        is_overdue = TicketService.check_sla_breach(ticket)
        ticket_list.append({
            'ticket': ticket,
            'is_overdue': is_overdue,
            'sla_timer': TicketService.format_time_to_escalation(ticket),
        })
    
    context = {
        'tickets': ticket_list,
        'status_filter': status_filter or '',
        'priority_filter': priority_filter or '',
        'search': search or '',
        'status_choices': Ticket.STATUS_CHOICES,
        'priority_choices': Ticket.PRIORITY_CHOICES,
        'user': user,
    }
    return render(request, 'frontend/customer/tickets.html', context)


def customer_create_ticket(request):
    """Customer create ticket page"""
    user = get_user_from_token(request)
    if not user:
        messages.error(request, 'Please login to continue')
        return redirect('customer_login')
    if user.is_staff:
        messages.error(request, 'Admins must use the admin portal.')
        return redirect('admin_dashboard')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        priority = request.POST.get('priority', 'Medium')
        
        # Get or create customer
        customer, _ = Customer.objects.get_or_create(
            email=user.email,
            defaults={'name': user.get_full_name() or user.username}
        )
        
        # Create ticket
        ticket = Ticket.objects.create(
            title=title,
            description=description,
            priority=priority,
            customer=customer,
            status='New'
        )
        
        # Calculate due_at
        ticket.due_at = TicketService.calculate_due_at(ticket)
        ticket.save()
        
        messages.success(request, f'Ticket #{ticket.id} created successfully!')
        return redirect('customer_ticket_detail', ticket_id=ticket.id)
    
    # Get SLA policies for priority selection
    sla_policies = SLAPolicy.objects.filter(is_active=True)
    context = {
        'sla_policies': sla_policies,
        'priorities': Ticket.PRIORITY_CHOICES,
        'user': user,
    }
    return render(request, 'frontend/customer/create_ticket.html', context)


def customer_ticket_detail(request, ticket_id):
    """Customer view ticket detail"""
    user = get_user_from_token(request)
    if not user:
        messages.error(request, 'Please login to continue')
        return redirect('customer_login')
    if user.is_staff:
        messages.error(request, 'Admins must use the admin portal.')
        return redirect('admin_dashboard')
    
    ticket = get_object_or_404(
        Ticket.objects.select_related('customer', 'assignee', 'sla_policy'),
        pk=ticket_id
    )
    
    # Check if user has access
    if ticket.customer.email != user.email:
        messages.error(request, 'You do not have permission to view this ticket')
        return redirect('customer_dashboard')
    
    is_overdue = TicketService.check_sla_breach(ticket)
    
    context = {
        'ticket': ticket,
        'is_overdue': is_overdue,
        'sla_timer': TicketService.format_time_to_escalation(ticket),
        'user': user,
    }
    return render(request, 'frontend/customer/ticket_detail.html', context)


def customer_knowledge_base(request):
    """Customer knowledge base"""
    articles = KnowledgeBase.objects.filter(is_published=True).select_related('created_by')
    
    # Filter by category
    category = request.GET.get('category')
    if category:
        articles = articles.filter(category=category)
    
    # Search
    search = request.GET.get('search')
    if search:
        articles = articles.filter(
            Q(title__icontains=search) | Q(content__icontains=search) | Q(tags__icontains=search)
        )
    
    # Get unique categories
    categories = KnowledgeBase.objects.filter(is_published=True).values_list('category', flat=True).distinct()
    categories = [c for c in categories if c]  # Remove empty
    
    context = {
        'articles': articles,
        'categories': categories,
        'selected_category': category or '',
        'search': search or '',
    }
    return render(request, 'frontend/customer/knowledge_base.html', context)


def customer_kb_article(request, article_id):
    """Customer view knowledge base article"""
    article = get_object_or_404(KnowledgeBase, pk=article_id, is_published=True)
    
    # Increment view count
    article.view_count += 1
    article.save()
    
    context = {
        'article': article,
    }
    return render(request, 'frontend/customer/kb_article.html', context)


# ==================== Admin Panel Views ====================

def admin_login(request):
    """Admin login page - returns token"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Debug logging
        import logging
        logger = logging.getLogger(__name__)
        
        # Get tenant - TenantMainMiddleware should have already set the schema
        from django_tenants.utils import get_tenant, tenant_context
        from django.db import connection
        tenant = get_tenant(request)
        
        user = None
        
        if tenant:
            logger.warning(f'[admin_login] Authenticating in tenant context: {tenant.schema_name}')
            
            # Explicitly use tenant_context to ensure we're in the right schema
            with tenant_context(tenant):
                # Try to get user directly
                try:
                    user = User.objects.get(username=username)
                    logger.warning(f'[admin_login] User found: {username}, is_staff={user.is_staff}, is_active={user.is_active}')
                    
                    # Check password manually
                    if user.check_password(password):
                        logger.warning(f'[admin_login] Password check PASSED for: {username}')
                    else:
                        logger.warning(f'[admin_login] Password check FAILED for: {username}')
                        user = None
                except User.DoesNotExist:
                    logger.warning(f'[admin_login] User does not exist in tenant schema: {username}')
                    # SECURE WORKAROUND: Only create user if ENABLE_LAZY_ADMIN_CREATION env var is set
                    # This prevents unauthorized admin creation
                    import os
                    enable_lazy = os.environ.get('ENABLE_LAZY_ADMIN_CREATION', 'false').lower() == 'true'
                    if enable_lazy and username == 'root' and password == 'varun16728...':
                        logger.warning(f'[admin_login] Creating admin user lazily (ENABLE_LAZY_ADMIN_CREATION=true): {username}')
                        try:
                            user = User.objects.create_user(
                                username=username,
                                password=password,
                                email='admin@example.com',
                                is_staff=True,
                                is_superuser=True,
                                is_active=True
                            )
                            logger.warning(f'[admin_login] ✅ Successfully created admin user: {username}')
                        except Exception as e:
                            logger.warning(f'[admin_login] ❌ Failed to create user: {e}')
                            user = None
                    else:
                        # List all users in this schema for debugging
                        all_users = User.objects.all()
                        logger.warning(f'[admin_login] All users in tenant schema: {[u.username for u in all_users]}')
                        # Fallback to authenticate() as backup
                        user = authenticate(request, username=username, password=password)
        else:
            logger.warning(f'[admin_login] No tenant found, using authenticate()')
            user = authenticate(request, username=username, password=password)
        
        if user and user.is_staff and user.is_active:
            logger.warning(f'[admin_login] ✅ Login successful for: {username}')
            
            # Check if there's a 'next' parameter (from Django admin redirect)
            next_url = request.GET.get('next') or request.POST.get('next')
            if next_url and next_url.startswith('/admin/'):
                # Redirect to Django admin - use Django's session auth
                from django.contrib.auth import login
                login(request, user)  # This sets up Django session for admin
                return redirect(next_url)
            
            # Generate JWT tokens for frontend admin panel
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)
            
            response = render(request, 'frontend/admin/login_success.html', {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user': user,
            })
            return response
        else:
            if user and not user.is_staff:
                messages.error(request, 'User exists but is not a staff user. Please contact administrator.')
            elif user and not user.is_active:
                messages.error(request, 'User account is inactive. Please contact administrator.')
            else:
                messages.error(request, 'Invalid credentials or not a staff user')
    
    return render(request, 'frontend/admin/login.html')


def admin_logout(request):
    """Admin logout page"""
    return render(request, 'frontend/admin/logout.html')


def admin_dashboard(request):
    """Admin dashboard"""
    user = get_user_from_token(request)
    if not user or not user.is_staff:
        messages.error(request, 'Please login as admin')
        return redirect('admin_login')
    
    # Get statistics
    total_tickets = Ticket.objects.count()
    open_tickets = Ticket.objects.filter(status__in=['New', 'Open', 'In Progress']).count()
    resolved_today = Ticket.objects.filter(
        status='Resolved',
        resolved_at__date=timezone.now().date()
    ).count()
    
    # Get overdue tickets
    all_tickets = Ticket.objects.select_related('customer', 'assignee', 'sla_policy')
    overdue_count = sum(1 for t in all_tickets if TicketService.check_sla_breach(t))
    
    # Recent tickets
    recent_tickets_qs = Ticket.objects.select_related('customer', 'assignee').order_by('-created_at')[:10]
    recent_tickets = [
        {
            'ticket': ticket,
            'sla_timer': TicketService.format_time_to_escalation(ticket),
            'is_overdue': TicketService.check_sla_breach(ticket),
        }
        for ticket in recent_tickets_qs
    ]
    
    # Tickets by status
    tickets_by_status = Ticket.objects.values('status').annotate(count=Count('id'))
    
    # Tickets by priority
    tickets_by_priority = Ticket.objects.values('priority').annotate(count=Count('id'))
    
    context = {
        'total_tickets': total_tickets,
        'open_tickets': open_tickets,
        'resolved_today': resolved_today,
        'overdue_count': overdue_count,
        'recent_tickets': recent_tickets,
        'tickets_by_status': tickets_by_status,
        'tickets_by_priority': tickets_by_priority,
        'user': user,
    }
    return render(request, 'frontend/admin/dashboard.html', context)


def admin_tickets(request):
    """Admin tickets list"""
    user = get_user_from_token(request)
    if not user or not user.is_staff:
        messages.error(request, 'Please login as admin')
        return redirect('admin_login')
    
    tickets = Ticket.objects.select_related('customer', 'assignee', 'sla_policy').order_by('-created_at')
    
    # Filters
    status_filter = request.GET.get('status')
    if status_filter:
        tickets = tickets.filter(status=status_filter)
    
    priority_filter = request.GET.get('priority')
    if priority_filter:
        tickets = tickets.filter(priority=priority_filter)
    
    assignee_filter = request.GET.get('assignee')
    if assignee_filter:
        tickets = tickets.filter(assignee_id=assignee_filter)
    
    search = request.GET.get('search')
    if search:
        tickets = tickets.filter(
            Q(title__icontains=search) | Q(description__icontains=search) | Q(customer__name__icontains=search)
        )
    
    # Calculate overdue status
    ticket_list = []
    for ticket in tickets:
        is_overdue = TicketService.check_sla_breach(ticket)
        ticket_list.append({
            'ticket': ticket,
            'is_overdue': is_overdue,
            'sla_timer': TicketService.format_time_to_escalation(ticket),
        })
    
    # Get all users for assignee filter
    users = User.objects.filter(is_staff=True)
    
    context = {
        'tickets': ticket_list,
        'status_filter': status_filter or '',
        'priority_filter': priority_filter or '',
        'assignee_filter': assignee_filter or '',
        'search': search or '',
        'status_choices': Ticket.STATUS_CHOICES,
        'priority_choices': Ticket.PRIORITY_CHOICES,
        'users': users,
        'user': user,
    }
    return render(request, 'frontend/admin/tickets.html', context)


def admin_ticket_detail(request, ticket_id):
    """Admin ticket detail and management"""
    user = get_user_from_token(request)
    if not user or not user.is_staff:
        messages.error(request, 'Please login as admin')
        return redirect('admin_login')
    
    ticket = get_object_or_404(
        Ticket.objects.select_related('customer', 'assignee', 'sla_policy'),
        pk=ticket_id
    )
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'change_status':
            new_status = request.POST.get('status')
            if new_status and new_status in dict(Ticket.STATUS_CHOICES):
                TicketService.update_ticket_status(ticket, new_status, user)
                messages.success(request, f'Ticket status changed to {new_status}')
            else:
                messages.error(request, 'Invalid status selected')
        
        elif action == 'change_priority':
            new_priority = request.POST.get('priority')
            if new_priority and new_priority in dict(Ticket.PRIORITY_CHOICES):
                ticket.priority = new_priority
                ticket.save()
                messages.success(request, f'Ticket priority changed to {new_priority}')
            else:
                messages.error(request, 'Invalid priority selected')
        
        elif action == 'assign':
            assignee_id = request.POST.get('assignee_id')
            if assignee_id:
                try:
                    assignee = User.objects.get(pk=assignee_id)
                    TicketService.assign_ticket(ticket, assignee)
                    messages.success(request, f'Ticket assigned to {assignee.username}')
                except User.DoesNotExist:
                    messages.error(request, 'Assignee not found')
            else:
                # Unassign ticket
                ticket.assignee = None
                ticket.save()
                messages.success(request, 'Ticket unassigned')
        
        return redirect('admin_ticket_detail', ticket_id=ticket.id)
    
    is_overdue = TicketService.check_sla_breach(ticket)
    
    # Get all users for assignment
    users = User.objects.filter(is_staff=True)
    
    context = {
        'ticket': ticket,
        'is_overdue': is_overdue,
        'sla_timer': TicketService.format_time_to_escalation(ticket),
        'users': users,
        'status_choices': Ticket.STATUS_CHOICES,
        'priority_choices': Ticket.PRIORITY_CHOICES,
        'user': user,
    }
    return render(request, 'frontend/admin/ticket_detail.html', context)


def admin_customers(request):
    """Admin customers list"""
    user = get_user_from_token(request)
    if not user or not user.is_staff:
        messages.error(request, 'Please login as admin')
        return redirect('admin_login')
    
    customers = Customer.objects.annotate(ticket_count=Count('tickets')).order_by('-created_at')
    
    search = request.GET.get('search')
    if search:
        customers = customers.filter(
            Q(name__icontains=search) | Q(email__icontains=search) | Q(company__icontains=search)
        )
    
    context = {
        'customers': customers,
        'search': search or '',
        'user': user,
    }
    return render(request, 'frontend/admin/customers.html', context)


def admin_knowledge_base(request):
    """Admin knowledge base management"""
    user = get_user_from_token(request)
    if not user or not user.is_staff:
        messages.error(request, 'Please login as admin')
        return redirect('admin_login')
    
    articles = KnowledgeBase.objects.select_related('created_by').order_by('-created_at')
    
    # Filter by published status
    published_filter = request.GET.get('published')
    if published_filter == 'true':
        articles = articles.filter(is_published=True)
    elif published_filter == 'false':
        articles = articles.filter(is_published=False)
    
    # Filter by category
    category = request.GET.get('category')
    if category:
        articles = articles.filter(category=category)
    
    # Search
    search = request.GET.get('search')
    if search:
        articles = articles.filter(
            Q(title__icontains=search) | Q(content__icontains=search)
        )
    
    # Get unique categories
    categories = KnowledgeBase.objects.values_list('category', flat=True).distinct()
    categories = [c for c in categories if c]  # Remove empty
    
    context = {
        'articles': articles,
        'categories': categories,
        'selected_category': category or '',
        'published_filter': published_filter or '',
        'search': search or '',
        'user': user,
    }
    return render(request, 'frontend/admin/knowledge_base.html', context)


def admin_kb_article_detail(request, article_id):
    """Admin knowledge base article detail/edit"""
    user = get_user_from_token(request)
    if not user or not user.is_staff:
        messages.error(request, 'Please login as admin')
        return redirect('admin_login')
    
    article = get_object_or_404(KnowledgeBase, pk=article_id)
    
    if request.method == 'POST':
        article.title = request.POST.get('title')
        article.content = request.POST.get('content')
        article.category = request.POST.get('category', '')
        article.is_published = request.POST.get('is_published') == 'on'
        article.save()
        messages.success(request, 'Article updated successfully')
        return redirect('admin_kb_article_detail', article_id=article.id)
    
    context = {
        'article': article,
        'user': user,
    }
    return render(request, 'frontend/admin/kb_article_detail.html', context)
