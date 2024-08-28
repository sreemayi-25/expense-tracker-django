from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.template import loader
from .forms import SignUpForm, ExpenseForm, CustomPasswordResetForm
from .models import Expense
import matplotlib.pyplot as plt
from django.db import models
from django.contrib.auth import logout
from django.views import View
import io
from io import BytesIO
import urllib, base64
import matplotlib
matplotlib.use('Agg')
from django.contrib import messages
from django.db.models import Sum
from django.db.models.functions import TruncMonth, TruncWeek
from django.utils.timezone import now, timedelta,localdate
from django.db.models.functions import ExtractWeek, ExtractMonth
import calendar
import datetime

def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')  # Redirect to a success page or home
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')  # Redirect to a success page
            else:
                form.add_error(None, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})


@login_required
def home_view(request):
    # Retrieve the latest 5 expenses for the logged-in user
    expenses = Expense.objects.filter(user=request.user).order_by('-date')[:5]
    
    # Aggregate expenses by month
    monthly_expenses = (
        Expense.objects.filter(user=request.user)
        .annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('-month')
    )
    
    # Aggregate expenses by week
    weekly_expenses = (
        Expense.objects.filter(user=request.user)
        .annotate(week=TruncWeek('date'))
        .values('week')
        .annotate(total=Sum('amount'))
        .order_by('-week')
    )
    
    return render(request, 'home.html', {
        'expenses': expenses,
        'monthly_expenses': monthly_expenses,
        'weekly_expenses': weekly_expenses,
    })


@login_required
def add_expense_view(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user
            expense.save()
            return redirect('home')
    else:
        form = ExpenseForm()
    return render(request, 'add_expense.html', {'form': form})


@login_required
def delete_expense_view(request, id):
    expense = Expense.objects.filter(id=id, user=request.user).first()
    if expense:
        expense.delete()
    return redirect('home')


@login_required
def expense_graph_view(request):
    # Filter expenses for the logged-in user
    expenses = Expense.objects.filter(user=request.user)
    
    # Get unique categories
    categories = expenses.values_list('category', flat=True).distinct()
    
    # Aggregate the total amount spent in each category
    data = {category: expenses.filter(category=category).aggregate(models.Sum('amount'))['amount__sum'] for category in categories}
    
    # Generate a bar graph of the expenses by category
    plt.figure(figsize=(10, 5))
    plt.bar(data.keys(), data.values(), color='green')
    plt.xlabel('Category')
    plt.ylabel('Amount Spent')
    plt.title('Expenses by Category')
    
    # Save the bar graph to a string buffer and encode it in base64
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    bar_graph_png = buffer.getvalue()
    bar_graph = base64.b64encode(bar_graph_png).decode('utf-8')
    buffer.close()
    
    # Generate a pie chart of the expenses by category
    plt.figure(figsize=(8, 8))
    plt.pie(data.values(), labels=data.keys(), autopct='%1.1f%%', startangle=140)
    plt.title('Expenses by Category (Pie Chart)')
    
    # Save the pie chart to a string buffer and encode it in base64
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    pie_chart_png = buffer.getvalue()
    pie_chart = base64.b64encode(pie_chart_png).decode('utf-8')
    buffer.close()
    
    # Render the graphs in the template
    return render(request, 'expense_graph.html', {
        'bar_graph': bar_graph,
        'pie_chart': pie_chart,
        'data': data
    })

def password_reset_view(request):
    if request.method == 'POST':
        form = CustomPasswordResetForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login') 
    else:
        form = CustomPasswordResetForm()
    return render(request, 'password_reset.html', {'form': form})

class CustomLogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('login')  # Redirect to login page after logout

    def post(self, request):
        logout(request)
        return redirect('login')

@login_required
def update_expense_view(request, id):
    expense = get_object_or_404(Expense, id=id, user=request.user)
    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = ExpenseForm(instance=expense)
    return render(request, 'update_expense.html', {'form': form})

@login_required
def weekly_expenses(request):
    # Aggregate expenses by week
    weekly_expenses = (
        Expense.objects.filter(user=request.user)
        .annotate(week=TruncWeek('date'))
        .values('week')
        .annotate(total_amount=Sum('amount'))
        .order_by('-week')
    )
    
    return render(request, 'weekly_expense.html', {'weekly_data': weekly_expenses})

@login_required
def monthly_expenses(request):
    selected_month_str = request.GET.get('month', None)
    selected_month = None
    
    if selected_month_str:
        selected_month = datetime.datetime.strptime(selected_month_str, "%Y-%m")
    
    monthly_data = Expense.objects.filter(user=request.user)\
                                  .annotate(month=TruncMonth('date'))\
                                  .values('month')\
                                  .annotate(total_amount=Sum('amount'))\
                                  .order_by('-month')
    
    pie_chart = None
    
    if selected_month:
        # Fetch data for the selected month
        monthly_expenses = Expense.objects.filter(
            user=request.user, 
            date__month=selected_month.month, 
            date__year=selected_month.year
        )
        
        # Generate pie chart for the selected month
        pie_chart = generate_pie_chart(monthly_expenses)
    
    return render(request, 'monthly_expense.html', {
        'monthly_data': monthly_data,
        'selected_month': selected_month,
        'pie_chart': pie_chart
    })
def generate_pie_chart(expenses):
    # Group expenses by category and sum the amounts
    category_data = expenses.values('category').annotate(total_amount=Sum('amount'))
    
    if not category_data.exists():
        return None
    
    categories = [item['category'] for item in category_data]
    amounts = [item['total_amount'] for item in category_data]
    labels = [f"{category}: Rs.{amount}" for category, amount in zip(categories, amounts)]

    # Create a pie chart
    fig, ax = plt.subplots()
    ax.pie(amounts, labels=labels, autopct='%1.1f%%', startangle=90)
    ax.axis('equal')  # Equal aspect ratio ensures the pie chart is circular.

    # Save the plot to a bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)

    # Encode the image to base64
    image_base64 = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()

    return image_base64


