"""
URL configuration for expense project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from expense_app import views as expense_views
from django.contrib.auth import views as auth_views
from expense_app.views import CustomLogoutView 

urlpatterns = [
    path('admin/', admin.site.urls),
    path('signup/', expense_views.signup_view, name='signup'),
    path('login/', expense_views.login_view, name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('password_reset/', expense_views.password_reset_view, name='password_reset'),
    path('', expense_views.home_view, name='home'),
    path('add_expense/', expense_views.add_expense_view, name='add_expense'),
    path('delete_expense/<int:id>/', expense_views.delete_expense_view, name='delete_expense'),
    path('update_expense/<int:id>/', expense_views.update_expense_view, name='update_expense'),
    path('weekly_expense/', expense_views.weekly_expenses, name='weekly_expense'),
    path('monthly_expense/', expense_views.monthly_expenses, name='monthly_expense'),
    path('expense_graph/', expense_views.expense_graph_view, name='expense_graph'),
]
