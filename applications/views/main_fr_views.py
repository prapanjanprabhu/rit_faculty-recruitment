from django.shortcuts import render,redirect
from django.http import JsonResponse
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

def index(request):
    return render(request, "faculty_requirement/index.html")


def admin_home(request):
    return render(request, "faculty_requirement/admin/admin_home.html")
